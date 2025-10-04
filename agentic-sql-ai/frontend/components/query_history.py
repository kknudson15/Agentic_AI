import streamlit as st

def show_history(history: list):
    st.subheader("Query History")
    for item in reversed(history):
        with st.expander(f"Query: {item['query'][:50]}..."):
            st.markdown("**Generated SQL:**")
            st.code(item["sql"], language="sql")
            st.markdown(f"**Validation:** {item['validation']}")