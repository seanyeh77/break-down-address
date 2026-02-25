"""Tests for geoinfo.pipeline module."""

import numpy as np
import pandas as pd

from geoinfo.pipeline import (
    address_standardize,
    break_address_qualify,
    break_address_combine,
)


# ─── address_standardize ─────────────────────────────────────────────────────


class TestAddressStandardize:
    def test_county_code_replacement(self):
        """Old county codes should be replaced with new ones."""
        df = pd.DataFrame({"City": ["10001", "10003"], "Township": ["001", "002"]})
        result = address_standardize(df)
        assert result.loc[0, "City"] == "65000"  # 台北縣 -> 新北市
        assert result.loc[1, "City"] == "68000"  # 桃園縣 -> 桃園市

    def test_zero_padding(self):
        """City and Township codes should be zero-padded."""
        df = pd.DataFrame({"City": [63000], "Township": [1]})
        result = address_standardize(df)
        assert result.loc[0, "City"] == "63000"
        assert result.loc[0, "Township"] == "001"

    def test_city_district_code_merge(self):
        """Should create city_district_code_merge column."""
        df = pd.DataFrame({"City": ["63000"], "Township": ["001"]})
        result = address_standardize(df)
        assert "city_district_code_merge" in result.columns
        assert result.loc[0, "city_district_code_merge"] == "63000001"

    def test_nan_handling(self):
        """NaN values should be handled gracefully."""
        df = pd.DataFrame({"City": [np.nan], "Township": [np.nan]})
        result = address_standardize(df)
        assert result.loc[0, "City"] == "00000"
        assert result.loc[0, "Township"] == "000"

    def test_no_city_township_columns(self):
        """Should not error if City/Township columns don't exist."""
        df = pd.DataFrame({"other": ["value"]})
        result = address_standardize(df)
        assert "city_district_code_merge" not in result.columns

    def test_multiple_replacements(self):
        """All old codes should be replaced correctly."""
        df = pd.DataFrame(
            {
                "City": ["10006", "10019", "10011", "10021"],
                "Township": ["001", "001", "001", "001"],
            }
        )
        result = address_standardize(df)
        assert result.loc[0, "City"] == "66000"  # 台中縣
        assert result.loc[1, "City"] == "66000"  # 台中市
        assert result.loc[2, "City"] == "67000"  # 台南縣
        assert result.loc[3, "City"] == "67000"  # 台南市


# ─── break_address_qualify ────────────────────────────────────────────────────


class TestBreakAddressQualify:
    def test_replaces_nan_and_empty(self):
        """Should replace NaN and empty strings with None before qualifying."""
        df = pd.DataFrame(
            {
                "縣市別": ["臺北市"],
                "縣市別(address)": [np.nan],
                "縣市別(citycode)": [""],
                "第三級行政區": ["中山區"],
                "第三級行政區(address)": [np.nan],
                "第三級行政區(towncode)": [np.nan],
                "路": ["中山路"],
                "地域": [np.nan],
                "巷": [np.nan],
                "弄": [np.nan],
                "號": ["42號"],
                "特殊字": [0],
            }
        )
        result = break_address_qualify(df)
        assert "可信度" in result.columns
        assert result.loc[0, "可信度"] == "C"


# ─── break_address_combine ───────────────────────────────────────────────────


class TestBreakAddressCombine:
    def test_creates_address2(self):
        """Should create Address2 column from combined fields."""
        df = pd.DataFrame(
            {
                "縣市別": ["臺北市"],
                "第三級行政區": ["中山區"],
                "路": ["中山路"],
                "地域": [None],
                "段": [None],
                "巷": [None],
                "之(巷)": [None],
                "弄": [None],
                "之(弄)": [None],
                "號": ["1號"],
                "之(號)": [None],
            }
        )
        result = break_address_combine(df)
        assert "Address2" in result.columns
        assert result.loc[0, "Address2"] == "臺北市中山區中山路1號"

    def test_handles_all_nan(self):
        """Should not error with all-NaN row."""
        df = pd.DataFrame(
            {
                "縣市別": [np.nan],
                "第三級行政區": [np.nan],
                "路": [np.nan],
                "地域": [np.nan],
                "段": [np.nan],
                "巷": [np.nan],
                "之(巷)": [np.nan],
                "弄": [np.nan],
                "之(弄)": [np.nan],
                "號": [np.nan],
                "之(號)": [np.nan],
            }
        )
        result = break_address_combine(df)
        assert result.loc[0, "Address2"] == ""
