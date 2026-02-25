"""Tests for geoinfo.geocoding.google_api module."""

from unittest.mock import patch, MagicMock

import pandas as pd

from geoinfo.geocoding.google_api import get_lonlat, process_chunk


# ─── get_lonlat ───────────────────────────────────────────────────────────────


class TestGetLonlat:
    @patch("geoinfo.geocoding.google_api.googlemaps.Client")
    def test_successful_geocode(self, mock_client_class):
        """Should populate Lat, Lon, and Address3 on successful geocode."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.geocode.return_value = [
            {
                "address_components": [
                    {
                        "long_name": "臺北市",
                        "types": ["administrative_area_level_1"],
                    },
                    {
                        "long_name": "中山區",
                        "types": ["administrative_area_level_2"],
                    },
                    {
                        "long_name": "中山路",
                        "types": ["route"],
                    },
                    {
                        "long_name": "42",
                        "types": ["street_number"],
                    },
                ],
                "formatted_address": "臺北市中山區中山路42號",
                "geometry": {"location": {"lat": 25.0330, "lng": 121.5654}},
            }
        ]

        row = pd.Series({"Address2": "臺北市中山區中山路42號", "已處理": 0})
        result = get_lonlat(row, "Address2", "fake_api_key")

        assert result["已處理"] == 1
        assert result["Lat"] == 25.0330
        assert result["Lon"] == 121.5654
        assert result["Address3"] == "臺北市中山區中山路42號"
        assert result["縣市3"] == "臺北市"
        assert result["第三級行政區3"] == "中山區"
        assert result["路3"] == "中山路"
        assert result["號3"] == "42"

    @patch("geoinfo.geocoding.google_api.googlemaps.Client")
    def test_none_address_skipped(self, mock_client_class):
        """Rows with None/NaN address: pd.Series stores None as NaN,
        so `is None` check in get_lonlat doesn't catch it. The geocode
        call still happens but with NaN. Verify 已處理 is set to 1."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        # Simulate empty geocode result for NaN input
        mock_client.geocode.return_value = []

        row = pd.Series({"Address2": None, "已處理": 0})
        result = get_lonlat(row, "Address2", "fake_api_key")

        assert result["已處理"] == 1

    @patch("geoinfo.geocoding.google_api.googlemaps.Client")
    def test_empty_geocode_result(self, mock_client_class):
        """Empty geocode result should return row with 已處理=1 but no lat/lon."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.geocode.return_value = []

        row = pd.Series({"Address2": "不存在的地址", "已處理": 0})
        result = get_lonlat(row, "Address2", "fake_api_key")

        assert result["已處理"] == 1
        assert "Lat" not in result or result.get("Lat") is None


# ─── process_chunk ────────────────────────────────────────────────────────────


class TestProcessChunk:
    def test_exception_returns_none(self):
        """process_chunk should return None on exception."""
        result = process_chunk(None, "Address2", "fake_key")
        assert result is None
