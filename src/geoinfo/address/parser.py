"""Core address parsing functions for breaking down Taiwanese addresses into components."""

import re

import pandas as pd
import cn2an

from geoinfo.utils.text import (
    to_half_width,
    remove_prefix,
    get_num_from_str,
)
from geoinfo.constants import (
    CITY_TRANSFORM,
    TOWN_TRANSFORM,
    DIRECT_MUNICIPALITIES,
    SPECIAL_CHARS,
    CHAR_REPLACE_MAP,
)


# 多個字元尋找在字串中的位置(以最後字元為主)
# ex1:
# input: "這是一段測試文字，測試是否有效" ["一","測","字"]
# output:[2, 4, 7, 9]
# ex2:
# input: "這是一段測試文字，測試是否有效" ["一段測","測","字"]
# output:[4, 7, 9]
def find_chars_in_str(input_str: str, patterns: list) -> list:
    indexes = []
    for pattern in patterns:
        matches = re.finditer(re.escape(pattern), input_str)
        for match in matches:
            indexes.append(match.end() - 1)
    return sorted(list(set(indexes)))


# 尋找符合樣本(patterns)字串，並回傳input_str的開頭到樣本中的字串
# ex:
# input: input_str = 弘道街41號2樓 patterns = ["道","街","號","樓"]
# return 弘道街 (搜尋的index取最小，若最小後面馬上連接另一個pattern，則取第二小的pattern)
def find_pattern(input_str: str, patterns: list) -> str:
    input_str_patterns_index_list = find_chars_in_str(input_str, patterns)
    if input_str_patterns_index_list:
        ind = min(input_str_patterns_index_list)
        while (ind + 1) in input_str_patterns_index_list:
            ind += 1
        output = input_str[: ind + 1]
        return output
    else:
        return ""


