import ids
import utils
import json
import sys

import pandas as pd
import dash_leaflet as dl
import dash_leaflet.express as dlx

from dash import html, dcc
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output
from maindash import app

from globals import DATA


@app.callback(
    Output(ids.LEAFLET_MAP_MARKERS, "data"),
    inputs=[
        Input(ids.CHECKLIST_MUNICIPALITIES, "value"),
        Input(ids.RANGESLIDER_AREA_FILTER, "value")
    ]
)
def filter_data(
    municipalities: list[str], 
    area_range: list[float]
) -> dl.GeoJSON:
    if municipalities is None or area_range is None:
        municipalities = DATA["Kommune"].unique().tolist()
        area_range = (DATA["Areal"].min(), DATA["Areal"].max())
    
    df_filtered = DATA.loc[(DATA["Kommune"].isin(municipalities)) & (DATA["Areal"].between(*area_range))]
    df_filtered = df_filtered.drop_duplicates(subset=["Latitude", "Longitude"])

    points = [
        dict(lat=row["Latitude"],  lon=row["Longitude"]) for i, row in df_filtered.iterrows()
    ]
    data = dlx.dicts_to_geojson(points)
    return data

@app.callback(
    [
        Output(ids.DETAILS_MUNICIPALITY, "children"),
        Output(ids.DETAILS_ADDRESS, "children"),
        Output(ids.DETAILS_AREA, "children"),
        Output(ids.DETAILS_NORGESKART, "href"),
        Output(ids.DETAILS_KARTVERKET, "href"),
        Output(ids.DETAILS_GOOGLEMAPS, "href")
    ],
    Input(ids.LEAFLET_MAP_MARKERS,  "click_feature")
)
def show_details(
    feature
) -> tuple:
    if feature is None:
        raise PreventUpdate
    
    if feature["properties"]["cluster"]:
        raise PreventUpdate
    
    lon, lat = feature["geometry"]["coordinates"]
    row = DATA.loc[((DATA.Latitude - lat).abs() < 1.0e-9) & ((DATA.Longitude - lon).abs() < 1.0e-9)]
    return (
        row.Kommune.values[0],
        row.Adresse.values[0].title(),
        row.Areal.values[0],
        row.Norgeskart.values[0],
        row.Kartverket.values[0],
        row.GoogleMaps.values[0]
    )
