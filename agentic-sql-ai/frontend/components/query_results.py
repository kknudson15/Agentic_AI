import streamlit as st

def show_results(sql: str, validation: str):
    st.subheader("Generated SQL")
    st.code(sql, language="sql")
    st.markdown(f"**Validation Result:** {validation}")