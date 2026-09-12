import streamlit as st
from snowflake.snowpark.context import get_active_session

st.set_page_title("Lumina Mutual - Claims Intelligence", layout="wide")
st.title("🛡️ Lumina Mutual Insurance: Claims Analytics")

# Connect to the active Snowflake session (Streamlit in Snowflake native context)
session = get_active_session()

# Query Gold Analytics Layer
df = session.sql("SELECT * FROM LUMINA_PROD.ANALYTICS.VW_CLAIMS_BY_STATUS").to_pandas()

# Layout Metrics
col1, col2 = st.columns(2)
with col1:
    st.metric(label="Total Claim Categories", value=len(df))
with col2:
    st.metric(label="Total Payout Amount", value=f"${df['TOTAL_AMOUNT'].sum():,.2f}")

st.subheader("Claims Breakdown by Status")
st.dataframe(df, use_container_width=True)

# Interactive Chart
st.bar_chart(df.set_index("STATUS")["TOTAL_AMOUNT"])