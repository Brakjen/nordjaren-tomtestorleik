import urllib.parse
import json
import requests
import traceback

import pandas as pd

from pyproj import Transformer
from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


def load_postal_numbers(kommune, f="postnummer.xlsx"):
    _df_postnummer = pd.read_excel(f)
    df_postnummer = _df_postnummer.loc[(_df_postnummer["Kommunenavn"].str.lower().isin(kommune)) & (_df_postnummer["Kategori"] == "G")].reset_index(drop=True)
    df_postnummer["Query"] = df_postnummer["Postnummer"].astype(str) + " " + df_postnummer["Poststed"]
    return df_postnummer

def initialize_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.page_load_strategy = "none"
    chrome_path = ChromeDriverManager().install()
    service = Service(chrome_path)
    driver = Chrome(options=options, service=service)
    driver.implicitly_wait(5)
    return driver

def get_addresses(postal_number, postal_place, per_page=10000, address_sep="_"):
    url = f"https://adressesok.posten.no/api/v1/grouped_addresses.json?address={postal_number}%20{urllib.parse.quote(postal_place)}+&per_page={per_page}&page=1"
    result = json.loads(requests.get(url).content)

    street_addresses = []
    for grouped_address in result["groupedAddresses"]:
        street_name = grouped_address["street"]
        for address_point in grouped_address["address_points"]:
            street_number = address_point["street_number"]

            street_address = f"{street_name}{address_sep}{street_number}{address_sep}{postal_number}{address_sep}{postal_place}"
            if street_address not in street_addresses:
                street_addresses.append(street_address)
    return street_addresses

def get_all_addresses(kommune):
    df_postnummer = load_postal_numbers(kommune=kommune)
    all_addresses = []
    for postal_number, postal_place in zip(df_postnummer["Postnummer"].values.tolist(), df_postnummer["Poststed"].values.tolist()):
        addresses = get_addresses(postal_number=postal_number, postal_place=postal_place)
        if addresses:
            all_addresses.extend(addresses)
    return all_addresses

def get_matrikkel(street_name, street_number, postal_number, postal_place):
    url = f"https://seeiendom.kartverket.no/api/soekEtterEiendom?searchstring={urllib.parse.quote(street_name)}%20{street_number},%20{postal_number}%20{urllib.parse.quote(postal_place)}"
    result = json.loads(requests.get(url).content)
    if len(result) > 1:
        print("Warning: More than one matrikkel hit found on address: ", street_name, street_number, postal_number, postal_place)

    kommunenummer = result[0]["kommunenr"]
    gaardsnummer = result[0]["gaardsnr"]
    bruksnummer = result[0]["bruksnr"]
    festenummer = result[0]["festenr"]
    seksjonsnummer = result[0]["seksjonsnr"]
    return str(kommunenummer), str(gaardsnummer), str(bruksnummer), str(festenummer), str(seksjonsnummer)

def extract_tomteareal(driver):
    return float(driver.find_element(By.ID, "eiendomDetails").find_element(By.CLASS_NAME, "eiendom-table-column").find_elements(By.TAG_NAME, "tr")[1].find_element(By.TAG_NAME, "td").get_attribute("innerHTML").split()[0].replace(",", ".").replace("&nbsp;", ""))

def extract_coords(driver):
    raw = driver.find_element(By.ID, "eiendomDetails").find_element(By.CLASS_NAME, "eiendom-table-column").find_elements(By.TAG_NAME, "tr")[0].find_element(By.TAG_NAME, "td").get_attribute("innerHTML")
    E, N, proj = raw.split()
    return int(E), int(N), int(proj[1:-1])

def convert_coords(E, N, in_proj, out_proj=4326):
    transformer = Transformer.from_crs(in_proj, out_proj)
    return transformer.transform(N, E)

def build_url_kartverket(matrikkel):
    base = "https://seeiendom.kartverket.no/eiendom/"
    return base + "/".join(matrikkel)

def build_url_norgeskart(lat, lon):
    return f"https://norgeskart.no/#!?project=seeiendom&lat={lat}&lon={lon}&markerLat={lat}&markerLon={lon}&panel=Seeiendom&showSelection=true&p=Seeiendom&layers=1002,1013,1014,1015"

def collect_data(driver, limit=10, address_sep="_", output="data.csv", kommune=["strand"], verbose=True):
    addresses = get_all_addresses(kommune=kommune) if limit is None else get_all_addresses(kommune=kommune)[:limit]

    table = []
    n_addresses = len(addresses)
    for i, address in enumerate(addresses):
        print(f"Finn data: {i+1} / {n_addresses}", end="\r")
        try:
            matrikkel = get_matrikkel(*address.split(address_sep))
            kommunenummer, gaardsnummer, bruksnummer, festenummer, seksjonsnummer = matrikkel
            url = build_url_kartverket(matrikkel)
            driver.get(url)
            A = extract_tomteareal(driver)

            raw_coords = extract_coords(driver)
            raw_lat, raw_lon, _ = raw_coords

            coords = convert_coords(*raw_coords)
            lat, lon = coords

            norgeskart = build_url_norgeskart(raw_lat, raw_lon)
            row = (
                " ".join(address.split(address_sep)),
                kommunenummer,
                gaardsnummer,
                bruksnummer,
                festenummer,
                seksjonsnummer,
                url,
                norgeskart,
                A,
                lat,
                lon
            )
            table.append(row)
        except Exception:
            if verbose:
                print(address)
                print(traceback.format_exc())
                continue
            else:
                continue
    
    df = pd.DataFrame(
        data=table,
        columns=["Adresse", "Kommunenummer", "Gårdsnummer", "Bruksnummer", "Festenummer", "Seksjonsnummer", "Kartverket", "Norgeskart", "Areal", "Latitude", "Longitude"]
    )
    df.to_csv(output, index=False)
    return df.drop_duplicates(subset=["Kommunenummer", "Gårdsnummer", "Bruksnummer", "Festenummer", "Seksjonsnummer"]).reset_index(drop=True)

if __name__ == "__main__":
    driver = initialize_driver()
    df = collect_data(driver, limit=10, output="test.csv")
