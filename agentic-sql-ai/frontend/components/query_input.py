import streamlit as st

def query_input():
    return st.text_area("Enter your question in plain English:", height=100)