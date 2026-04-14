import pandas as pd
import streamlit as st

st.set_page_config(page_title="東京23区 DM検索", layout="wide")
st.title("東京23区 DM検索")

df = pd.read_excel("20260414_東京23区.xlsx")
df.columns = df.columns.astype(str).str.strip()

# Power Query由来の本体列だけ使う
data_cols = [c for c in df.columns if c.startswith("Column")]
df = df[["Name"] + data_cols].copy()

# 1行目を見出し化
headers = ["ファイル名"] + df.iloc[0, 1:].astype(str).str.strip().tolist()
df.columns = headers
df = df.iloc[1:].reset_index(drop=True)

# 列名の余計な空白除去
df.columns = df.columns.astype(str).str.strip()

# ダブり見出し行を除去
if "名称" in df.columns:
    df = df[df["名称"].astype(str).str.strip() != "名称"].copy()

# 自治体名
df["自治体"] = df["ファイル名"].astype(str).str.extract(r"^\d+_(.+?)_DM")

# 住所列を柔軟に拾う
addr_cols = [c for c in df.columns if str(c).strip().startswith("住所")]

for c in addr_cols:
    df[c] = df[c].fillna("").astype(str).str.strip()

if addr_cols:
    df["住所"] = df[addr_cols].agg("".join, axis=1).str.strip()
else:
    df["住所"] = ""

# 検索対象列
dept_col = next((c for c in df.columns if "所属①" in str(c)), None)
section_col = next((c for c in df.columns if "所属②" in str(c)), None)

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

col1, col2 = st.columns(2)
col1.metric("全体件数", len(df))
col2.metric("検索結果件数", len(filtered))

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

with st.expander("確認用"):
    st.write("住所列として拾った列:", addr_cols)
    st.dataframe(df[["自治体", "名称", "住所"]].head(10), use_container_width=True, hide_index=True)