"""Tests for geoinfo.address.qualify module."""

import pandas as pd

from geoinfo.address.qualify import addrss_data_qualify, combine_address


# ─── combine_address ──────────────────────────────────────────────────────────


class TestCombineAddress:
    def test_full_address(self):
        row = pd.Series(
            {
                "縣市別": "臺北市",
                "第三級行政區": "中山區",
                "路": "中山路",
                "地域": "",
                "段": "一段",
                "巷": "10巷",
                "之(巷)": None,
                "弄": "5弄",
                "之(弄)": None,
                "號": "42號",
                "之(號)": None,
            }
        )
        result = combine_address(row)
        assert "臺北市" in result
        assert "中山區" in result
        assert "中山路" in result
        assert "10巷" in result
        assert "5弄" in result
        assert "42號" in result

    def test_minimal_address(self):
        row = pd.Series(
            {
                "縣市別": "臺北市",
                "第三級行政區": None,
                "路": "中山路",
                "地域": None,
                "段": None,
                "巷": None,
                "之(巷)": None,
                "弄": None,
                "之(弄)": None,
                "號": "1號",
                "之(號)": None,
            }
        )
        result = combine_address(row)
        assert result == "臺北市中山路1號"

    def test_with_of_values(self):
        """之(號) should be inserted into the 號 value."""
        row = pd.Series(
            {
                "縣市別": "臺北市",
                "第三級行政區": "中山區",
                "路": "中山路",
                "地域": None,
                "段": None,
                "巷": None,
                "之(巷)": None,
                "弄": None,
                "之(弄)": None,
                "號": "42號",
                "之(號)": "之1",
            }
        )
        result = combine_address(row)
        assert "42" in result
        assert "之1" in result

    def test_all_none(self):
        row = pd.Series(
            {
                "縣市別": None,
                "第三級行政區": None,
                "路": None,
                "地域": None,
                "段": None,
                "巷": None,
                "之(巷)": None,
                "弄": None,
                "之(弄)": None,
                "號": None,
                "之(號)": None,
            }
        )
        result = combine_address(row)
        assert result == ""


# ─── addrss_data_qualify ──────────────────────────────────────────────────────


class TestAddrssDataQualify:
    def _make_df(self, rows):
        """Helper to create a DataFrame with all required columns.
        縣市別 and 第三級行政區 default to valid strings to avoid triggering
        the H credibility rule (NaN != NaN → True → H).
        """
        base = {
            "縣市別": "臺北市",
            "縣市別(address)": None,
            "縣市別(citycode)": None,
            "第三級行政區": "中山區",
            "第三級行政區(address)": None,
            "第三級行政區(towncode)": None,
            "路": None,
            "地域": None,
            "巷": None,
            "弄": None,
            "號": None,
            "特殊字": 0,
        }
        data = []
        for row in rows:
            merged = {**base, **row}
            data.append(merged)
        return pd.DataFrame(data)

    def test_credibility_a(self):
        """A: 有路無地域有巷有弄有號"""
        df = self._make_df([{"路": "中山路", "巷": "10巷", "弄": "5弄", "號": "42號"}])
        result = addrss_data_qualify(df)
        assert result.loc[0, "可信度"] == "A"

    def test_credibility_b(self):
        """B: 有路無地域有巷無弄有號"""
        df = self._make_df([{"路": "中山路", "巷": "10巷", "號": "42號"}])
        result = addrss_data_qualify(df)
        assert result.loc[0, "可信度"] == "B"

    def test_credibility_c(self):
        """C: 有路無地域無巷無弄有號"""
        df = self._make_df([{"路": "中山路", "號": "42號"}])
        result = addrss_data_qualify(df)
        assert result.loc[0, "可信度"] == "C"

    def test_credibility_d(self):
        """D: 無路有地域"""
        df = self._make_df([{"地域": "某地域", "號": "1號"}])
        result = addrss_data_qualify(df)
        assert result.loc[0, "可信度"] == "D"

    def test_credibility_e_special_char(self):
        """E: 有特殊字"""
        df = self._make_df([{"路": "中山路", "號": "42號", "特殊字": 1}])
        result = addrss_data_qualify(df)
        assert result.loc[0, "可信度"] == "E"

    def test_credibility_e_long_road(self):
        """E: road name too long (>= 6 chars)"""
        df = self._make_df([{"路": "非常長的路名稱", "號": "42號"}])
        result = addrss_data_qualify(df)
        assert result.loc[0, "可信度"] == "E"

    def test_credibility_f_city_mismatch(self):
        """F: city from address != city from code"""
        df = self._make_df(
            [
                {
                    "路": "中山路",
                    "號": "42號",
                    "縣市別(address)": "臺北市",
                    "縣市別(citycode)": "新北市",
                }
            ]
        )
        result = addrss_data_qualify(df)
        assert result.loc[0, "可信度"] == "F"

    def test_credibility_g(self):
        """G: 有路有地域"""
        df = self._make_df([{"路": "中山路", "地域": "某地域", "號": "42號"}])
        result = addrss_data_qualify(df)
        assert result.loc[0, "可信度"] == "G"

    def test_credibility_h(self):
        """H: 縣市別 or 第三級行政區 is NaN (garbled data)"""
        df = self._make_df([{"縣市別": None, "第三級行政區": None, "路": "中山路", "號": "42號"}])
        result = addrss_data_qualify(df)
        assert result.loc[0, "可信度"] == "H"

    def test_credibility_i(self):
        """I: 無號"""
        df = self._make_df([{"路": "中山路"}])
        result = addrss_data_qualify(df)
        assert result.loc[0, "可信度"] == "I"

    def test_multiple_rows(self):
        """Test multiple rows get different credibility scores."""
        df = self._make_df(
            [
                {"路": "中山路", "巷": "10巷", "弄": "5弄", "號": "42號"},  # A
                {"路": "中山路"},  # I (no 號)
            ]
        )
        result = addrss_data_qualify(df)
        assert result.loc[0, "可信度"] == "A"
        assert result.loc[1, "可信度"] == "I"
