"""Text utility functions for character width conversion, prefix removal, and number extraction."""

import re


def to_half_width(text) -> str:
    """Convert full-width characters to half-width."""
    if not text:
        return ""
    return "".join(
        chr(0x0021 + (ord(char) - 0xFF01)) if "\uff01" <= char <= "\uff5e" else char
        for char in text
    )


def to_full_width(text) -> str:
    """Convert half-width characters to full-width."""
    if not text:
        return ""
    return "".join(
        chr(0xFF01 + (ord(char) - 0x0021)) if "\u0021" <= char <= "\u007e" else char
        for char in text
    )


def remove_prefix(original_str, prefix) -> str:
    """去掉前符合字元"""
    if original_str.startswith(prefix):
        return original_str[len(prefix) :]
    else:
        return original_str


def get_num_from_str(input_str):
    """從字串中提取數字"""
    result = re.sub(r"[^0-9]", "", input_str)
    return result
