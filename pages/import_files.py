from dash import Dash, dcc, html
from dash import callback, Input, Output, State, ctx, Patch, set_props, ALL, MATCH
import base64
import io
import utils
import dash


# process uploaded requirements.txt file and save its contents in dcc.store store_raw
@callback(
    Output({"type": "textarea", "index": MATCH}, "value"),
    Input({"type": "upload", "index": MATCH}, "contents"),
    Input({"type": "upload", "index": MATCH}, "filename"),
    Input({"type": "clear-uploaded", "index": MATCH}, "n_clicks"),
    prevent_initial_call=True,
)
def update_output(contents, filename, clear_button):
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    elif ctx.triggered_id["type"] == "clear-uploaded":
        return ""

    elif contents:
        # process the contents
        content_type, content_string = contents.split(",")
        decoded_base64 = base64.b64decode(content_string)
        decoded_io = io.StringIO(decoded_base64.decode("utf-8"))
        file_content = decoded_io.read().replace("\ufeff", "")
        return file_content

    else:
        return dash.no_update


@callback(
    Output("store_extra", "data"),
    Output({"type": "store", "index": "req"}, "data"),
    Output({"type": "store", "index": "pip_freeze"}, "data"),
    Input({"type": "textarea", "index": "req"}, "value"),
    Input({"type": "textarea", "index": "pip_freeze"}, "value"),
    prevent_initial_call=True,
)
def process_textarea(raw_info_req, raw_info_pip):
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    file_type = ctx.triggered_id["index"]

    if file_type == "req":
        req_list = utils.read_requirements_text(raw_info_req)
        req_name_version = [
            utils.extract_name_version(line, file_type="req")
            for line in req_list
            if line
        ]
        store_extra = Patch()
        store_extra["extra_index_url"] = utils.extract_extra_index_url(raw_info_req)
        return store_extra, req_name_version, dash.no_update
    else:
        pip_list = utils.read_requirements_text(raw_info_pip)
        pip_name_version = [
            utils.extract_name_version(line, file_type="pip_freeze")
            for line in pip_list
            if line
        ]
        return dash.no_update, dash.no_update, pip_name_version
