"""Tests for geoinfo.utils.text module."""

from geoinfo.utils.text import (
    to_half_width,
    to_full_width,
    remove_prefix,
    get_num_from_str,
)


# ─── to_half_width ────────────────────────────────────────────────────────────


class TestToHalfWidth:
    def test_full_width_letters(self):
        assert to_half_width("ＡＢＣ") == "ABC"

    def test_full_width_digits(self):
        assert to_half_width("１２３") == "123"

    def test_mixed_characters(self):
        assert to_half_width("Ａ測試Ｂ") == "A測試B"

    def test_already_half_width(self):
        assert to_half_width("ABC123") == "ABC123"

    def test_empty_string(self):
        assert to_half_width("") == ""

    def test_none(self):
        assert to_half_width(None) == ""

    def test_full_width_symbols(self):
        assert to_half_width("！＠＃") == "!@#"


# ─── to_full_width ────────────────────────────────────────────────────────────


class TestToFullWidth:
    def test_half_width_letters(self):
        assert to_full_width("ABC") == "ＡＢＣ"

    def test_half_width_digits(self):
        assert to_full_width("123") == "１２３"

    def test_mixed_characters(self):
        assert to_full_width("A測試B") == "Ａ測試Ｂ"

    def test_already_full_width(self):
        assert to_full_width("ＡＢＣ") == "ＡＢＣ"

    def test_empty_string(self):
        assert to_full_width("") == ""

    def test_none(self):
        assert to_full_width(None) == ""

    def test_roundtrip(self):
        """to_full_width(to_half_width(x)) should return original full-width."""
        original = "ＡＢＣ１２３"
        assert to_full_width(to_half_width(original)) == original

    def test_roundtrip_reverse(self):
        """to_half_width(to_full_width(x)) should return original half-width."""
        original = "ABC123"
        assert to_half_width(to_full_width(original)) == original


# ─── remove_prefix ────────────────────────────────────────────────────────────


class TestRemovePrefix:
    def test_matching_prefix(self):
        assert remove_prefix("hello_world", "hello") == "_world"

    def test_no_matching_prefix(self):
        assert remove_prefix("hello_world", "world") == "hello_world"

    def test_full_string_as_prefix(self):
        assert remove_prefix("hello", "hello") == ""

    def test_empty_prefix(self):
        assert remove_prefix("hello", "") == "hello"

    def test_empty_string(self):
        assert remove_prefix("", "hello") == ""

    def test_chinese_prefix(self):
        assert remove_prefix("臺北市中山區", "臺北市") == "中山區"

    def test_prefix_longer_than_string(self):
        assert remove_prefix("hi", "hello") == "hi"


# ─── get_num_from_str ─────────────────────────────────────────────────────────


class TestGetNumFromStr:
    def test_mixed_string(self):
        assert get_num_from_str("abc123def") == "123"

    def test_only_digits(self):
        assert get_num_from_str("456") == "456"

    def test_no_digits(self):
        assert get_num_from_str("abc") == ""

    def test_chinese_with_digits(self):
        assert get_num_from_str("臺北市3號") == "3"

    def test_multiple_digit_groups(self):
        assert get_num_from_str("1巷2弄3號") == "123"

    def test_empty_string(self):
        assert get_num_from_str("") == ""
