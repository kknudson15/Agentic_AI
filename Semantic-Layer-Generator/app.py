import streamlit as st
from snowflake.snowpark import Session
from agentic_semantic import run_agentic_semantic

st.set_page_config(page_title="Agentic Semantic Builder", page_icon="🧠", layout="centered")

# --- Sidebar: Connection Config ---
st.sidebar.title("🔐 Snowflake Connection")
account = st.sidebar.text_input("Account", placeholder="your_account_id")
user = st.sidebar.text_input("User", placeholder="username")
password = st.sidebar.text_input("Password", type="password")
role = st.sidebar.text_input("Role", value="SYSADMIN")
warehouse = st.sidebar.text_input("Warehouse", value="COMPUTE_WH")
database = st.sidebar.text_input("Database", value="MY_DB")

connect_btn = st.sidebar.button("Connect to Snowflake")

session = None

if connect_btn:
    try:
        session = (
            Session.builder.configs(
                {
                    "account": account,
                    "user": user,
                    "password": password,
                    "role": role,
                    "warehouse": warehouse,
                    "database": database,
                }
            ).create()
        )
        st.session_state["session"] = session
        st.sidebar.success("✅ Connected successfully!")
    except Exception as e:
        st.sidebar.error(f"Connection failed: {e}")

# Reuse session if already connected
if "session" in st.session_state:
    session = st.session_state["session"]

# --- Schema Picker + Generation ---
if session:
    try:
        schemas_df = session.sql("SHOW SCHEMAS").collect()
        schema_names = [row["name"] for row in schemas_df if not row["name"].startswith("INFORMATION_SCHEMA")]

        selected_schema = st.selectbox("Select a Schema:", schema_names)

        if st.button("🧩 Generate Semantic Model"):
            with st.spinner("Running Agentic AI to build semantic model..."):
                yaml_str = run_agentic_semantic(session, database, selected_schema)

            st.success("✅ Model generated successfully!")
            st.subheader("📄 Generated Semantic Model (YAML)")
            st.code(yaml_str, language="yaml")

            st.download_button(
                label="💾 Download YAML",
                data=yaml_str,
                file_name=f"{selected_schema}_semantic_model.yaml",
                mime="text/yaml",
            )

    except Exception as e:
        st.error(f"Error loading schemas: {e}")
else:
    st.info("Please connect to Snowflake in the sidebar to continue.")