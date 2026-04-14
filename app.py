import pandas as pd
import streamlit as st

st.set_page_config(page_title="東京23区検索", layout="wide")
st.title("東京23区検索")

# =====================
# データ読み込み
# =====================
df = pd.read_excel("20260414_東京23区.xlsx")
df.columns = df.columns.astype(str).str.strip()

# Power Queryの本体列だけ
data_cols = [c for c in df.columns if c.startswith("Column")]
df = df[["Name"] + data_cols].copy()

# 見出し作成
headers = ["ファイル名"] + df.iloc[0, 1:].astype(str).str.strip().tolist()
df.columns = headers
df = df.iloc[1:].reset_index(drop=True)

df.columns = df.columns.astype(str).str.strip()

# 自治体
df["自治体"] = df["ファイル名"].astype(str).str.extract(r"^\d+_(.+?)_DM")

# =====================
# シート分割
# =====================
header_marker = df["NO"].astype(str).str.strip().eq("NO")
df["block_no"] = header_marker.groupby(df["ファイル名"]).cumsum()

df = df[~header_marker].copy()

# ダブり見出し削除
if "名称" in df.columns:
    df = df[df["名称"].astype(str).str.strip() != "名称"].copy()

# =====================
# 住所結合
# =====================
addr_cols = [c for c in df.columns if str(c).strip().startswith("住所")]
for c in addr_cols:
    df[c] = df[c].fillna("").astype(str).str.strip()

if addr_cols:
    df["住所"] = df[addr_cols].agg("".join, axis=1).str.strip()
else:
    df["住所"] = ""

# =====================
# 列特定
# =====================
dept_col = next((c for c in df.columns if "所属①" in str(c)), None)
section_col = next((c for c in df.columns if "所属②" in str(c)), None)

# =====================
# UI
# =====================
sheet_mode = st.selectbox(
    "表示対象",
    ["両方", "全体（1シート目）", "選別後（2シート目）"],
    index=0
)

keyword = st.text_input("部署名で検索")

city_list = ["全体"] + sorted(df["自治体"].dropna().astype(str).unique().tolist())
city = st.selectbox("自治体", city_list, index=0)

# =====================
# フィルタ
# =====================
filtered = df.copy()

# シート切替
if sheet_mode == "全体（1シート目）":
    filtered = filtered[filtered["block_no"] == 1]
elif sheet_mode == "選別後（2シート目）":
    filtered = filtered[filtered["block_no"] == 2]

# 検索
if keyword:
    cond = pd.Series(False, index=filtered.index)
    if dept_col:
        cond |= filtered[dept_col].astype(str).str.contains(keyword, na=False)
    if section_col:
        cond |= filtered[section_col].astype(str).str.contains(keyword, na=False)
    filtered = filtered[cond]

# 自治体
if city != "全体":
    filtered = filtered[filtered["自治体"] == city]

# =====================
# 件数表示
# =====================
sheet1_count = len(df[df["block_no"] == 1])
sheet2_count = len(df[df["block_no"] == 2])

sheet1_filtered = len(filtered[filtered["block_no"] == 1])
sheet2_filtered = len(filtered[filtered["block_no"] == 2])

col1, col2, col3, col4 = st.columns(4)
col1.metric("全体件数", len(df))
col2.metric("検索結果件数", len(filtered))
col3.metric("全体（元データ）", sheet1_count)
col4.metric("選別後", sheet2_count)

st.write(f"内訳 → 全体: {sheet1_filtered}件 / 選別後: {sheet2_filtered}件")

# =====================
# 表示
# =====================
show_cols = ["自治体"]
for c in ["名称", "〒"]:
    if c in filtered.columns:
        show_cols.append(c)

if dept_col:
    show_cols.append(dept_col)
if section_col:
    show_cols.append(section_col)

show_cols.append("住所")

st.dataframe(filtered[show_cols], use_container_width=True, hide_index=True)