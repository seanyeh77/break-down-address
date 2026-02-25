# 地址分解與地理編碼系統

一個用於解析、標準化和地理編碼台灣地址。此工具自動化地址分解流程，包括地址成分提取、驗證、村里代碼查詢和坐標轉換，內置多進程支持和 Google Maps API 集成。

## 概述

地址分解與地理編碼系統解決了處理、規範化和定位台灣地址的複雜問題。能夠建地理信息系統、進行數據清理、分析或空間研究，此工具都提供了可靠的批量地址處理能力。

主要功能：
- 將台灣地址分解為縣市、鄉鎮、村里、街道、段、巷、弄、號等組成部分
- 批量標準化地址格式和縣市代碼
- 自動驗證並加入村里代碼信息
- 使用 Google Maps API 轉換地址為經緯度坐標
- 支持多進程並行處理大規模數據集
- 空間分析與地理信息查詢

## 功能特性

- **地址解析**: 精確拆分台灣地址為結構化成分
- **標準化処理**: 自動處理各種地址格式和縣市代碼轉換
- **地理編碼**: 直接將地址轉換為經緯度坐標
- **高性能**: 利用多進程實現並行數據處理
- **數據驗證**: 內置地址合法性檢查和村里代碼驗證
- **空間分析**: 基於 Shapefile 進行地理邊界查詢和位置驗證

## 快速開始

### 前置要求

