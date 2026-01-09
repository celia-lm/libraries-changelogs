import pandas as pd
import re
import requests

# https://stackoverflow.com/a/72188040
from packaging.version import Version, parse

import dash_mantine_components as dmc
from dash import dcc, html, ctx
from dash_iconify import DashIconify
import dash
import datetime
import traceback
import diskcache

cache = diskcache.Cache("./cache")

# file_ids
file_ids = {
    "req": "requirements.txt",
    "pip_freeze": "Pip Freeze",
    "build_logs": "Build logs",
}


def raise_callback_error(err):
    err_traceback = traceback.format_exc()
    print(
        f"""
        Error in callback with outputs: 
        {ctx.outputs_list} 
        and inputs {ctx.inputs_list}:
        {err_traceback}
        """
    )

    dash.set_props(
        "notification-container",
        {
            "sendNotifications": [
                {
                    "action": "show",
                    "message": f"{err} - Check logs for complete traceback",
                    "color": "red",
                    "autoClose": False,
                }
            ]
        },
    )


def text_upload_set(file_type, placeholder=None):

    return html.Div(
        [
            dcc.Store(
                id={"type": "store", "index": file_type}, data=[], storage_type="local"
            ),  # for requirements.txt
            dmc.Textarea(
                id={"type": "textarea", "index": file_type},
                label=dmc.Group(
                    [
                        dmc.Text(file_ids[file_type]),
                        dcc.Upload(
                            dmc.ActionIcon(
                                DashIconify(icon="lucide:upload", width=20),
                                variant="transparent",
                            ),
                            id={"type": "upload", "index": file_type},
                        ),
                        dmc.ActionIcon(
                            DashIconify(icon="lucide:trash-2", width=20),
                            variant="transparent",
                            id={"type": "clear-uploaded", "index": file_type},
                        ),
                    ]
                ),
                autosize=True,
                minRows=5,
                maxRows=10,
                placeholder=placeholder,
                debounce=True,
                persistence=True,
                persistence_type="local",
            ),
        ]
    )


@cache.memoize()
def check_library_valid_format(line: str) -> bool:
    comment_pattern = "^#"
    extra_index_pattern = "^--"
    full_pattern = f"({comment_pattern}|{extra_index_pattern})"

    if re.match(
        full_pattern, line
    ):  # if match, this line doesn't refer to a library that's going to be installed
        return False
    else:
        return True


@cache.memoize()
def extract_extra_index_url(file_source: str) -> str:
    """
    Read a line from a requirements.txt (pre-processed with `read_requirements_file`) and return it if it starts with `--extra-index-url`; otherwise, return an empty string.

    Parameters
    ----------
    file_source :str
        Raw content of requirements.txt file in the form of a string.

    Returns
    -------
    list of str
        --extra-index-url complete line or empty string.
    """
    extra_index_pattern = "^--extra-index-url"
    extra_index_list = [
        line for line in file_source.split("\n") if re.match(extra_index_pattern, line)
    ]

    return extra_index_list


@cache.memoize()
def extract_version_from_string(file_string: str) -> str:

    pattern = "\d+(\.\d+){2,3}"

    # Search for the pattern in the input string
    match = re.search(pattern, file_string)

    # Extract the matched string
    if match:
        extracted_string = match.group()
        return extracted_string
    else:
        return None


# file (requirements, pip freeze) specific
@cache.memoize()
def strip_requirements(line: str) -> str:
    return re.split("==|>=|<=|>|<|~=", line)[0]


def read_requirements_text(req_text: str) -> list[str]:
    """
    Read requirements from textarea and return a list with one item per library.
    All comments and --extra-index-url will be removed.

    Returns
    -------
    list of str
        List of requirements.
    """

    requirements_list = (
        [line for line in req_text.split("\n") if check_library_valid_format(line)]
        if req_text
        else []
    )

    return requirements_list


