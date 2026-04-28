import os
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DATA_PATH = "CLV Dataset.csv"

@st.cache_data
def load_data(path=DATA_PATH):
    if not os.path.exists(path):
        st.error(f"Dataset not found: {path}")
        return pd.DataFrame()

    df = pd.read_csv(path)
    critical = ["Customer_Lifetime_Value", "churn_probability",
                "total_revenue_generated", "purchase_frequency",
                "average_order_value", "engagement_score"]
    df = df.dropna(subset=critical).drop_duplicates()
    df = df[
        (df["Customer_Lifetime_Value"] > 0) &
        (df["churn_probability"].between(0, 1)) &
        (df["purchase_frequency"] >= 1) &
        (df["average_order_value"] > 0)
    ]
    return df

@st.cache_data
def engineer_features(df):
    if df.empty:
        return df

    bins = [0, 2000, 5000, df["Customer_Lifetime_Value"].max() + 1]
    labels = ["Low Value", "Medium Value", "High Value"]
    df["clv_segment"] = pd.cut(df["Customer_Lifetime_Value"], bins=bins,
                                labels=labels, include_lowest=True).astype(str)

    df["churn_risk"] = pd.cut(df["churn_probability"],
                                bins=[0, 0.35, 0.65, 1.01],
                                labels=["Low Risk", "Medium Risk", "High Risk"],
                                include_lowest=True).astype(str)

    rev_bins = [0, 100, 500, 1000, df["total_revenue_generated"].max() + 1]
    rev_labels = ["Bronze", "Silver", "Gold", "Platinum"]
    df["revenue_band"] = pd.cut(df["total_revenue_generated"],
                                  bins=rev_bins, labels=rev_labels,
                                  include_lowest=True).astype(str)

    mn, mx = df["engagement_score"].min(), df["engagement_score"].max()
    df["engagement_score_normalized"] = (
        (df["engagement_score"] - mn) / (mx - mn) * 100
    ).round(2)

    df["priority_score"] = (
        df["Customer_Lifetime_Value"] / df["Customer_Lifetime_Value"].max() * 0.5 +
        df["churn_probability"] * 0.3 +
        df["engagement_score_normalized"] / 100 * 0.2
    ).round(4)

    return df

st.set_page_config(page_title="CLV Intelligence Dashboard",
                   layout="wide",
                   page_icon="📊")

st.title("CLV Intelligence Dashboard")
st.markdown(
    "Streamlit-hosted CLV dashboard powered by the CLV dataset. Use the filters "
    "to explore customer lifetime value, churn risk, revenue bands, and channel performance."
)

raw_df = load_data()
if raw_df.empty:
    st.stop()

df = engineer_features(raw_df)

clv_options = ["All"] + sorted(df["clv_segment"].dropna().unique().tolist())
churn_options = ["All"] + sorted(df["churn_risk"].dropna().unique().tolist())
channel_options = ["All"] + sorted(df["acquisition_channel"].dropna().unique().tolist())
region_options = ["All"] + sorted(df["location_region"].dropna().unique().tolist())

with st.sidebar:
    st.header("Filters")
    selected_clv = st.selectbox("CLV Segment", clv_options, index=0)
    selected_churn = st.selectbox("Churn Risk", churn_options, index=0)
    selected_channel = st.selectbox("Acquisition Channel", channel_options, index=0)
    selected_region = st.selectbox("Region", region_options, index=0)

filtered = df.copy()
if selected_clv != "All":
    filtered = filtered[filtered["clv_segment"] == selected_clv]
if selected_churn != "All":
    filtered = filtered[filtered["churn_risk"] == selected_churn]
if selected_channel != "All":
    filtered = filtered[filtered["acquisition_channel"] == selected_channel]
if selected_region != "All":
    filtered = filtered[filtered["location_region"] == selected_region]

st.markdown(f"**Filtered customers:** {len(filtered):,} / {len(df):,}")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Total Customers", f"{len(filtered):,}")
with col2:
    st.metric("Avg CLV", f"₹{filtered['Customer_Lifetime_Value'].mean():,.0f}")
with col3:
    danger_count = ((filtered["clv_segment"] == "High Value") &
                    (filtered["churn_risk"] == "High Risk")).sum()
    st.metric("Danger Zone", f"{danger_count:,}")
with col4:
    st.metric("Avg Churn", f"{filtered['churn_probability'].mean():.1%}")
with col5:
    best_channel = filtered.groupby("acquisition_channel")["Customer_Lifetime_Value"].mean().idxmax()
    st.metric("Best Channel", best_channel)

st.write("---")

seg_counts = filtered["clv_segment"].value_counts().reindex(clv_options[1:], fill_value=0)
pie = px.pie(seg_counts, values=seg_counts.values, names=seg_counts.index,
             hole=0.45, title="CLV Segment Distribution")

churn_counts = filtered["churn_risk"].value_counts().reindex(churn_options[1:], fill_value=0)
bar = px.bar(x=churn_counts.index, y=churn_counts.values,
             title="Churn Risk Breakdown", labels={"x": "Churn Risk", "y": "Count"})

rev_counts = filtered["revenue_band"].value_counts().reindex(["Platinum", "Gold", "Silver", "Bronze"], fill_value=0)
donut = px.pie(rev_counts, values=rev_counts.values, names=rev_counts.index,
               hole=0.45, title="Revenue Band Composition")

scatter = px.scatter(filtered.sample(min(2000, len(filtered)), random_state=42),
                     x="churn_probability", y="Customer_Lifetime_Value",
                     color="clv_segment", title="CLV vs Churn Probability",
                     labels={"churn_probability": "Churn Probability",
                             "Customer_Lifetime_Value": "CLV (₹)"})

row1_col1, row1_col2 = st.columns(2)
with row1_col1:
    st.plotly_chart(pie, use_container_width=True)
with row1_col2:
    st.plotly_chart(bar, use_container_width=True)

row2_col1, row2_col2 = st.columns(2)
with row2_col1:
    st.plotly_chart(donut, use_container_width=True)
with row2_col2:
    st.plotly_chart(scatter, use_container_width=True)

st.write("---")

st.subheader("Filtered Customer Data")
st.dataframe(filtered.head(500))
