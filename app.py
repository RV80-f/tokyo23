import pandas as pd
import streamlit as st

st.set_page_config(page_title="東京23区 DM検索", layout="wide")
st.title("東京23区 DM検索")

df = pd.read_excel("20260414_東京23区.xlsx")
df.columns = df.columns.astype(str).str.strip()

data_cols = [c for c in df.columns if c.startswith("Column")]
df = df[["Name"] + data_cols].copy()

headers = ["ファイル名"] + df.iloc[0, 1:].astype(str).str.strip().tolist()
df.columns = headers
df = df.iloc[1:].reset_index(drop=True)

df["自治体"] = df["ファイル名"].astype(str).str.extract(r"^\d+_(.+?)_DM")
df.columns = df.columns.astype(str).str.strip()

dept_col = "所属①（部署）" if "所属①（部署）" in df.columns else None
section_col = "所属②（課/係）" if "所属②（課/係）" in df.columns else None

address_parts = [c for c in ["住所1", "住所2", "住所3"] if c in df.columns]
if address_parts:
    df["住所"] = (
        df[address_parts]
        .fillna("")
        .astype(str)
        .agg("".join, axis=1)
        .str.strip()
    )
else:
    df["住所"] = ""

keyword = st.text_input("部署名で検索")
city_list = ["全体"] + sorted(df["自治体"].dropna().astype(str).unique().tolist())
city = st.selectbox("自治体", city_list, index=0)

filtered = df.copy()

if keyword:
    cond = pd.Series(False, index=filtered.index)
    if dept_col:
        cond = cond | filtered[dept_col].astype(str).str.contains(keyword, na=False)
    if section_col:
        cond = cond | filtered[section_col].astype(str).str.contains(keyword, na=False)
    filtered = filtered[cond]

if city != "全体":
    filtered = filtered[filtered["自治体"] == city]

# 件数表示
col1, col2 = st.columns(2)
col1.metric("全体件数", len(df))
col2.metric("検索結果件数", len(filtered))

show_cols = ["自治体"]
for c in ["名称", "〒", "所属①（部署）", "所属②（課/係）", "住所"]:
    if c in filtered.columns:
        show_cols.append(c)

st.dataframe(filtered[show_cols], use_container_width=True, hide_index=True)