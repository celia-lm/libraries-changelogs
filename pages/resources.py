# https://github.com/MrNaif2018/changelog-checker/tree/master
# _generate_package_report function:
# https://github.com/MrNaif2018/changelog-checker/blob/master/changelog_checker/core.py#L84C9-L84C33

from dash import dcc, html
import dash_mantine_components as dmc
from dash_iconify import DashIconify

commands = {
    "clear_env":"pip uninstall -y -r <(pip freeze)",
    "clear_pip_cache":"pip cache remove *"
}

def codeblock_with_copy(code):
    return dmc.Group([
        dmc.Code(
            code,
            block=True
            ),
        dmc.CopyButton(
            value="This text is copied",
            children=DashIconify(icon="fa-regular:copy"),
            copiedChildren=DashIconify(icon="fa-regular:check-circle"),
            color="gray",
            copiedColor="dark",
            variant="transparent",
            styles={
                "root":{
                    "--button-padding-x":"0px"
                }
            }
            )
        ],
        gap="sm",
    )

resources_text = dmc.Container([
    dcc.Markdown("""
        **Command to remove all of the installed libraries: **
        """
    ),
    codeblock_with_copy(commands['clear_env']),
    dcc.Markdown("""
        **Command to remove cached dependencies: **
        """
    ),
    codeblock_with_copy(commands['clear_pip_cache']),
    dcc.Markdown("""
        This command is useful when we want to install a library without a pinned version (e.g. `pip install dash`). 
        If we had previously installed a specific version (e.g. `pip install dash==3.0.0`), 
        pip will reuse that one since it has the wheel in its cache directory. 
        Alternatively, we can do:
        """
    ),
    codeblock_with_copy("pip install dash --no-cache-dir")
])