在開始前，請確保您有：
- [uv](https://docs.astral.sh/uv/getting-started/installation/) 已安裝。
- Google Maps API 密鑰（用於地理編碼功能）

### 安裝

1. **導航到項目目錄：**
```bash
git clone git@gitlab.seanyeh77.com:seanyeh77/break-down-address.git
cd break_down_address
```

2. **安裝所有依賴項：**
```bash
uv sync
```

此命令將自動創建虛擬環境並安裝所有必需的依賴項。

3. **配置 Google Maps API（可選）：**

創建 `.env` 文件並添加您的 Google Maps API 密鑰：
```
GOOGLE_MAPS_API_KEY=your_api_key_here
```

### 快速開始

運行地址處理管道：

```bash
uv run python -m geoinfo
```

這將：
1. 讀取 `input/` 目錄中的 CSV 文件
2. 執行地址標準化、驗證和地理編碼
3. 將處理結果寫回輸出 CSV 文件
4. 在控制台顯示處理進度

## 架構設計

### 核心模塊

#### `address/` - 地址處理模塊
- **`parser.py`**: 地址解析引擎
  - `find_chars_in_str()`: 在字符串中查找模式位置
  - `find_pattern()`: 查找並提取地址模式段
  - `break_address()`: 主地址解析函數，分解為各組成部分
  - `apply_async_wrapper()`: 多進程異步執行包裝器

- **`qualify.py`**: 地址驗證和合併
  - `addrss_data_qualify()`: 驗證地址數據完整性
  - `combine_address()`: 合併分解的地址組成部分

#### `geo/` - 地理信息模塊
- **`spatial.py`**: 空間分析功能
  - `get_village_Code_df()`: 從 Shapefile 加載村里代碼數據
  - 地理邊界查詢和位置驗證

#### `geocoding/` - 地理編碼模塊
- **`google_api.py`**: Google Maps 集成
  - `address_get_pos()`: 批量獲取地址經緯度
  - `process_chunk()`: 分批處理地址的異常處理

#### `utils/` - 工具函數
- **`text.py`**: 文本處理工具
  - 全半角字符轉換
  - 前綴移除和數字提取
  - 文本規範化函數

#### `pipeline.py` - 處理管道
- **`break_address_statardize()`**: 標準化縣市代碼和地址格式
- **`break_address_qualify()`**: 驗證和清理地址數據
- **`break_address_combine()`**: 合併地址成分
- **`break_address_get_lonlat()`**: 地理編碼轉換

## 使用方式

### 基本地址處理

1. **準備輸入數據：**

創建或轉移 CSV 文件到 `input/` 目錄，確保包含地址列。

例如，`input/addresses.csv`:
```csv
ID,場所地址
1,台北市中山區松江路87號4樓
2,高雄市鼓山區自強街10號
3,台中市西屯區文心路段123號
```

2. **啟用所需的處理步驟：**

編輯 `src/geoinfo/__main__.py` 中的標誌：
```python
STATARDIZE = True   # 標準化地址
QUALIFY = True      # 驗證地址
COMBINE = True      # 合併成分
GET_LONLAT = True   # 獲取坐標
```

3. **運行管道：**
```bash
uv run python -m geoinfo
```

### 編程使用

在您自己的 Python 腳本中導入和使用：

```python
import pandas as pd
from geoinfo.pipeline import (
    break_address_statardize,
    break_address_qualify,
    break_address_get_lonlat,
)

# 加載地址數據
df = pd.read_csv("your_addresses.csv")

# 標準化地址
df_standardized = break_address_statardize(df, "address_column_name")

# 驗證地址
df_qualified = break_address_qualify(df_standardized)

# 地理編碼
df_geocoded = break_address_get_lonlat(df_qualified, "address_column_name")

# 保存結果
df_geocoded.to_csv("output.csv", index=False)
```

### 自定義配置

在 `src/geoinfo/constants.py` 中調整常數以滿足不同需求：

```python
# 地址列名稱
DEFAULT_ADDRESS_COLUMN = "場所地址"
DEFAULT_OUTPUT_ADDRESS_COLUMN = "標準地址"

# 地理編碼輸出列
GEOCODE_OUTPUT_COLUMNS = ["latitude", "longitude", "accuracy"]

# 多進程設置
MAX_POOL_SPLITS = 4  # 並行進程數

# 縣市代碼轉換
COUNTY_CODE_REPLACE = {
    "1000XX": "63000",  # 基隆市
    "2000XX": "65000",  # 新竹市
    # ... 更多映射
}
```

## 配置選項

主要配置常數位於 `src/geoinfo/constants.py`：

| 常數 | 說明 |
|------|------|
| `DEFAULT_ADDRESS_COLUMN` | 輸入 CSV 中的地址列名稱 |
| `DEFAULT_OUTPUT_ADDRESS_COLUMN` | 標準化後的地址輸出列名 |
| `GEOCODE_OUTPUT_COLUMNS` | 表示坐標的列名列表 |
| `MAX_POOL_SPLITS` | 多進程池的並行進程數 |
| `COUNTY_CODE_REPLACE` | 縣市代碼標準化映射表 |
| `CITY_TRANSFORM` | 城市名稱轉換映射 |
| `TOWN_TRANSFORM` | 鎮鄉名稱轉換映射 |
| `DIRECT_MUNICIPALITIES` | 直轄市列表 |

## 示例工作流

### 示例 1: 簡單地址解析

```python
from geoinfo.address.parser import break_address

# 解析單個地址
address = "台北市中山區松江路87號4樓"
result = break_address(address)

print(result)
# 輸出: {
#   'city': '台北市',
#   'district': '中山區', 
#   'street': '松江路',
#   'section': None,
#   'lane': None,
#   'alley': None,
#   'number': '87號4樓'
# }
```

### 示例 2: 批量地址處理

```python
import pandas as pd
from geoinfo.pipeline import break_address_statardize, break_address_get_lonlat

# 加載 CSV 文件
df = pd.read_csv("input_addresses.csv")

# 標準化
df = break_address_statardize(df)

# 地理編碼
df = break_address_get_lonlat(df, "場所地址")

# 保存結果
df.to_csv("geocoded_addresses.csv", index=False)
```

### 示例 3: 空間查詢

```python
from geoinfo.geo.spatial import get_village_Code_df
import geopandas as gpd

# 加載村里邊界 Shapefile
village_gdf = get_village_Code_df("data/village/Village_Sanhe.shp")

# 執行空間查詢
# 使用 geopandas 進行點-面空間聯接等操作
```

## 項目結構

```
break_down_address/
├── README.md                    # 項目文檔
├── pyproject.toml              # Python 依賴和項目元數據
├── pytest.ini                  # pytest 配置
├── uv.lock                     # 依賴鎖定文件
├── .env                        # 環境變量（包含 API 密鑰）
│
├── data/                       # 地理數據目錄
│   └── village/               # 村里邊界數據
│       ├── TW-07-301000100G-613995.xml
│       ├── VILLAGE_NLSC_1120825.*  (Shapefile 文件)
│       └── Village_Sanhe.*         (Shapefile 文件)
│
├── src/geoinfo/               # 主源代碼目錄
│   ├── __init__.py
│   ├── __main__.py            # 命令行入口
│   ├── pipeline.py            # 處理管道編排
│   ├── constants.py           # 常數和配置
│   │
│   ├── address/               # 地址處理模塊
│   │   ├── __init__.py
│   │   ├── parser.py          # 地址解析引擎
│   │   └── qualify.py         # 驗證和合併
│   │
│   ├── geo/                   # 地理信息模塊
│   │   ├── __init__.py
│   │   └── spatial.py         # 空間分析
│   │
│   ├── geocoding/             # 地理編碼模塊
│   │   ├── __init__.py
│   │   └── google_api.py      # Google Maps 集成
│   │
│   └── utils/                 # 工具函數
│       ├── __init__.py
│       └── text.py            # 文本處理工具
│
├── tests/                     # 測試目錄
│   ├── test_parser.py
│   ├── test_qualify.py
│   ├── test_spatial.py
│   ├── test_text.py
│   ├── test_pipeline.py
│   └── test_google_api.py
│
└── input/                     # 輸入目錄（存放 CSV 文件）
    └── *.csv                  # 待處理的地址文件
```

## 依賴項

### 依賴
- **`cn2an`** - 中文到阿拉伯數字轉換
- **`geopandas`** - 地理空間數據處理
- **`googlemaps`** - Google Maps API 客戶端
- **`pandas`** - 數據處理和分析
- **`dotenv`** - 環境變量管理

### 開發工具
- **`pytest`** - 單元測試框架
- **`pytest-cov`** - 測試覆蓋率報告
- **`mypy`** - 靜態類型檢查
- **`ruff`** - 代碼風格檢查和格式化

詳見 [pyproject.toml](pyproject.toml) 查看完整依賴列表。

## 開發指南

### 運行測試

```bash
# 運行所有測試
uv run pytest

# 運行特定測試文件
uv run pytest tests/test_parser.py

# 運行時顯示覆蓋率
uv run pytest --cov=src/geoinfo
```

### 代碼檢查和格式化

```bash
# 檢查代碼風格問題
uv run ruff check src/

# 自動修復問題
uv run ruff check --fix src/

# 格式化代碼
uv run ruff format src/

# 類型檢查
uv run mypy src/
```