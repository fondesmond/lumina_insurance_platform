import streamlit as st
import plotly.express as px
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Lumina Mutual - Claims Intelligence", layout="wide")
st.title("🛡️ Lumina Mutual Insurance: Claims Analytics")

# Connect to the active Snowflake session
session = get_active_session()

# Query our Gold Analytics Layer
df = session.sql("SELECT * FROM LUMINA_PROD.ANALYTICS.VW_CLAIMS_BY_STATUS").to_pandas()

# Layout Metrics
col1, col2 = st.columns(2)
with col1:
    st.metric(label="Total Claim Categories", value=len(df))
with col2:
    st.metric(label="Total Payout Amount", value=f"${df['TOTAL_AMOUNT'].sum():,.2f}")

st.subheader("Claims Breakdown by Status")
st.dataframe(df, use_container_width=True)

# Interactive Plotly Bar Chart
fig = px.bar(
    df, 
    x="STATUS", 
    y="TOTAL_AMOUNT", 
    color="STATUS",
    text="TOTAL_AMOUNT",
    title="Total Payout Amount by Claim Status",
    labels={"STATUS": "Claim Status", "TOTAL_AMOUNT": "Total Payout ($)"}
)
fig.update_traces(texttemplate='%{text:$.2f}', textposition='outside')
fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')

st.plotly_chart(fig, use_container_width=True)