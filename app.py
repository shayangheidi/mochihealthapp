from dash import Dash

# meta_tags are required for the app layout to be mobile responsive
app = Dash(
    __name__,
    suppress_callback_exceptions=True,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"},
        {
            "name": "title",
            "content": """Mochi Health Assessment""",
        },
    ],
    update_title=None,
)
server = app.server

#
