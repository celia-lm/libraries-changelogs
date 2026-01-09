import dash
from dash import Dash, dcc, html
from dash import callback, Input, Output, State, ALL, Patch
import dash_mantine_components as dmc
import utils

cache = utils.cache

@cache.memoize()
def changelog_accordion(lib_name):
    lib = utils.get_library_history(lib_name)
    repo_url = utils.get_repo_url(lib)

    if repo_url.get("url"):
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
