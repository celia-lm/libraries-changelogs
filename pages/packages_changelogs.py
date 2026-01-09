import dash
from dash import Dash, dcc, html, register_page
from dash import callback, Input, Output, State, ctx, MATCH, ALL, Patch
import dash_ag_grid as dag
import dash_mantine_components as dmc
from dash_iconify import DashIconify
from operator import itemgetter
import utils

cache = utils.cache

@cache.memoize()
def version_markdown_format(all_changelogs, versions_to_add):
    return "\r\n***\r\n".join(
        [
            f"# [{k}]({all_changelogs[k]['release_url']}) ({all_changelogs[k]['release_date']})\r\n{all_changelogs[k]['changelog_text']}"
            for k in versions_to_add
        ]
    )


def version_management_layout_gh(lib_name: str, changelogs_dict: dict):
    versions_reversed = changelogs_dict.get("versions_reversed")
    if len(versions_reversed) < 1:
        versions_reversed = [None]
    last_version = versions_reversed[4] if len(versions_reversed) >= 4 else None
    return dmc.Container(
        [
            # store
            dcc.Store(
                id={"type": "changelog-store", "index": lib_name},
                data=changelogs_dict,
            ),
            dcc.Store(
                id={"type": "changelog-state", "index": lib_name},
                data={"last": last_version},
            ),
            # controls
            dmc.SimpleGrid(
                [
                    dmc.Button(
                        children="Load more versions",
                        justify="center",
                        leftSection=DashIconify(icon="lucide:plus"),
                        variant="outline",
                        id={"type": "changelog-version-load-more", "index": lib_name},
                    ),
                    dmc.Popover(
                        trapFocus=True,
                        position="top",
                        withArrow=True,
                        children=[
                            dmc.PopoverTarget(
                                dmc.Button(
                                    "Or select min and max versions", variant="outline"
                                ),
                            ),
                            dmc.PopoverDropdown(
                                [
                                    dmc.Select(
                                        label="Min version",
                                        clearable=True,
                                        searchable=True,
                                        data=versions_reversed,
                                        placeholder=versions_reversed[-1],
                                        id={
                                            "type": "changelog-version-min",
                                            "index": lib_name,
                                        },
                                    ),
                                    dmc.Select(
                                        label="Max version",
                                        clearable=True,
                                        searchable=True,
                                        data=versions_reversed,
                                        placeholder=versions_reversed[0],
                                        id={
                                            "type": "changelog-version-max",
                                            "index": lib_name,
                                        },
                                    ),
                                    dmc.ActionIcon(
                                        DashIconify(icon="lucide:refresh-cw"),
                                        variant="transparent",
                                        id={
                                            "type": "changelog-version-update",
                                            "index": lib_name,
                                        },
                                    ),
                                ]
                            ),
                        ],
                    ),
                ],
                cols=2,
                spacing="xs",
            ),
        ]
    )


