import ids
import utils

import pandas as pd
import dash_leaflet as dl
import dash_leaflet.express as dlx
import dash_bootstrap_components as dbc

from dash import html, dcc
from dash_extensions.javascript import Namespace

def make_map(
    component_id: str,
    df: pd.DataFrame
) -> html.Div:
    center_lat = df["Latitude"].mean()
    center_lon = df["Longitude"].mean()
    map = dl.Map(children=[
        dl.TileLayer(), 
        utils.make_markers(ids.LEAFLET_MAP_MARKERS, df), 
        dl.GestureHandling()
    ],
    style=dict(height=F"700px"),
    id=component_id,
    center=(center_lat, center_lon),
    zoom=9,
    maxZoom=20
    )

    return html.Div(map)

def make_markers(
        component_id: str,
        df: pd.DataFrame
    ) -> dl.GeoJSON:
    points = [
        dict(lat=row["Latitude"],  lon=row["Longitude"]) for i, row in df.iterrows()
    ]
    data = dlx.dicts_to_geojson(points)
    ns = Namespace("myNamespace", "mySubNamespace")
    return  dl.GeoJSON(
        id=component_id,
        data=data, 
        options=dict(pointToLayer=ns("pointToLayer")), 
        cluster=True, 
        zoomToBoundsOnClick=True,
        zoomToBounds=False,
        spiderfyOnMaxZoom=False,
        superClusterOptions={"maxClusterRadius": 200}
    )

def make_checklist_municipality(
    component_id: str,
    municipalities: list
) -> html.Div:
    options = [
            {
                "label": [
                    html.Img(src=f"assets/{municipality.lower()}_50px.png"),
                    html.Span(municipality.upper(), style={"fontSize": 20, "padding-left": 10, "padding-right": 50})
                ],
                "value": municipality.capitalize()
            }
            for municipality in  municipalities
    ]

    checklist = dcc.Checklist(
        options,
        value=[],
        id=component_id, 
        labelStyle={"display": "inline-block", "align-items": "center"}
    )
    return html.Div(children=[html.Hr(), checklist, html.Hr()])

def make_area_rangeslider(component_id: str) -> dbc.Card:
    rangeslider = dcc.RangeSlider(
        id=component_id,
        min=0.0,
        max=10000.0,
        value=(1400, 4000.0),
        allowCross=False,
        pushable=100,
        tooltip={"placement": "bottom", "always_visible": True}
    )

    title = html.H4("Tomteareal (kvadratmeter)", style={"textAlign": "center"})

    return dbc.Card([
        dbc.CardHeader(title),
        dbc.CardBody(rangeslider)
    ])

def make_marker_details_pane() -> dbc.Card:
     return dbc.Card([
         dbc.CardHeader(html.H4("Detaljar for valgt adresse")),
         dbc.CardBody([
             html.Div(["Kommune: ", html.Span(id=ids.DETAILS_MUNICIPALITY)]),
             html.Div(["Adresse: ", html.Span(id=ids.DETAILS_ADDRESS)]),
             html.Div(["Areal  : ", html.Span(id=ids.DETAILS_AREA)]),
             dbc.ButtonGroup([
                 dbc.Button([html.Img(src="assets/norgeskart.png", style={"margin-right": "10px"}), "Norgeskart"], id=ids.DETAILS_NORGESKART, size="sm", outline=True),
                 dbc.Button([html.Img(src="assets/kartverket.png", style={"margin-right": "10px"}), "Kartverket"], id=ids.DETAILS_KARTVERKET, size="sm", outline=True),
                 dbc.Button([html.Img(src="assets/googlemaps.png", style={"margin-right": "10px"}), "Google Maps"], id=ids.DETAILS_GOOGLEMAPS, size="sm", outline=True)
             ])
         ])
     ])
