import dash
from dash import Dash, dcc, html
from dash import callback, Input, Output, State, ctx, Patch, set_props, ALL, MATCH
import dash_mantine_components as dmc
from dash_iconify import DashIconify


import utils
import re
import pages

app = Dash(
    __name__,
    suppress_callback_exceptions=True,
    on_error=utils.raise_callback_error,
    title="Libraries Resources",
)

server = app.server

cache = utils.cache

with open("README.md", "r") as f:
    markdown_text = f.read()
    readme = dmc.Container(dcc.Markdown(markdown_text))

app.layout = dmc.MantineProvider(
    dmc.Container(
        [
            # notification container
            dmc.NotificationContainer(
                id="notification-container", position="top-right"
            ),
            # location to add query strings / parameters
            dcc.Location(id="location", refresh="callback-nav"),
            # stores
            # stores for pip_freeze, req and build_logs are generated as part of their text areas
            dcc.Store(id="store_raw", data=""),
            dcc.Store(
                id="store_extra", data={}, storage_type="session"
            ),  # for additional information like extra-index-url
            dcc.Store(
                id="store_stripped_requirements", data=[], storage_type="session"
            ),  # for stripped requirements
            # layout
            dmc.Space(h=15),
            dmc.Accordion(
                multiple=True,
                variant="contained",
                value=[],
                children=[
                    # README
                    dmc.AccordionItem(
                        [
                            dmc.AccordionControl("What is this app?"),
                            dmc.AccordionPanel(readme),
                        ],
                        value="readme",
                    ),
                    # Instructions and resources
                    dmc.AccordionItem(
                        [
                            dmc.AccordionControl("Additional resources"),
                            dmc.AccordionPanel(pages.resources.resources_text),
                        ],
                        value="info",
                    ),
                    # Upload file(s)
                    dmc.AccordionItem(
                        [
                            dmc.AccordionControl("Upload files"),
                            dmc.AccordionPanel(
                                [
                                    dmc.SimpleGrid(
                                        [
                                            utils.text_upload_set("req"),
                                            utils.text_upload_set(
                                                "pip_freeze",
                                                placeholder=' run "pip freeze > pip_freeze.txt" to get this information in a txt file',
                                            ),
                                            # utils.text_upload_set("build_logs"),
                                        ],
                                        cols=2,  # 3
                                        spacing="xs",
                                    )
                                ]
                            ),
                        ],
                        value="files",
                    ),
                ],
            ),
            dmc.Space(h=15),
            # Select a case
            dmc.SegmentedControl(
                id="choose_action",
                orientation="horizontal",
                fullWidth=True,
                data=[
                    {"label": "Packages history", "value": "packages-history"},
                    {"label": "Changelogs", "value": "changelogs"},
                    {"label": "Strip requirements", "value": "strip-req"},
                ],
                value=None,
                size="md",
            ),
            dmc.Space(h=15),
            dcc.Loading(dmc.Container(id="content", fluid=True), delay_show=500),
            dmc.Space(h=100),
        ],
        fluid=True,
    )
)


# manage routing based on url + segmented control
# to set a defaul (packages-history) and avoid infinite loops
@callback(
    Output("choose_action", "value"),
    Output("location", "pathname"),
    Output("location", "search"),
    Input("choose_action", "value"),
    State("location", "pathname"),
    State("location", "search"),
)
def update_location_with_page(choose_action, pathname, search):
    pathname = dash.strip_relative_path(pathname)
    if not choose_action:
        if not pathname:
            return "packages-history", dash.get_relative_path("/packages-history"), ""
        else:
            return pathname.strip("/"), dash.get_relative_path(f"/{pathname}"), search
    else:
        if choose_action != "changelogs":
            search = ""
        return dash.no_update, dash.get_relative_path(f"/{choose_action}"), search


@callback(
    Output("content", "children"),
    Input("location", "pathname"),
    Input({"type": "store", "index": "req"}, "data"),
    Input({"type": "store", "index": "pip_freeze"}, "data"),
    State("store_stripped_requirements", "data"),
    State("store_extra", "data"),
    State("location", "search"),
    # add this to improve performance
    # the update_location_with_page should always run first
    prevent_initial_call=True,
)
def change_content(
    pathname, store_req, store_pip, store_stripped_req, store_extra, search_str
):
    pathname = dash.strip_relative_path(pathname)
    match pathname:
        case "packages-history":
            return pages.packages_history.layout(store_req, store_pip)
        case "changelogs":
            libs = search_str.removeprefix("?libs=").split("&") if search_str else None
            return pages.packages_changelogs.layout(libs, store_req, store_pip)
        case "strip-req":
            return pages.strip_req.layout(store_req, store_stripped_req, store_extra)
        case _:
            return []


if __name__ == "__main__":
    app.run(debug=True)