@callback(
    Output({"type": "changelog-container", "index": MATCH}, "children"),
    Input({"type": "changelog-version-update", "index": MATCH}, "n_clicks"),
    Input({"type": "changelog-version-load-more", "index": MATCH}, "n_clicks"),
    State({"type": "changelog-version-min", "index": MATCH}, "value"),
    State({"type": "changelog-version-max", "index": MATCH}, "value"),
    State({"type": "changelog-store", "index": MATCH}, "data"),
    State({"type": "changelog-state", "index": MATCH}, "data"),
)
def update_changelog_versions(
    n_clicks_update,
    n_clicks_load_more,
    min_version,
    max_version,
    versions_store,
    versions_state,
):
    if not ctx.triggered:
        return dash.no_update
    elif ctx.triggered_id["type"] == "changelog-version-load-more":
        versions_reversed = versions_store.get("versions_reversed")
        all_changelogs = versions_store.get("all_changelogs")
        current_last_version = versions_state.get("last")
        current_position = (
            versions_reversed.index(current_last_version) if current_last_version else 4
        )
        # https://stackoverflow.com/a/24204498 itemgetter
        # we need to do +1 to current position to avoid generating a duplicate
        # the first value we want to take is the one that follows the current position
        versions_to_add = versions_reversed[current_position + 1 : current_position + 6]
        current_text = Patch()

        text_to_add = version_markdown_format(all_changelogs, versions_to_add)

        current_text += text_to_add
        # we use a different store to changelog-store so that we can overwrite the value of this one
        # without having to send back the changelog-store as an output too
        dash.set_props(
            {"type": "changelog-state", "index": ctx.triggered_id["index"]},
            {"data": {"last": versions_to_add[-1]}},
        )
        return current_text
    else:
        versions_reversed = versions_store.get("versions_reversed")
        min_version_position = (
            versions_reversed.index(min_version)
            if min_version
            else len(versions_reversed)
        )
        max_version_position = (
            versions_reversed.index(max_version) if max_version else 0
        )
        # since the list is in reverse order (from most recent to oldest) we will select max:min
        versions_to_add = versions_reversed[
            max_version_position : min_version_position + 1
        ]
        new_text = version_markdown_format(all_changelogs, versions_to_add)

        # reset count for the changelog state
        dash.set_props(
            {"type": "changelog-state", "index": ctx.triggered_id["index"]},
            {"data": {"last": None}},
        )
        return new_text


@cache.memoize()
def changelog_accordion(lib_name):
    lib = utils.get_library_history(lib_name)
    repo_url = utils.get_repo_url(lib)

    if repo_url.get("is_github"):
        full_changelog = utils.get_changelogs(repo_url)
        changelogs_dict = full_changelog.get("all_changelogs")
        versions_reversed = full_changelog.get("versions_reversed")
        accordion_content = [
            dcc.Markdown(
                id={"type": "changelog-container", "index": lib_name},
                children=version_markdown_format(
                    changelogs_dict, versions_reversed[:5]
                ),
                style={"height": "50vh", "overflow-y": "scroll"},
            ),
            version_management_layout_gh(lib_name, full_changelog),
        ]
    elif repo_url.get("url"):
        accordion_content = [
            html.Iframe(
                src=repo_url.get("url"),
                style={"width": "-webkit-fill-available", "height": "50vh"},
            )
        ]
    else:
        text = f"The changelog for {lib_name} couldn't be processed. Check the library page: {lib.get('urls')}"
        accordion_content = dcc.Markdown(text)

    return dmc.AccordionItem(
        value=lib_name,
        children=[
            dmc.AccordionControl(lib_name),
            dmc.AccordionPanel(accordion_content),
        ],
        id={"type": "changelog-accordion-item", "index": lib_name},
    )


def layout(libs, store_req={}, store_pip={}):

    # changelogs = [changelog_accordion(l) for l in libs] if libs else []

    return dmc.Container(
        [
            dmc.Container(
                [
                    dmc.TagsInput(
                        id="lib-names",
                        label="Library names",
                        value=libs,
                        data=utils.get_lib_names_list(store_req, store_pip),
                        persistence=True,
                        clearable=True,
                    ),
                ]
            ),
            dmc.Accordion(
                multiple=True,
                id="changelogs-container",
                children=[],
            ),
        ]
    )


@callback(
    Output("changelogs-container", "children"),
    Input("lib-names", "value"),
    State({"type": "changelog-accordion-item", "index": ALL}, "value"),
)
def load_changelogs(lib_names, current_changelogs):
    if lib_names:
        loaded_changelogs = Patch()

        if current_changelogs:
            for lib in current_changelogs:
                if lib not in lib_names:
                    index_to_remove = current_changelogs.index(lib)
                    del loaded_changelogs[index_to_remove]

        loaded_changelogs += [
            changelog_accordion(lib)
            for lib in lib_names
            if lib not in current_changelogs
        ]

        return loaded_changelogs
    else:
        return []
