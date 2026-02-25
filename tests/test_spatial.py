"""Tests for geoinfo.geo.spatial module."""

import pandas as pd
import geopandas as gpd

from geoinfo.geo.spatial import get_village_Code_df, town_find_city


# ─── get_village_Code_df ──────────────────────────────────────────────────────


class TestGetVillageCodeDf:
    def test_returns_geodataframe(self):
        """Should return a GeoDataFrame (or dict as typed)."""
        result = get_village_Code_df()
        assert isinstance(result, gpd.GeoDataFrame)

    def test_has_required_columns(self):
        """Should contain COUNTYCODE, TOWNCODE, COUNTYNAME, TOWNNAME, VILLNAME."""
        result = get_village_Code_df()
        for col in ["COUNTYCODE", "TOWNCODE", "COUNTYNAME", "TOWNNAME", "VILLNAME"]:
            assert col in result.columns, f"Missing column: {col}"

    def test_countycode_zero_padded(self):
        """COUNTYCODE values should be zero-padded strings of at least 5 chars."""
        result = get_village_Code_df()
        for code in result["COUNTYCODE"].dropna().head(10):
            assert len(code) >= 5, f"COUNTYCODE {code!r} is shorter than 5 chars"
            assert code.isdigit() or code == "", f"COUNTYCODE {code!r} is not numeric"

    def test_towncode_is_string(self):
        """TOWNCODE values should be zero-padded numeric strings."""
        result = get_village_Code_df()
        for code in result["TOWNCODE"].dropna().head(10):
            assert isinstance(code, str), f"TOWNCODE {code!r} is not a string"
            assert code.isdigit() or code == "", f"TOWNCODE {code!r} is not numeric"

    def test_not_empty(self):
        """The shapefile should contain data."""
        result = get_village_Code_df()
        assert len(result) > 0


# ─── town_find_city ───────────────────────────────────────────────────────────


class TestTownFindCity:
    def test_known_town_to_city(self):
        """A known town name should resolve to its parent city."""
        df = pd.DataFrame({"第三級行政區": ["中山區"]})
        result = town_find_city(df, "第三級行政區")
        assert "縣市別" in result.columns
        assert result.loc[0, "縣市別"] != ""

    def test_unknown_town_returns_empty(self):
        """An unknown town name should return empty city."""
        df = pd.DataFrame({"第三級行政區": ["不存在的區"]})
        result = town_find_city(df, "第三級行政區")
        assert result.loc[0, "縣市別"] == ""

    def test_multiple_rows(self):
        """Should handle multiple rows."""
        df = pd.DataFrame({"第三級行政區": ["中山區", "不存在區"]})
        result = town_find_city(df, "第三級行政區")
        assert len(result) == 2
        assert result.loc[0, "縣市別"] != ""
        assert result.loc[1, "縣市別"] == ""
