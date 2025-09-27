import streamlit as st
import pandas as pd
from agents.knowledge_base_agent import KnowledgeBaseAgent

kb = KnowledgeBaseAgent()

st.title("Autonomous Incident Management Dashboard")

def load_data():
    data = kb.fetch_incidents()
    df = pd.DataFrame(
        data, 
        columns=[
            "ID","Timestamp","Pipeline","Task ID","Error","Severity",
            "Retry Count","Pipeline Type","Source System","Summary",
            "Next Steps","Fix","Validation"
        ]
    )
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], unit='s')
    return df

df = load_data()

# -----------------------------
# Filters
# -----------------------------
st.subheader("Filter Incidents")
pipeline_filter = st.selectbox("Select Pipeline", ["All"] + df["Pipeline"].unique().tolist())
severity_filter = st.selectbox("Select Severity", ["All", "High", "Medium", "Low"])

filtered_df = df.copy()
if pipeline_filter != "All":
    filtered_df = filtered_df[filtered_df["Pipeline"] == pipeline_filter]
if severity_filter != "All":
    filtered_df = filtered_df[filtered_df["Severity"] == severity_filter]

st.dataframe(filtered_df)

# -----------------------------
# Two-column visualizations
# -----------------------------
st.subheader("Incident Visualizations")
col1, col2 = st.columns(2)

with col1:
    st.write("Incidents by Severity")
    severity_counts = filtered_df["Severity"].value_counts()
    st.bar_chart(severity_counts)

with col2:
    st.write("Incidents Over Time")
    if not filtered_df.empty:
        time_series = filtered_df.groupby(filtered_df["Timestamp"].dt.floor("min")).size()
        st.line_chart(time_series)