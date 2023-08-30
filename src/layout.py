import utils
import ids

import pandas as pd
import dash_bootstrap_components as dbc

from dash import html

def render(df: pd.DataFrame) -> html.Div:
    municipalities = df["Kommune"].unique().tolist()

    return html.Div(children=[
        dbc.Row([dbc.Col(utils.make_map(ids.LEAFLET_MAP, df))]),
        dbc.Row([dbc.Col(utils.make_checklist_municipality(ids.CHECKLIST_MUNICIPALITIES, municipalities))], class_name="text-center"),
        dbc.Row([
            dbc.Col(utils.make_area_rangeslider(ids.RANGESLIDER_AREA_FILTER)),
            dbc.Col(utils.make_marker_details_pane())
        ])
    ])
