import dash
from dash import Dash, dcc, html
from dash import callback, Input, Output, State, ctx
import dash_mantine_components as dmc
import utils
from dash_iconify import DashIconify


def load_stripped_req(store_req, store_stripped_req, store_extra):

    textarea_value = None
    placeholder = None

    if not store_req:
        placeholder = "Provide some requirements.txt to remove their version numbers"
    else:
        if store_extra:
            extra_index_string = "\n".join(store_extra.get("extra_index_url", ""))
        else:
            extra_index_string = ""
        if store_stripped_req:
            stripped_req = store_stripped_req
        else:
            stripped_req = [lib["name"] for lib in store_req]

        textarea_value = extra_index_string + "\n" + "\n".join(stripped_req)
        textarea_value.replace("\n\n", "\n")

        # save stripped requirements
        dash.set_props("store_stripped_requirements", {"data": stripped_req})

    return {"value": textarea_value, "placeholder": placeholder}


def layout(store_req, store_stripped_req, store_extra):

    textarea_args = load_stripped_req(store_req, store_stripped_req, store_extra)

    return dmc.Container(
        [
            dmc.Textarea(
                id="textarea_stripped_req",
                label=dmc.Group(
                    [
                        dmc.Text("Requirements.txt without version restrictions"),
                        dmc.ActionIcon(
                            DashIconify(icon="tabler:reload", width=20),
                            variant="transparent",
                            id="reload_stripped_req_button",
                        ),
                        dmc.ActionIcon(
                            DashIconify(icon="lucide:download", width=20),
                            variant="transparent",
                            id="download_stripped_req_button",
                        ),
                    ]
                ),
                autosize=True,
                minRows=5,
                maxRows=15,
                **textarea_args
            ),
            dcc.Download(id="download_stripped_req"),
        ]
    )


@callback(
    Output("textarea_stripped_req", "value"),
    Input("reload_stripped_req_button", "n_clicks"),
    # this store should already be updated based on the values that have been modified in the text area
    State({"type": "store", "index": "req"}, "data"),
    State("store_extra", "data"),
    prevent_initial_call=True,
)
def update_textarea(n_clicks, store_req, store_extra):
    new_textarea_args = load_stripped_req(store_req, None, store_extra)
    return load_stripped_req["value"]


@callback(
    Output("download_stripped_req", "data"),
    Input("download_stripped_req_button", "n_clicks"),
    State("textarea_stripped_req", "value"),
    prevent_initial_call=True,
)
def download_stripped_req(n_clicks, textarea):
    return dict(content=textarea, filename="requirements.txt")
