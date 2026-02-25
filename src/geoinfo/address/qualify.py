"""Data qualification and address combination functions."""

import pandas as pd


def addrss_data_qualify(df):

    df["可信度"] = ""

    # 可信度D：無路有地域
    criteria_D = (df["路"].isnull()) & (df["地域"].notnull())
    df.loc[criteria_D, "可信度"] = "D"

    # 可信度E：有特殊字元 or 字數6以上 的'路'/'地域' or 字數2以下的"路"(包含路/街)
    criteria_E = (
        (df["路"].str.len() >= 6)
        | ((df["路"].str.len() <= 2) & (df["路"].notnull()))
        | (df["地域"].str.len() >= 6)
        | ((df["地域"].str.len() <= 1) & (df["地域"].notnull()))
        | (df["特殊字"] == 1)
    )
    df.loc[criteria_E, "可信度"] = "E"

    # 可信度F：若縣市別(address)/縣市別(citycode)不為空值, 縣市別(address) != 縣市別(citycode)
    criteria_F = (
        (df["縣市別(address)"].notnull())
        & (df["縣市別(citycode)"].notnull())
        & (df["縣市別(address)"] != df["縣市別(citycode)"])
    ) | (
        (df["第三級行政區(address)"].notnull())
        & (df["第三級行政區(towncode)"].notnull())
        & (df["第三級行政區(address)"] != df["第三級行政區(towncode)"])
    )
    df.loc[criteria_F, "可信度"] = "F"

    # 可信度G：有路有地域 (從縣市合併路/地域 ...號)
    criteria_G = (df["路"].notnull()) & (df["地域"].notnull())
    df.loc[criteria_G, "可信度"] = "G"

    # 可信度I：無號 (從縣市合併到路段)
    criteria_I = df["號"].isnull()
    df.loc[criteria_I, "可信度"] = "I"

    # 可信度A：有路無地域有巷有弄有號 且不為D/E/F/G/I
    criteria_A = (
        (df["路"].notnull())
        & (df["地域"].isnull())
        & (df["巷"].notnull())
        & (df["弄"].notnull())
        & (df["號"].notnull())
        & ~(df["可信度"].isin(["D", "E", "F", "G", "I"]))
    )
    df.loc[criteria_A, "可信度"] = "A"

    # 可信度B：有路無地域有巷無弄有號 且不為D/E/F/G/I
    criteria_B = (
        (df["路"].notnull())
        & (df["地域"].isnull())
        & (df["巷"].notnull())
        & (df["弄"].isnull())
        & (df["號"].notnull())
        & ~(df["可信度"].isin(["D", "E", "F", "G", "I"]))
    )
    df.loc[criteria_B, "可信度"] = "B"

    # 可信度C：有路無地域無巷無弄有號 且不為D/E/F/G/I
    criteria_C = (
        (df["路"].notnull())
        & (df["地域"].isnull())
        & (df["巷"].isnull())
        & (df["弄"].isnull())
        & (df["號"].notnull())
        & ~(df["可信度"].isin(["D", "E", "F", "G", "I"]))
    )
    df.loc[criteria_C, "可信度"] = "C"

    # 可信度H：縣市別 or 第三級行政區為亂碼
    criteria_H = (
        (df["縣市別"] != df["縣市別"]) | (df["第三級行政區"] != df["第三級行政區"])
    ) & ~(df["可信度"].isin(["I"]))
    df.loc[criteria_H, "可信度"] = "H"

    return df


def combine_address(row):
    res = ""
    parts = [
        row["縣市別"] if pd.notna(row["縣市別"]) else "",
        row["第三級行政區"] if pd.notna(row["第三級行政區"]) else "",
        row["路"] if pd.notna(row["路"]) else "",
        row["地域"] if pd.notna(row["地域"]) else "",
        row["段"] if pd.notna(row["段"]) else "",
    ]
    res = "".join(parts)
    if pd.notna(row["巷"]):
        res += row["巷"]
        if pd.notna(row["之(巷)"]):
            res = res[:-1] + row["之(巷)"] + res[-1]
    if pd.notna(row["弄"]):
        res += row["弄"]
        if pd.notna(row["之(弄)"]):
            res = res[:-1] + row["之(弄)"] + res[-1]
    if pd.notna(row["號"]):
        res += row["號"]
        if pd.notna(row["之(號)"]):
            res = res[:-1] + row["之(號)"] + res[-1]

    return res