def convert_address(
    rowdata: pd.Series, town_code_shp, addressColumnName: str
) -> pd.Series:
    '''取得該資料列的 "縣市別" "縣市別(citycode)" "縣市別(address)"  "第三級行政區" "第三級行政區(towncode)" "第三級行政區(address)" "村里" "路" "地域" "鄰" "段" "衖" "之(巷)" "之(弄)" "之(號)" "之(樓)" "巷", "弄", "號", "樓" "特殊字"'''
    rowdata["excess"] = ""
    city_tansform = CITY_TRANSFORM
    town_tansform = TOWN_TRANSFORM

    address: str = rowdata[addressColumnName]  # 取得 address_df 的 address value
    address = to_half_width(address)  # 將address轉為half_width
    town_code = (
        rowdata["city_district_code_merge"]
        if "city_district_code_merge" in rowdata
        else ""
    )
    # 處理空值
    if address == "" and town_code == "":
        return rowdata

    # 去除()內的值
    rowdata["excess"] = "".join(re.findall(r"\([^)]*\)", address))
    address = re.sub(r"\([^)]*\)", "", address)
    address = re.sub(r"\s+", "", address)

    # 剔除["；",";","，",","," "]
    address = re.sub(r"(?:；|;|，|,)", "", address)
    # if " " in address:
    #     address = address[: address.find(" ")]

    # 將特定字母修正

    address = re.sub(
        r"((?:[a-zA-Z0-9]+|[a-zA-Z零一二三四五六七八九十百千萬]+))粼", r"\1鄰", address
    )
    address = re.sub(
        r"((?:[a-zA-Z0-9]+|[a-zA-Z零一二三四五六七八九十百千萬]+))[Ff]",
        r"\1樓",
        address,
    )
    replace_table = str.maketrans(CHAR_REPLACE_MAP)

    # Extract unwanted characters at once and add them to excess
    unwanted_chars = re.findall(r"[()\\「\\」\\、\\*\\/]", address)
    if unwanted_chars:
        rowdata["excess"] += "".join(unwanted_chars)

    # Extract numbers after "、" and add them to excess
    # 臺中市潭子區豐興路一段66、88號
    num_excess = re.findall(r"、(\d+)", address)
    rowdata["excess"] += "".join(num_excess)
    address = re.sub(r"、(\d+)", "、", address)

    address = (
        address.replace("後 路", "後廍路")
        .replace("光 路", "光峰路")
        .translate(replace_table)
    )
    address_init = address
    address = address.replace(" ", "")
    # 無法確定為"臺北市"或"新北市"
    # # 臺(台)北更改為臺北市
    # address1 = re.sub(r"[臺台]北(?!市|縣)", "臺北市", address)
    # 分析縣市
    (
        city,
        town,
        village,
        road_address,
        area,
    ) = (
        "",
        "",
        "",
        "",
        "",
    )
    # 找出特殊字
    rowdata["特殊字"] = 1 if len(find_chars_in_str(address, SPECIAL_CHARS)) else 0

    # 處理縣市
    # 從VILLAGE_NLSC_1120825.COUNTYNAME
    city_from_town_code_shp = ""
    if town_code != "":
        filtered_data = town_code_shp[town_code_shp["COUNTYCODE"] == town_code[:5]]
        if not filtered_data.empty:
            city_from_town_code_shp = filtered_data.iloc[0]["COUNTYNAME"]
            city_from_town_code_shp = city_tansform.get(
                city_from_town_code_shp, city_from_town_code_shp
            )

    # 查找 Address 縣市
    city_init = ""  # Address原始縣市別
    city_address = ""  # 處理後Address原始縣市別
    citys_form_from_town_code_shp: list = town_code_shp[
        "COUNTYNAME"
    ].unique()  # 存shpfile抓取所有的COUNTYNAME
    city_end = (
        address.find("縣")
        if address.find("縣") == 2 or address.find("縣") == 1
        else (
            address.find("市")
            if address.find("市") == 2 or address.find("市") == 1
            else -1
        )
    )
    if city_end != -1:
        city_init: str = address[: city_end + 1]
        city_address = city_init.replace("台", "臺")
        # 縣市後兩位出現了["路","巷","里","街"]，則不採用為Address的縣市別。
        # 新市村29鄰復興路62巷36號
        # 新市一路一段58號四樓
        if len(city_address) == 2 and re.search(
            r"^"
            + re.escape(f"{city_init}")
            + r"(?:[a-zA-Z0-9]+|[a-zA-Z零一二三四五六七八九十百千萬]+)?[路巷里街村]",
            address,
        ):
            city_address = ""
        city_address = city_address.replace(get_num_from_str(city_init), "")
        city_address = city_tansform.get(
            city_address, city_address
        )  # 將過去的地址轉換為現在
        # 應出現在VILLAGE_NLSC_1120825.csv -> 從address中刪除city_init
        if city_address in citys_form_from_town_code_shp:
            address = address.replace(city_init, "")
        else:
            city_address = ""

    # 確認"縣市別"該取決於citycode(city_from_town_code_shp)或是address(city_address)
    if city_address:
        city = city_address
    elif city_from_town_code_shp:
        city = city_from_town_code_shp
    else:
        city = ""

    rowdata["縣市別"] = city
    rowdata["縣市別(citycode)"] = city_from_town_code_shp
    rowdata["縣市別(address)"] = city_address

    # 處理第三級行政區
    # 從VILLAGE_NLSC_1120825.csv尋找TownName
    town_from_town_code_shp = ""
    filtered_data = town_code_shp[town_code_shp["TOWNCODE"] == town_code]
    if not filtered_data.empty:
        if not city_address or (
            city_address and city_address == city_from_town_code_shp
        ):
            town_from_town_code_shp = filtered_data.iloc[0]["TOWNNAME"]
            town_from_town_code_shp = town_tansform.get(
                town_from_town_code_shp, town_from_town_code_shp
            )
            if city in DIRECT_MUNICIPALITIES and town_from_town_code_shp:
                town_from_town_code_shp = town_from_town_code_shp[
                    0:-1
                ] + town_from_town_code_shp[-1].replace("鄉", "區").replace(
                    "鎮", "區"
                ).replace("市", "區")
    # 從Address中尋找TownName
    town_init = ""
    town_address = ""
    towns_form_from_town_code_shp: list = town_code_shp[
        (town_code_shp["COUNTYNAME"] == rowdata["縣市別"]) | (rowdata["縣市別"] == "")
    ]["TOWNNAME"].unique()  # 存shpfile抓取所有的TOWNNAME
    patterns = ["市區", "鎮區", "鎮市", "鄉", "鎮", "區", "市"]
    town_init = find_pattern(address, patterns)
    # 防止"三民區市中一路"出現問題
    if (
        len(town_init) == 4
        and not len(find_chars_in_str(town_init, ["市區", "鎮區"]))
        and (town_init[-1] in patterns and town_init[-2] in patterns)
    ):
        town_init = town_init[:-1]
    town_address = town_init.replace(get_num_from_str(town_init), "")
    town_address = town_address.replace("台", "臺")
    town_address = town_tansform.get(
        town_address, town_address
    )  # 將過去的地址轉換為現在
    if city in DIRECT_MUNICIPALITIES and town_address:
        town_address = town_address[:-1] + (
            town_address[-1].replace("鄉", "區").replace("鎮", "區").replace("市", "區")
        )
    if town_address in towns_form_from_town_code_shp:
        address = remove_prefix(address, town_init)
    else:
        town_address = ""

    # 確認"縣市別"該取決於citycode(city_from_town_code_shp)或是address(city_address)
    if town_address:
        town = town_address
    elif town_from_town_code_shp:
        town = town_from_town_code_shp
    else:
        town = ""
    rowdata["第三級行政區"] = town
    rowdata["第三級行政區(towncode)"] = town_from_town_code_shp
    rowdata["第三級行政區(address)"] = town_address
    # 處理村里
    patterns = ["村", "里"]
    village_form_from_town_code_shp: list = town_code_shp[
        ((town_code_shp["COUNTYNAME"] == rowdata["縣市別"]) | (rowdata["縣市別"] == ""))
        & (
            (town_code_shp["TOWNNAME"] == rowdata["第三級行政區"])
            | (rowdata["第三級行政區"] == "")
        )
    ]["VILLNAME"].unique()  # 存shpfile抓取所有的TOWNNAME
    village_init = find_pattern(address, patterns)
    village = village_init.replace(get_num_from_str(village_init), "")
    village = (
        ""
        if village != "" and ("{}路".format(village) in address)
        else ("{}里".format(village) if "{}里".format(village) in address else village)
    )
    village = (
        "{}里".format(village)
        if village != "" and ("{}里".format(village) in address)
        else village
    )

    if len(village) >= 2:
        if village in village_form_from_town_code_shp:
            address = remove_prefix(address, village_init)
        # ["臺北市", "新北市", "桃園市", "臺中市", "高雄市"] 村-> 里&里-> 村(大約修正村與里)
        elif (
            village[0:-1] + village[-1].replace("村", "里")
            in village_form_from_town_code_shp
        ):
            address = remove_prefix(address, village_init)
            village = village[:-1] + village[-1].replace("村", "里")
        elif (
            village[0:-1] + village[-1].replace("里", "村")
            in village_form_from_town_code_shp
        ):
            address = remove_prefix(address, village_init)
            village = village[:-1] + village[-1].replace("里", "村")
        else:
            address = remove_prefix(address, village_init)
    else:
        village = ""
    rowdata["村里"] = village

    # 處理 鄰、段、衖
    for column in ["鄰", "段", "衖"]:
        value = ""
        if column in address:
            pattern = (
                r"((?:[a-zA-Z0-9]+|[a-zA-Z零一二三四五六七八九十百千萬]+)){}".format(
                    column
                )
            )
            match = re.search(pattern, address)
            if match:
                value = match.group(0)
                # 溫泉2鄰溫泉路89巷1號之18
                if column == "鄰":
                    split_address = address.split(value)
                    if len(split_address) >= 2:
                        # 里7鄰鯉南路39之77號
                        if len(split_address[0]) == 1:
                            rowdata["excess"] += split_address[0]
                        elif not rowdata["村里"]:
                            rowdata["村里"] = split_address[0]
                        else:
                            rowdata["excess"] += split_address[0]
                        address = "".join(split_address[1:])
                else:
                    address = address.replace(match.group(0), "")
                while value and value[0] == "0":
                    value = value[1:]
        if column == "段":
            rowdata[column] = cn2an.transform(value, "an2cn")
            continue
        rowdata[column] = cn2an.transform(value, "cn2an")

    # 處理"鄰"所分開的"村里"
    if rowdata["村里"]:
        village = rowdata["村里"]
        # 南興李27鄰建業路77號 -> 南興里
        pattern = r"[李理裡禮裏]$"
        village_match = re.search(pattern, village)
        if village_match:
            village = village[:-1] + "里"

        if village in village_form_from_town_code_shp:
            rowdata["村里"] = village
        # ["臺北市", "新北市", "桃園市", "臺中市", "高雄市"] 村-> 里&里-> 村(大約修正村與里)
        elif (
            village[0:-1] + village[-1].replace("村", "里")
            in village_form_from_town_code_shp
        ):
            rowdata["村里"] = village[:-1] + village[-1].replace("村", "里")
        elif (
            village[0:-1] + village[-1].replace("里", "村")
            in village_form_from_town_code_shp
        ):
            rowdata["村里"] = village[:-1] + village[-1].replace("里", "村")
        # 溫泉2鄰溫泉路89巷1號之18 -> 溫泉村
        elif f"{village}里" in village_form_from_town_code_shp:
            rowdata["村里"] = f"{village}里"
        elif f"{village}村" in village_form_from_town_code_shp:
            rowdata["村里"] = f"{village}村"
        else:
            rowdata["村里"] = village

    # 處理路
    patterns = ["路", "街", "道", "村路", "大道"]
    road_init = find_pattern(address, patterns)
    road_address = road_init
    # 解決街中有數字問題
    # 花蓮縣花蓮市國治里1新港街42之1號7樓 -> 1新港街-> 鄰:1鄰 路:新港街

    pattern = r"^[0-9之]+"
    match = re.search(pattern, road_init)
    if match:
        # 南安里4鄰68-1路
        if len(match.group(0)) == len(road_init) - 1:
            rowdata["excess"] += road_init
            road_address = ""
        elif rowdata["鄰"]:
            rowdata["excess"] += road_init[: match.end()]
        else:
            rowdata["鄰"] = f"{road_init[: match.end()]}鄰"
        road_address = road_init[match.end() :]
    road_address = cn2an.transform(road_address, "an2cn")

    if len(road_address) == 1:
        road_address = ""
    # 竹村五路19號101室  路: 五路-> 竹村五路
    elif len(road_address) == 2 and not rowdata["鄰"]:
        road_address = f"{rowdata['村里']}{road_address}"
        rowdata["村里"] = ""
        address = remove_prefix(address, road_init)
    elif re.search(re.escape(f"{road_address}[巷]"), address):
        road_address = ""
    else:
        address = remove_prefix(address, road_init)
    rowdata["路"] = road_address

    # 處理地域
    rowdata["地域"] = ""
    pattern = r"(?<![a-zA-Z0-9]|[a-zA-Z零一二三四五六七八九十百千萬])[巷段]"
    match = re.search(pattern, address)
    if match and len(match.group(0)) == 1:
        area = address[: match.start() + 1]

        rowdata[area[-1]] = area
        address = remove_prefix(address, area)
    else:
        pattern = (
            r"(.*?)(?:[a-zA-Z0-9]+|[a-zA-Z零一二三四五六七八九十百千萬]+)[之巷弄號樓]"
        )
        match = re.search(pattern, address)
        if match:
            area = match.group(1)
            if len(area) <= 1:
                area = ""
            if area not in address_init:
                for i in range(1, len(area)):
                    if area[0:i] not in address_init:
                        area = area[i - 1 :]
                        break
            # 在地域中排除錯字 13向-> 13巷
            pattern = r"([a-zA-Z0-9]+)[向像象相項]"
            area_match = re.search(pattern, area)
            if area_match:
                address = address.replace(
                    area_match.group(0), f"{area_match.group(1)}巷"
                )
                area = ""
            # 13林-> 13鄰
            pattern = r"([a-zA-Z0-9]+)[林霖淋麟磷臨]"
            area_match = re.search(pattern, area)
            if area_match:
                address = address.replace(
                    area_match.group(0), f"{area_match.group(1)}鄰"
                )
                area = ""
            # 13浩-> 13號
            pattern = r"([a-zA-Z0-9]+)[浩耗皓昊賀好]"
            area_match = re.search(pattern, area)
            if area_match:
                address = address.replace(
                    area_match.group(0), f"{area_match.group(1)}號"
                )
                area = ""
            # 13斷-> 13段
            pattern = r"([a-zA-Z0-9]+)[斷]"
            area_match = re.search(pattern, area)
            if area_match:
                address = address.replace(area_match.group(0), "")
                rowdata["段"] = cn2an.transform(f"{area_match.group(1)}段", "an2cn")
                area = ""
            rowdata["地域"] = area
            address = address.replace(area, "")

    # 處理巷、弄、號、樓
    for column in ["巷", "弄", "號", "樓"]:
        of_value, value = "", ""

        # O巷(弄、號、樓))之O
        pattern = r"((?:[a-zA-Z0-9]+|[a-zA-Z零一二三四五六七八九十百千萬]+){}之(?:[a-zA-Z0-9]+|[a-zA-Z零一二三四五六七八九十百千萬]+))".format(
            column
        )
        match = re.search(pattern, address)
        if match:
            # 之 of 巷(弄、號、樓)
            pattern = r"(之(?:[a-zA-Z0-9]+|[a-zA-Z零一二三四五六七八九十百千萬]+))"
            of_value = re.search(pattern, match.group(0)).group(0)

            # 巷(弄、號、樓)
            pattern = (
                r"((?:[a-zA-Z0-9]+|[a-zA-Z零一二三四五六七八九十百千萬]+)){}".format(
                    column
                )
            )
            value = re.search(pattern, match.group(0)).group(0)
            address = address.replace(match.group(0), "")
        # O巷(弄、號、樓) O之O巷(弄、號、樓) O之O之O巷(弄、號、樓)...
        else:
            pattern = r"((?:(?:[a-zA-Z0-9]+|[a-zA-Z零一二三四五六七八九十百千萬]+)之)*(?:[a-zA-Z0-9]+|[a-zA-Z零一二三四五六七八九十百千萬]+){})".format(
                column
            )
            match = re.search(pattern, address)
            if match:
                # 之 of 巷(弄、號、樓)
                pattern = r"之(?:[a-zA-Z0-9]+|[a-zA-Z零一二三四五六七八九十百千萬]+)(?:之(?:[a-zA-Z0-9]+|[a-zA-Z零一二三四五六七八九十百千萬]+))*"
                of_match = re.search(pattern, match.group(0))
                if of_match:
                    of_value = of_match.group(0)
                # 巷(弄、號、樓)
                pattern = r"((?:[a-zA-Z0-9]+|[a-zA-Z零一二三四五六七八九十百千萬]+))[之{}]".format(
                    column
                )
                value_match = re.search(pattern, match.group(0))
                if value_match:
                    value = value_match.group(1) + column
                address = address.replace(match.group(0), "")
        pattern = r"{}{}".format(of_value, value)
        match = re.search(pattern, address)
        if (
            f"之({column})" not in rowdata
            or rowdata[f"之({column})"] == ""
            or rowdata[f"之({column})"] is None
        ):
            rowdata[f"之({column})"] = cn2an.transform(of_value, "cn2an")
        if column not in rowdata or rowdata[column] == "" or rowdata[column] is None:
            rowdata[column] = cn2an.transform(value, "cn2an")

    rowdata["excess"] += address

    ####################################################################
    # 後處理
    # 若找不到 "第三級行政區" 從 "村里" 回推，需同時符合 "縣市" 與 "村里"
    if (
        rowdata["縣市別"] != ""
        and rowdata["第三級行政區"] == ""
        and rowdata["村里"] != ""
    ):
        filtered_data = town_code_shp[
            (town_code_shp["VILLNAME"] == rowdata["村里"])
            & (
                (town_code_shp["COUNTYCODE"] == town_code[:5])
                | (town_code_shp["COUNTYNAME"] == rowdata["縣市別"])
            )
        ]
        if not filtered_data.empty:
            rowdata["第三級行政區"] = filtered_data.iloc[0]["VILLNAME"]

    # 若找不到 "第三級行政區" 與 "縣市別" 從 "村里" 回推，需符合 "村里" 且 只有一筆該 "村里" 的資料
    if (
        rowdata["縣市別"] == ""
        and rowdata["第三級行政區"] == ""
        and rowdata["村里"] != ""
    ):
        filtered_data = town_code_shp[town_code_shp["VILLNAME"] == rowdata["村里"]]
        if not filtered_data.empty and len(filtered_data) == 1:
            rowdata["縣市別"] = filtered_data.iloc[0]["COUNTYNAME"]
            rowdata["第三級行政區"] = filtered_data.iloc[0]["VILLNAME"]

    # 若 "地域" 中最後一個字為 "路" -> 改加入在 "路"欄
    if rowdata["地域"] != "" and (
        rowdata["地域"][-1] == "路" or rowdata["地域"][-1] == "街"
    ):
        rowdata["路"] = rowdata["路"] + rowdata["地域"]
        rowdata["地域"] = ""

    # 筆誤修正:
    # 13謝-> 13巷
    pattern = r"([a-zA-Z0-9]+)[謝莌]"

    match = re.search(pattern, rowdata["地域"])
    if match:
        if rowdata["巷"] == "":
            rowdata["巷"] = cn2an.transform(f"{match.group(1)}巷", "cn2an")
            rowdata["地域"] = ""

    # 13落-> 13號
    pattern = r"([a-zA-Z0-9]+)[落行]"
    match = re.search(pattern, rowdata["地域"])
    if match:
        if rowdata["號"] == "":
            rowdata["號"] = cn2an.transform(f"{match.group(1)}號", "cn2an")
            rowdata["地域"] = ""

    # 282南 -> 282南十八(加到"巷"前)
    pattern = r"([a-zA-Z0-9]+)[南北]"
    match = re.search(pattern, rowdata["地域"])
    if match:
        if rowdata["弄"] == "":
            rowdata["弄"] = f"{match.group(1)}{rowdata['巷']}"
            rowdata["地域"] = ""

    # 13接-> 13街
    pattern = r"([a-zA-Z0-9]+)[接間]"
    match = re.search(pattern, rowdata["地域"])
    if match:
        if rowdata["路"] == "":
            rowdata["路"] = f"{match.group(1)}街"
            rowdata["地域"] = ""

    # 特殊案例
    # 東安里8鄰本街鯉魚一巷18-1號
    if len(rowdata["路"]) == 2 and rowdata["地域"]:
        rowdata["地域"] = f"{rowdata['路']}{rowdata['地域']}"
        rowdata["路"] = ""
    # 區敦化北路244巷31號3樓
    if len(rowdata["路"]) == 5 and rowdata["路"][0] == "區":
        rowdata["excess"] = f"{rowdata['路'][0]}{rowdata['excess']}"
        rowdata["路"] = rowdata["路"][1:]

    while rowdata["路"] != "" and rowdata["路"][0] == "鄰":
        rowdata["路"] = rowdata["路"][1:]
    while rowdata["地域"] != "" and rowdata["地域"][0] == "鄰":
        rowdata["地域"] = rowdata["地域"][1:]

    if (
        (
            rowdata["路"]
            and rowdata["路"] not in address_init
            and cn2an.transform(rowdata["路"], "cn2an") not in address_init
            and cn2an.transform(rowdata["路"], "an2cn") not in address_init
        )
        or rowdata["地域"] not in address_init
        or (
            rowdata["號"]
            and cn2an.transform(rowdata["號"], "cn2an") not in address_init
            and cn2an.transform(rowdata["號"], "an2cn") not in address_init
            and (
                rowdata["號"]
                and rowdata["之(號)"]
                and not cn2an.transform(
                    f"{rowdata['號'][:-1]}{rowdata['之(號)']}{rowdata['號'][-1]}",
                    "an2cn",
                )
                and not cn2an.transform(
                    f"{rowdata['號'][:-1]}{rowdata['之(號)']}{rowdata['號'][-1]}",
                    "cn2an",
                )
            )
        )
    ):
        rowdata["特殊字"] = 1
    return rowdata


def apply_async_wrapper(_input, town_code_dict, addressColumnName):
    return _input.apply(
        convert_address,
        axis=1,
        args=(
            town_code_dict,
            addressColumnName,
        ),
    )
