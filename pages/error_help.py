import dash
from dash import Dash, dcc, html, register_page
from dash import callback, Input, Output, State, ctx
import dash_mantine_components as dmc

layout = html.Div(
    [
        dmc.Textarea(
            label="Paste traceback/logs here",
            placeholder="""
        Format is typically similar to: `ImportError: cannot import name 'url_quote' from 'werkzeug.urls' (/app/.heroku/python/lib/python3.9/site-packages/werkzeug/urls.py)`.\n Include as many lines as possible!
        """,
            autosize=True,
            minRows=10,
        ),
    ]
)

register_page("Error help", path="/error-help", layout=layout)
