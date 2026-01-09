import dash
from dash import dcc, html
from dash import callback, Input, Output, State, ctx, clientside_callback
import dash_ag_grid as dag
import dash_mantine_components as dmc
import pandas as pd
import utils

cache = utils.cache


@cache.memoize()
def libraries_grid(lib_data, req=True, pip=True):

    columnDefs = [
        {"field": "name", "hide": False},
        # req
        {
            "headerName": "requirements.txt",
            "children": [
                {"field": "req_version", "headerName": "Version", "hide": not req},
                {"field": "req_pinned", "headerName": "Pinned", "hide": not req},
                {"field": "raw_line_req", "headerName": "Raw line"},
                {
                    "field": "req_release_date",
                    "headerName": "Release date",
                    "filter": "agDateColumnFilter",
                    "filterValueGetter": {
                        "function": "d3.timeParse('%d/%m/%Y')(params.data.req_release_date)"
                    },
                    "hide": not req,
                },
            ],
        },
        # installed
        {
            "headerName": "Installed",
            "children": [
                {
                    "field": "installed_version",
                    "headerName": "Version",
                    "hide": not pip,
                },
                {
                    "field": "installed_release_date",
                    "headerName": "Release date",
                    "filter": "agDateColumnFilter",
                    "filterValueGetter": {
                        "function": "d3.timeParse('%d/%m/%Y')(params.data.installed_release_date)"
                    },
                    "hide": not pip,
                },
            ],
        },
        # new
        {
            "headerName": "Newest",
            "children": [
                {"field": "newest_version", "headerName": "Version", "hide": False},
                {
                    "field": "newest_release_date",
                    "headerName": "Release date",
                    "hide": False,
                    "filter": "agDateColumnFilter",
                    "filterValueGetter": {
                        "function": "d3.timeParse('%Y-%m-%d')(params.data.newest_release_date)"
                    },
                    "sort": "desc",
                },
            ],
        },
        # other info
        # https://community.plotly.com/t/how-to-make-dash-ag-grid-table-cells-hyperlinked/77482/9
        {
            "field": "urls",
            "headerName": "Links",
            "cellRenderer": "markdown",
            "linkTarget": "_blank",
        },
    ]

    defaultColDef = {
        "sortable": True,
        "filter": True,
        "floatingFilter": True,
        "hide": True,
    }

    return dag.AgGrid(
        id="libraries_grid",
        rowData=lib_data,
        columnDefs=columnDefs,
        defaultColDef=defaultColDef,
        columnSize="sizeToFit",
        dashGridOptions={
            "sideBar": True,
            "rowSelection": {
                "mode": "multiRow",
                "headerCheckbox": False,
                "enableClickSelection": True,
            },
        },
        enableEnterpriseModules=True,
        licenseKey="placeholder",
    )


def layout(store_req, store_pip):

    req = True
    pip = True

    if not any([store_req, store_pip]):
        return dmc.Container(
            "Upload requirements.txt and/or pip_freeze.txt to see each packages' history"
        )
    elif store_req and store_pip:
        req_df = pd.DataFrame.from_records(store_req)
        pip_df = pd.DataFrame.from_records(store_pip)
        # merge both sources
        df = req_df.merge(pip_df, how="outer")
        df_records = df.to_dict("records")
    elif store_req:
        df_records = store_req.copy()
        pip = False
    elif store_pip:
        df_records = store_pip.copy()
        req = False

    df_complete_records = [utils.get_library_history(lib) for lib in df_records]
    return dmc.Container(
        [
            dmc.Button(
                id="show_details_button",
                children="Show selected libraries changelogs",
                disabled=True,
                mt="10px",
                mb="10px",
            ),
            html.Br(),
            libraries_grid(df_complete_records, req, pip),
        ],
        fluid=True,
    )


# enable "Show changelogs" button
clientside_callback(
    """
    function(selectedRows) {
        console.log(selectedRows);
        if (selectedRows === undefined || selectedRows.length == 0) {
            console.log('true');
            return true;
        } else {
            console.log('false');
            return false;
            }
       }
    """,
    Output("show_details_button", "disabled"),
    Input("libraries_grid", "selectedRows"),
    prevent_initial_call=True,
)


@callback(
    Input("show_details_button", "n_clicks"),
    State("libraries_grid", "selectedRows"),
    prevent_initial_call=True,
)
def switch_to_chagelogs(n_clicks, selectedRows):
    if selectedRows:
        libs = "&".join([lib["name"] for lib in selectedRows])

        dash.set_props(
            "location", {"pathname": dash.get_relative_path("/changelogs"), "search": f"?libs={libs}"}
        )
        dash.set_props("choose_action", {"value": "changelogs"})
