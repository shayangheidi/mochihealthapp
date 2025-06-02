from dash import (
    html,
    dcc,
    Output,
    Input,
    State,
)
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import gspread
from google.auth import default
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import yaml
from app import app, server  # noqa: F401

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

creds, _ = default()
gc = gspread.authorize(creds)
client = gspread.authorize(creds)

sheet = client.open_by_key("1FyYJj9wjjvLefmILiOH3NhcAdxIU7Dpx5zsJeli2Wec").sheet1


with open("config.yml") as f:
    config = yaml.safe_load(f)

app.title = "Mochi Health Mood"

app.layout = dmc.MantineProvider(
    id="main-page",
    theme={
        "colorScheme": "dark",
        "fontFamily": "'Inter', sans-serif",
        "primaryColor": config["display"]["accent_color_dark"],
        "keepTransitions": True,
        "components": {
            "Button": {"styles": {"root": {"fontWeight": 400}}},
            "Alert": {"styles": {"title": {"fontWeight": 500}}},
            "AvatarGroup": {"styles": {"truncated": {"fontWeight": 500}}},
            "Slider": {
                "styles": {
                    "thumb": {
                        "border-color": config["display"]["accent_colorcode_dark"],
                        "background-color": config["display"]["accent_colorcode_dark"],
                        "width": "15px",
                        "height": "15px",
                    }
                }
            },
        },
    },
    inherit=True,
    withGlobalStyles=True,
    withNormalizeCSS=True,
    children=html.Div(
        [
            html.Div(
                [
                    html.H1(children="Mochi Health"),
                ],
                className="header",
            ),
            html.P(
                "Created By Shayan Gheidi",
                style={"width": "fit-content", "margin-inline": "auto"},
            ),
            html.Div(
                [
                    dmc.Tooltip(
                        dmc.ActionIcon(
                            DashIconify(
                                icon="ic:outline-light-mode",
                                width=config["display"]["settings-darkmode-icon-width"],
                            ),
                            id="button-darkmode",
                            radius="xl",
                            size="xl",
                            variant="transparent",
                            style={"margin-top": "5px"},
                        ),
                        label=config["tooltips"]["actionicon-darkmode"],
                        openDelay=600,
                        position="left",
                        transition="slide-right",
                        transitionDuration=300,
                    ),
                ],
                className="top-buttons",
            ),
            html.Div(
                [
                    dmc.Select(
                        value="😊",
                        data=["😊", "😠", "😕", "🎉"],
                        label="How are you feeling?",
                        id="mood-select",
                        style={"width": "400px", "margin-inline": "auto"},
                    ),
                    dmc.Textarea(
                        id="mood-comment",
                        label="Add a comment (optional)",
                        placeholder="Tell us more about your experience today",
                        autosize=True,
                        minRows=1,
                        maxRows=3,
                        style={"width": "400px", "margin-inline": "auto"},
                    ),
                    dmc.Button(
                        "Submit",
                        id="submit-mood",
                        leftIcon=DashIconify(
                            icon="material-symbols-light:check-box-outline-rounded",
                            width=25,
                        ),
                        style={"width": "400px", "margin-inline": "auto"},
                    ),
                    dmc.Alert(
                        icon=DashIconify(icon="bxs:happy", width=25),
                        id="alert",
                        hide=True,
                        withCloseButton=True,
                        style={"margin-inline": "auto"},
                        radius="md",
                        className="alert",
                    ),
                    dmc.Select(
                        id="mood-date-filter",
                        label="Filter by date",
                        value="today",
                        data=[
                            {"label": "Today", "value": "today"},
                            {"label": "Past Week", "value": "week"},
                            {"label": "Past Month", "value": "month"},
                        ],
                        style={"width": "400px", "margin-inline": "auto"},
                    ),
                    dcc.Graph(
                        id="mood-histogram",
                        style={
                            "width": "500px",
                            "margin-bottom": "100px",
                            "margin-inline": "auto",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "flex-direction": "column",
                    "margin-inline": "auto",
                    "grid-gap": "20px",
                },
            ),
        ],
        id="main",
        className="main",
    ),
)


@app.callback(
    Output("alert", "children"),
    Output("alert", "hide"),
    Input("submit-mood", "n_clicks"),
    State("mood-select", "value"),
    State("mood-comment", "value"),
    prevent_initial_call=True,
)
def submit_mood(n_clicks, mood, comment):
    if not mood:
        return "Please select a mood.", False
    if comment is None:
        comment = ""

    try:
        row = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), mood, comment]
        sheet.append_row(row)
        return "Mood submitted successfully!", False
    except Exception as e:
        return f"Error: {e}", False


