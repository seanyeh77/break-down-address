"""Google Maps API geocoding functions for converting addresses to coordinates."""

import multiprocessing as mp
import time

import googlemaps
import numpy as np
import pandas as pd

from geoinfo.constants import (
    GEOCODE_LANGUAGE,
    GEOCODE_BATCH_SIZE,
    GEOCODE_OUTPUT_CSV,
    GAPI_COMPONENT_MAPPING,
)


def address_get_pos(df, column_name, api_key):
    t = 0
    if "Lat" not in df.columns:
        df["Lat"] = None
    if "Lon" not in df.columns:
        df["Lon"] = None

    while len(df[df[column_name].notnull() & (df["已處理"] != 1)]) != 0:
        start = time.time()
        mask = df[column_name].notnull() & (df["已處理"] != 1)
        filtered_df = df[mask].head(GEOCODE_BATCH_SIZE)
        print(filtered_df.head(1))

        cup_count = min(mp.cpu_count(), len(filtered_df))
        chunks = np.array_split(filtered_df, cup_count)

        processed_chunks = []
        with mp.Pool(cup_count) as pool:
            results = [
                pool.apply_async(process_chunk, args=(chunk, column_name, api_key))
                for chunk in chunks
            ]
            processed_chunks = [r.get() for r in results]

        # 更新原始資料框
        for processed_chunk in processed_chunks:
            df.update(processed_chunk)

        df.to_csv(GEOCODE_OUTPUT_CSV, index=False)
        print(t, time.time() - start)
        t += 1


def get_lonlat(rowdata, column_name, api_key):
    gmaps = googlemaps.Client(key=api_key)
    rowdata["已處理"] = 1
    if rowdata[column_name] is None:
        return rowdata
    get_gmaps_pos = gmaps.geocode(rowdata[column_name], language=GEOCODE_LANGUAGE)
    df_gmaps_pos = pd.DataFrame(get_gmaps_pos)
    if len(df_gmaps_pos) == 0:
        return rowdata

    for address_component in df_gmaps_pos["address_components"][0]:
        for gapi_type, column in GAPI_COMPONENT_MAPPING.items():
            if gapi_type in address_component["types"]:
                rowdata[column] = address_component["long_name"]
                break

    pos_lat = df_gmaps_pos["geometry"].map(lambda x: x["location"]["lat"])
    pos_lng = df_gmaps_pos["geometry"].map(lambda x: x["location"]["lng"])

    rowdata["Lat"] = pos_lat[0]
    rowdata["Lon"] = pos_lng[0]
    rowdata["Address3"] = str(df_gmaps_pos["formatted_address"][0])

    return rowdata


# 定義處理每個分批的函數
def process_chunk(chunk, column_name, api_key):
    try:
        return chunk.apply(
            get_lonlat,
            args=(
                column_name,
                api_key,
            ),
            axis=1,
        )
    except Exception:
        return None
