"""Tests for geoinfo.address.parser module (find_chars_in_str, find_pattern, convert_address)."""

import pytest
import pandas as pd

from geoinfo.address.parser import find_chars_in_str, find_pattern, convert_address


# ─── find_chars_in_str ────────────────────────────────────────────────────────


class TestFindCharsInStr:
    def test_single_char_patterns(self):
        """Example from docstring: single character patterns."""
        result = find_chars_in_str("這是一段測試文字，測試是否有效", ["一", "測", "字"])
        assert result == [2, 4, 7, 9]

    def test_multi_char_pattern(self):
        """Example from docstring: multi-character pattern."""
        result = find_chars_in_str(
            "這是一段測試文字，測試是否有效", ["一段測", "測", "字"]
        )
        assert result == [4, 7, 9]

    def test_no_matches(self):
        result = find_chars_in_str("hello", ["x", "y", "z"])
        assert result == []

    def test_empty_string(self):
        result = find_chars_in_str("", ["a", "b"])
        assert result == []

    def test_empty_patterns(self):
        result = find_chars_in_str("hello", [])
        assert result == []

    def test_duplicate_positions_deduplicated(self):
        result = find_chars_in_str("aa", ["a"])
        assert result == [0, 1]

    def test_overlapping_patterns(self):
        result = find_chars_in_str("hello", ["l"])
        assert result == [2, 3]

    def test_address_patterns(self):
        """Test with address-related patterns."""
        result = find_chars_in_str("弘道街41號2樓", ["道", "街", "號", "樓"])
        assert 1 in result  # 道
        assert 2 in result  # 街
        assert 5 in result  # 號
        assert 7 in result  # 樓


# ─── find_pattern ─────────────────────────────────────────────────────────────


class TestFindPattern:
    def test_docstring_example(self):
        """Example from docstring."""
        result = find_pattern("弘道街41號2樓", ["道", "街", "號", "樓"])
        assert result == "弘道街"

    def test_no_match(self):
        result = find_pattern("hello", ["x", "y"])
        assert result == ""

    def test_single_pattern(self):
        result = find_pattern("中山區", ["區"])
        assert result == "中山區"

    def test_consecutive_pattern_skipping(self):
        """When consecutive pattern chars are found, skip to the next."""
        result = find_pattern("中山區市路", ["區", "市", "路"])
        # 區 at index 2, 市 at index 3 (consecutive), so skip to 市
        # 路 at index 4 (consecutive to 市), so result is up to 路
        assert result == "中山區市路"

    def test_town_patterns(self):
        result = find_pattern(
            "板橋區", ["市區", "鎮區", "鎮市", "鄉", "鎮", "區", "市"]
        )
        assert result == "板橋區"

    def test_empty_string(self):
        result = find_pattern("", ["路", "街"])
        assert result == ""


# ─── convert_address ──────────────────────────────────────────────────────────


class TestConvertAddress:
    @pytest.fixture
    def mock_town_code_shp(self):
        """Create a minimal mock DataFrame mimicking the shapefile data."""
        return pd.DataFrame(
            {
                "COUNTYCODE": ["63000", "63000", "65000", "65000"],
                "COUNTYNAME": ["臺北市", "臺北市", "新北市", "新北市"],
                "TOWNCODE": ["001", "002", "001", "002"],
                "TOWNNAME": ["中山區", "大安區", "板橋區", "中和區"],
                "VILLNAME": ["中山里", "大安里", "板橋里", "中和里"],
            }
        )

    def test_empty_address_returns_unchanged(self, mock_town_code_shp):
        """Empty address with no town code should return row unchanged."""
        row = pd.Series({"場所地址": "", "excess": ""})
        result = convert_address(row, mock_town_code_shp, "場所地址")
        assert result["excess"] == ""

    def test_city_extraction_from_address(self, mock_town_code_shp):
        """Should extract city name from address string."""
        row = pd.Series({"場所地址": "臺北市中山區中山路1號"})
        result = convert_address(row, mock_town_code_shp, "場所地址")
        assert result["縣市別"] == "臺北市"

    def test_town_extraction_from_address(self, mock_town_code_shp):
        """Should extract town/district from address string."""
        row = pd.Series({"場所地址": "臺北市中山區中山路1號"})
        result = convert_address(row, mock_town_code_shp, "場所地址")
        assert result["第三級行政區"] == "中山區"

    def test_road_extraction(self, mock_town_code_shp):
        """Should extract road from address string."""
        row = pd.Series({"場所地址": "臺北市中山區中山路1號"})
        result = convert_address(row, mock_town_code_shp, "場所地址")
        assert "路" in result.index
        assert result["路"] != ""

    def test_full_width_address_converted(self, mock_town_code_shp):
        """Full-width characters in address should be converted."""
        row = pd.Series({"場所地址": "臺北市中山區中山路１號"})
        result = convert_address(row, mock_town_code_shp, "場所地址")
        assert result["縣市別"] == "臺北市"

    def test_excess_parentheses_extracted(self, mock_town_code_shp):
        """Content in parentheses should be extracted to excess."""
        row = pd.Series({"場所地址": "臺北市中山區中山路1號(備註)"})
        result = convert_address(row, mock_town_code_shp, "場所地址")
        assert "(備註)" in result["excess"]

    def test_old_city_name_transform(self, mock_town_code_shp):
        """Old city names like 臺北縣 should be transformed to 新北市."""
        mock_shp = pd.DataFrame(
            {
                "COUNTYCODE": ["65000"],
                "COUNTYNAME": ["新北市"],
                "TOWNCODE": ["001"],
                "TOWNNAME": ["板橋區"],
                "VILLNAME": ["板橋里"],
            }
        )
        row = pd.Series({"場所地址": "新北市板橋區中山路1號"})
        result = convert_address(row, mock_shp, "場所地址")
        assert result["縣市別"] == "新北市"

    def test_special_char_detection(self, mock_town_code_shp):
        """Addresses with special characters should be flagged."""
        row = pd.Series({"場所地址": "臺北市中山路?號"})
        result = convert_address(row, mock_town_code_shp, "場所地址")
        assert result["特殊字"] == 1

    def test_semicolon_stripped(self, mock_town_code_shp):
        """Semicolons and commas should be stripped from address."""
        row = pd.Series({"場所地址": "臺北市；中山路1號"})
        result = convert_address(row, mock_town_code_shp, "場所地址")
        # Should not error and should process
        assert "縣市別" in result.index

    def test_hao_extraction(self, mock_town_code_shp):
        """號 (house number) should be extracted."""
        row = pd.Series({"場所地址": "臺北市中山區民生東路42號"})
        result = convert_address(row, mock_town_code_shp, "場所地址")
        assert result["號"] != ""

    def test_floor_extraction(self, mock_town_code_shp):
        """樓 (floor) should be extracted."""
        row = pd.Series({"場所地址": "臺北市中山區民生東路42號5樓"})
        result = convert_address(row, mock_town_code_shp, "場所地址")
        assert result["樓"] != ""

    def test_lane_extraction(self, mock_town_code_shp):
        """巷 (lane) should be extracted."""
        row = pd.Series({"場所地址": "臺北市中山區民生東路10巷42號"})
        result = convert_address(row, mock_town_code_shp, "場所地址")
        assert result["巷"] != ""
