import streamlit as st
import requests
from components.query_input import query_input
from components.query_results import show_results
from components.query_history import show_history

API_URL = "http://localhost:8000/api/query"

st.set_page_config(page_title="Agentic SQL Generator", layout="centered")

st.title("Agentic SQL Generator for Snowflake")

# Session state to track history
if "history" not in st.session_state:
    st.session_state.history = []

# Input
user_query = query_input()

if st.button("Generate SQL"):
    if user_query:
        with st.spinner("Generating SQL..."):
            try:
                response = requests.post(API_URL, json={"user_query": user_query})
                if response.status_code == 200:
                    data = response.json()
                    sql = data["sql"]
                    validation = data["validation"]
                    st.session_state.history.append({
                        "query": user_query,
                        "sql": sql,
                        "validation": validation
                    })
                    show_results(sql, validation)
                else:
                    st.error(f"API Error: {response.text}")
            except Exception as e:
                st.error(f"Request failed: {str(e)}")

# History
if st.session_state.history:
    show_history(st.session_state.history)