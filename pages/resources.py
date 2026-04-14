# https://github.com/MrNaif2018/changelog-checker/tree/master
# _generate_package_report function: 
# https://github.com/MrNaif2018/changelog-checker/blob/master/changelog_checker/core.py#L84C9-L84C33

from dash import dcc, html
import dash_mantine_components as dmc
from dash_iconify import DashIconify

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

def components_from_md(markdown_file):
    with open(markdown_file, 'r') as f:
        markdown_lines = f.readlines()

    # initialize variables for loop
    components = []
    current_block = ""
    current_block_is_code = False

    # loop
    for l in markdown_lines:
        if "```" in l:
            # if current_block_is_code is True, the ``` are CLOSING the codeblock
            if current_block_is_code:
                components.append(codeblock_with_copy(current_block))

                # reset current_block for the next iteration
                current_block = ""
                current_block_is_code = False
            # otherwise the ``` are OPENING the codeblock, 
            # so we need to close+add the previous markdown component
            else :
                components.append(dcc.Markdown(current_block))
                current_block = ""
                current_block_is_code = True
        else :
            current_block += l

    return components

resources_text = dmc.Container(
    components_from_md("pages/resources.md")
)
