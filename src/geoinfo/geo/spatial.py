"""Geo-spatial lookup functions using shapefiles for village/town/city resolution."""

import os

import geopandas as gpd
from os.path import join, dirname
from dotenv import find_dotenv
from shapely.geometry import Point

from geoinfo.constants import VILLAGE_SHP_FILENAME, VILLAGE_DATA_DIR


def town_find_city(df, townName_cloumn):
    """
    第三行政區找出縣市
    """
    town_code_shp = gpd.read_file(
        join(dirname(find_dotenv()), VILLAGE_DATA_DIR, VILLAGE_SHP_FILENAME)
    )
    # 透過df的第三行政區對應town_code_shp的TOWNNAME找出TOWNNAME縣市並放在df的縣市別
    df["縣市別"] = df[townName_cloumn].apply(
        lambda x: (
            town_code_shp[town_code_shp["TOWNNAME"] == x]["COUNTYNAME"].values[0]
            if not town_code_shp[town_code_shp["TOWNNAME"] == x].empty
            else ""
        )
    )
    return df


def coordinate_to_address(df, lon_column, lat_column):
    """
    經緯度轉地址 (使用空間連接)
    """
    town_code_shp = gpd.read_file(
        join(dirname(find_dotenv()), VILLAGE_DATA_DIR, VILLAGE_SHP_FILENAME)
    )

    # 將DataFrame轉換為GeoDataFrame
    geometry = [Point(xy) for xy in zip(df[lon_column], df[lat_column])]
    points_gdf = gpd.GeoDataFrame(df, geometry=geometry, crs=town_code_shp.crs)

    # 進行空間連接
    joined_gdf = gpd.sjoin(points_gdf, town_code_shp, how="left", predicate="within")

    # 將所有列(除了geometry)添加到原始DataFrame
    columns_to_add = [col for col in town_code_shp.columns if col != "geometry"]
    print(joined_gdf.head(10))
    for col in columns_to_add:
        df[col] = joined_gdf[f"{col}"]

    # 將 NaN 值轉換為空字串
    for col in columns_to_add:
        df[col] = df[col].fillna("")

    return df


def get_village_Code_df() -> dict:
    """讀取村里對照表"""
    # Traverse up: geo/ → geoinfo/ → src/ → project_root/
    path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "..",
        VILLAGE_DATA_DIR.replace("/", os.sep),
    )
    village_Code_df = gpd.read_file(os.path.join(path, VILLAGE_SHP_FILENAME))
    village_Code_df["COUNTYCODE"] = (
        village_Code_df["COUNTYCODE"]
        .fillna("")
        .astype(str)
        .apply(lambda x: x.split(".")[0].zfill(5))
    )
    village_Code_df["TOWNCODE"] = (
        village_Code_df["TOWNCODE"]
        .fillna("")
        .astype(str)
        .apply(lambda x: x.split(".")[0].zfill(3))
    )
    return village_Code_df
