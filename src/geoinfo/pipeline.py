"""Pipeline orchestration functions that compose the address processing workflow."""

import multiprocessing as mp
import os

import numpy as np
import pandas as pd
from os.path import join, dirname
from dotenv import load_dotenv

from geoinfo.address.parser import apply_async_wrapper
from geoinfo.address.qualify import addrss_data_qualify, combine_address
from geoinfo.geo.spatial import get_village_Code_df
from geoinfo.geocoding.google_api import address_get_pos
from geoinfo.constants import (
    COUNTY_CODE_REPLACE,
    DEFAULT_ADDRESS_COLUMN,
    DEFAULT_OUTPUT_ADDRESS_COLUMN,
    GEOCODE_OUTPUT_COLUMNS,
    MAX_POOL_SPLITS,
)


def address_standardize(df: pd.DataFrame):
    """將縣市代號更新 1000XX -> 6X000"""
    if "City" in df.columns:
        df["City"] = (
            df["City"].fillna("").astype(str).apply(lambda x: x.split(".")[0].zfill(5))
        )
        df["City"] = df["City"].replace(COUNTY_CODE_REPLACE)
    if "Township" in df.columns:
        df["Township"] = (
            df["Township"]
            .fillna("")
            .astype(str)
            .apply(lambda x: x.split(".")[0].zfill(3))
        )
    if "City" in df.columns or "Township" in df.columns:
        df["city_district_code_merge"] = df["City"] + df["Township"]

    return df


def get_df_address_info(df, village_Code_df, addressColumnName):
    pool = mp.Pool()
    _slice = min(MAX_POOL_SPLITS, df.shape[0])
    df = df.reset_index(drop=True)
    res = [[] for _ in range(_slice)]
    for i, _input in enumerate(np.array_split(df, _slice)):
        _input = _input.reset_index(drop=True)
        res[i] = pool.apply_async(
            apply_async_wrapper,
            args=(_input, village_Code_df, addressColumnName),
        )

    pool.close()
    pool.join()

    lis = []
    for x in res:
        try:
            result = x.get()
            lis.append(result)
        except Exception as e:
            print(f"Error in worker process: {e}")
            continue

    if not lis:
        return df

    df = pd.concat(lis, ignore_index=True)
    df = df.drop_duplicates().reset_index(drop=True)
    df = df.replace({np.nan: None, "": None})

    if "city_district_code_merge" in df.columns:
        del df["city_district_code_merge"]
    return df


def break_address_statardize(
    df, addressColumnName: str = DEFAULT_ADDRESS_COLUMN
) -> pd.DataFrame:
    df = df.replace({np.nan: None})
    village_Code_df = get_village_Code_df()  # 取得村里代碼表
    df = address_standardize(df)  # 更新縣市代號
    return get_df_address_info(
        df, village_Code_df, addressColumnName
    )  # 批次取得地址資訊


def break_address_qualify(df) -> pd.DataFrame:
    df = df.replace({np.nan: None, "": None})
    return addrss_data_qualify(df)


def break_address_combine(df) -> pd.DataFrame:
    df = df.replace({np.nan: None, "": None})
    df.loc[:, DEFAULT_OUTPUT_ADDRESS_COLUMN] = df.apply(combine_address, axis=1)
    return df


def break_address_get_lonlat(
    df, env_path: str = ".env", address_column_name: str = DEFAULT_OUTPUT_ADDRESS_COLUMN
) -> pd.DataFrame:

    if address_column_name not in df.columns:
        raise ValueError(f"{address_column_name} column not found")

    # 替換 NaN 和空字串
    df = df.replace({np.nan: None, "": None})

    # 確保所有 geocode 輸出欄位存在
    for col in GEOCODE_OUTPUT_COLUMNS:
        if col not in df.columns:
            df[col] = None
    if "已處理" not in df.columns:
        df["已處理"] = 0

    # Traverse up: geoinfo/ → src/ → project_root/
    dotenv_path = join(dirname(__file__), "..", "..", env_path)
    load_dotenv(dotenv_path, override=True)

    GOOGLE_PLACES_API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY")

    address_get_pos(df, address_column_name, GOOGLE_PLACES_API_KEY)
    return df