@cache.memoize()
def extract_name_version(line, file_type="req") -> dict:

    delimiter_pattern = "==|>=|<=|>|<|~="
    string_split = re.split(delimiter_pattern, line)
    source = "external"

    name = string_split[0].strip().lower()

    if len(string_split) > 1:
        version = string_split[1]
    else:
        version = extract_version_from_string(line)
        if version:
            source = "internal"
        else:
            file_pattern = " @ file"
            string_split_file = re.split(file_pattern, line)
            if len(string_split_file) > 1:
                name = string_split_file[0].strip()
                source = "internal"
                version = "unknown"

    if file_type == "req":
        delimiter_match = re.search("==|>=|<=|>|<", line)
        # if there's a match, it means the library is pinned
        if delimiter_match:  # will be retrieved from external repo
            pinned = delimiter_match.group()
        # this means it's installed from a file (e.g. tarball, wheel)
        elif source == "internal":
            pinned = "=="
        # internal or external, the version is not pinned, it's just the name
        else:
            pinned = "Not pinned"

        lib = {
            "raw_line_req": line.strip(),
            "name": name,
            "req_version": version.rstrip(),
            "source": source,
            "req_pinned": pinned,
        }
    elif file_type == "pip_freeze":
        lib = {
            "name": name,
            "installed_version": version.rstrip(),
            "raw_line_installed": line.strip(),
        }
    else:
        lib = {"name": name, "version": version}

    return lib


@cache.memoize()
def is_valid_version(version):
    try:
        parse(version)
        return True
    except:
        return False


@cache.memoize()
def get_library_history(lib: dict | str) -> dict:
    """
    lib: dict

    """
    if isinstance(lib, str):
        lib = {"name": lib}

    # we use .lower to make the grid sorting easier (it treats uppercase differently)
    name = lib["name"].lower()

    # get information from the pypi page in json forman
    releases_json = requests.get(f"https://pypi.org/pypi/{name}/json").json()
    if releases_json and releases_json.get("message") != "Not Found":
        versions_dict = {
            k: v[0]["upload_time"]
            for k, v in releases_json["releases"].items()
            if len(v)
        }
        # only keep valid version keys to make sorting possible
        # even if that means leaving out versions like '0.8.0-final0'
        versions_keys = [v for v in versions_dict.keys() if is_valid_version(v)]
        versions_keys.sort(key=Version)
        versions = {k: versions_dict[k] for k in versions_keys}
        newest = versions_keys[-1]
        newest_date = datetime.datetime.fromisoformat(versions[newest]).strftime(
            "%Y-%m-%d"
        )

        # installed version
        installed_version_info = versions.get(lib.get("installed_version"))

        installed_date = (
            datetime.datetime.fromisoformat(installed_version_info).strftime("%Y-%m-%d")
            if installed_version_info
            else None
        )

        # requirements version
        req_version_info = versions.get(lib.get("req_version"))

        req_date = (
            datetime.datetime.fromisoformat(req_version_info).strftime("%Y-%m-%d")
            if req_version_info
            else None
        )

        project_urls_raw = releases_json["info"]["project_urls"]

        project_urls = (
            ", ".join([f"[{k}]({v})" for k, v in project_urls_raw.items()])
            if project_urls_raw
            else ""
        )

    else:
        newest = None
        newest_date = None
        installed_date = None
        req_date = None
        project_urls = None
        project_urls_raw = {}

    # add to the dict
    lib.update(
        {
            "newest_version": newest,
            "newest_release_date": newest_date,
            "installed_release_date": installed_date,
            "req_release_date": req_date,
            # "all_versions": versions,
            "urls": project_urls,
            "urls_dict": project_urls_raw,
        }
    )

    return lib


@cache.memoize()
def get_repo_url(lib: dict):
    for name, url in lib["urls_dict"].items():
        if (name.lower() in ["source", "github", "changes", "changelog"]) or ("github" in url):
            return {"url": url}

    return {"url": None}

@cache.memoize()
def get_lib_names_list(store_req=[], store_pip=[]):
    return list(set([lib["name"] for lib in store_req + store_pip]))