@app.callback(
    Output("mood-histogram", "figure"),
    Input("mood-date-filter", "value"),
    Input("submit-mood", "n_clicks"),
    Input("button-darkmode", "n_clicks"),
)
def update_mood_barchart(date_filter, n_clicks, clicks):
    clicks = 0 if clicks is None else clicks
    plot_theme = "plotly_dark" if clicks % 2 == 0 else "plotly_white"

    try:
        records = sheet.get_all_records()
        df = pd.DataFrame(records)

        if df.empty or "Timestamp" not in df.columns:
            return px.bar(title="No data available.", template=plot_theme)

        df["Timestamp"] = pd.to_datetime(df["Timestamp"])
        df["Date"] = df["Timestamp"].dt.date

        # Filter by time range
        today = datetime.now().date()
        if date_filter == "today":
            df = df[df["Date"] == today]
        elif date_filter == "week":
            df = df[df["Date"] >= today - timedelta(days=7)]
        elif date_filter == "month":
            df = df[df["Date"] >= today - timedelta(days=30)]

        # Group and count moods (across all days in selected range)
        mood_counts = (
            df["Mood"]
            .value_counts()
            .reindex(["😊", "😠", "😕", "🎉"], fill_value=0)
            .reset_index()
        )
        mood_counts.columns = ["Mood", "Count"]

        # Plot bar chart with emojis as x-axis
        fig = px.bar(
            mood_counts,
            x="Mood",
            y="Count",
            title="Mood Frequency",
            template=plot_theme,
            color="Mood",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig.update_layout(
            xaxis_title="Mood",
            yaxis_title="Count",
            showlegend=False,
        )
        return fig

    except Exception as e:
        return px.bar(title=f"Error: {str(e)}", template=plot_theme)


@app.callback(
    Output("main-page", "theme"),
    Output("button-darkmode", "children"),
    Input("button-darkmode", "n_clicks"),
    State("main-page", "theme"),
    prevent_initial_call=True,
)
def darkmode(n_clicks, theme):
    if theme["colorScheme"] == "dark":
        return (
            {
                "colorScheme": "light",
                "fontFamily": "'Inter', sans-serif",
                "primaryColor": config["display"]["accent_color_light"],
                "keepTransitions": True,
                "components": {
                    "Button": {"styles": {"root": {"fontWeight": 400}}},
                    "Alert": {"styles": {"title": {"fontWeight": 500}}},
                    "AvatarGroup": {"styles": {"truncated": {"fontWeight": 500}}},
                    "Slider": {
                        "styles": {
                            "thumb": {
                                "border-color": config["display"][
                                    "accent_colorcode_light"
                                ],
                                "background-color": config["display"][
                                    "accent_colorcode_light"
                                ],
                                "width": "15px",
                                "height": "15px",
                            }
                        }
                    },
                },
            },
            DashIconify(
                icon="material-symbols:dark-mode",
                width=config["display"]["settings-darkmode-icon-width"],
            ),
        )
    else:
        return (
            {
                "colorScheme": "dark",
                "fontFamily": "'Inter', sans-serif",
                "primaryColor": config["display"]["accent_color_dark"],
                "keepTransitions": True,
                "components": {
                    "Button": {"styles": {"root": {"fontWeight": 400}}},
                    "Alert": {"styles": {"title": {"fontWeight": 500}}},
                    "AvatarGroup": {"styles": {"truncated": {"fontWeight": 500}}},
                    "Slider": {
                        "styles": {
                            "thumb": {
                                "border-color": config["display"][
                                    "accent_colorcode_dark"
                                ],
                                "background-color": config["display"][
                                    "accent_colorcode_dark"
                                ],
                                "width": "15px",
                                "height": "15px",
                            }
                        }
                    },
                },
            },
            DashIconify(
                icon="ic:outline-light-mode",
                width=config["display"]["settings-darkmode-icon-width"],
            ),
        )


if __name__ == "__main__":
    app.run_server(
        host="127.0.0.1", port="8080", debug=True, dev_tools_hot_reload=False
    )
