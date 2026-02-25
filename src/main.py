"""Main entry point for the address processing pipeline."""

import os
import sys
from pathlib import Path

# Add src directory to path so geoinfo module can be imported
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd

from geoinfo.pipeline import (
    break_address_statardize,
    break_address_qualify,
    break_address_combine,
    break_address_get_lonlat,
)


def main():
    """Execute the address processing pipeline.

    Configuration flags can be set to control which processing steps are run.
    """
    STATARDIZE = False
    QUALIFY = False
    COMBINE = False
    GET_LONLAT = True

    for input_file in os.listdir("input"):
        if input_file != "北市活動空地.csv":
            continue
        file_path = os.path.join("input", input_file)
        df = pd.read_csv(file_path)

        # 從一串地址中提取縣市、鄉鎮、村里、路、段、巷、弄、號等資訊
        if STATARDIZE:
            addressColumnName = "場所地址"  # 地址欄位名稱
            _df = break_address_statardize(df, addressColumnName)

        # 分析地址資訊的可信度
        if QUALIFY:
            _df = break_address_qualify(df)

        # 合併提取後的地址資訊
        if COMBINE:
            _df = break_address_combine(df)
            _df.to_csv("output/Address_output.csv", index=False)

        # 從合併後的地址資訊使用googleAPI取得經緯度
        if GET_LONLAT:
            df = pd.read_csv("output/Address_output.csv")
            _df = break_address_get_lonlat(df)
            _df.to_csv("output/Address_output.csv", index=False)


if __name__ == "__main__":
    main()
