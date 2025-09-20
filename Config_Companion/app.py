import streamlit as st
import sqlite3, yaml, io, re, difflib
from datetime import datetime
from html import escape
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

# --- DB Setup ---
conn = sqlite3.connect("job_configs.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS job_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_name TEXT,
    config_yaml TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER,
    governance_score INTEGER
)
""")
conn.commit()

# --- LLM Setup ---
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# --- Prompts ---
gen_prompt = ChatPromptTemplate.from_template("""
You are a pipeline config generator.
Job description: {job_description}
Past configs for context:
{context}
Use this format to generate the config: Generate a pipeline config in YAML with these exact fields and format:

job_name: <string>
description: <string>
source:
  type: <"database"|"api">
  connection_string: <string>
destination:
  type: <"database"|"csv">
  table: <string>
schedule: <cron string>
parameters:
  retries: <integer>
  batch_size: <integer>

Output raw YAML only, no markdown fences.
""")

analyze_prompt = ChatPromptTemplate.from_template("""
You are a governance checker.
Config:
{cfg}
Conflicts found:
{conflicts}
Provide:
1. Issues
2. Conflicts
3. Suggested optimizations
4. Governance score (1-10)
""")

# --- Helper to strip YAML fences ---
def strip_yaml_fences(yaml_str: str) -> str:
    return re.sub(r"^```(yaml)?\s*|```$", "", yaml_str.strip(), flags=re.MULTILINE)

# --- Retrieval ---
def retrieve_similar_configs(job_description: str, top_n: int = 3):
    keywords = [kw.strip().lower() for kw in job_description.split() if len(kw) > 3]
    cursor.execute("SELECT job_name, config_yaml FROM job_configs")
    rows = cursor.fetchall()
    scored = []
    for job_name, cfg in rows:
        job_name = job_name or ""
        cfg = cfg or ""
        score = sum(1 for kw in keywords if kw in cfg.lower())
        scored.append((score, job_name, cfg))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:top_n]

# --- Workflow ---
def run_workflow(job_description: str):
    past_table = None
    dest_table = None
    past_schedule = None
    schedule = None
    
    past_configs = retrieve_similar_configs(job_description)
    context_str = "\n\n".join([f"Job: {j}\nConfig:\n{c}" for _, j, c in past_configs])
    if not context_str:
        context_str = "No similar past jobs found."

    # Generate YAML
    resp = (gen_prompt | llm).invoke({"job_description": job_description, "context": context_str})
    original_yaml = strip_yaml_fences(resp.content.strip())

    # Conflict detection
    conflicts = []
    try:
        current_cfg = yaml.safe_load(original_yaml)
        dest_table = current_cfg.get("destination", {}).get("table")
        schedule = current_cfg.get("schedule")
    except Exception as e:
        conflicts.append(f"Error parsing config: {e}")

    for _, job_name, cfg in past_configs:
        try:
            parsed_cfg = yaml.safe_load(strip_yaml_fences(cfg))
        except:
            continue
        past_table = parsed_cfg.get("destination", {}).get("table")
        past_schedule = parsed_cfg.get("schedule")
        if past_table and dest_table and past_table == dest_table:
            conflicts.append(f"Destination table conflict: {past_table} already used by {job_name}.")
        if past_schedule and schedule and past_schedule == schedule:
            conflicts.append(f"Schedule overlap: both run at {schedule}.")
    if not conflicts:
        conflicts = ["No conflicts detected."]

    # Governance analysis
    resp = (analyze_prompt | llm).invoke({"cfg": original_yaml, "conflicts": "\n".join(conflicts)})
    analysis = resp.content.strip()

    return context_str, original_yaml, conflicts, analysis

# --- Governance Score Extractor ---
def extract_score(analysis: str) -> int:
    match = re.search(r"(\d{1,2})\s*(?:/10| out of 10)?", analysis)
    if match:
        return int(match.group(1))
    return None

# --- Save Configs ---
def save_configs(job_name: str, original_yaml: str, analysis: str):
    cursor.execute("SELECT MAX(version) FROM job_configs WHERE job_name = ?", (job_name,))
    last_version_row = cursor.fetchone()
    last_version = last_version_row[0] if last_version_row and last_version_row[0] is not None else 0
    version = last_version + 1

    score = extract_score(analysis)

    cursor.execute(
        "INSERT INTO job_configs (job_name, config_yaml, version, governance_score) VALUES (?, ?, ?, ?)",
        (job_name, original_yaml, version, score)
    )
    conn.commit()
    return version

# --- Streamlit App ---
st.title("Data Pipeline Config Governance Assistant")

tab1, tab2 = st.tabs(["Generate Config", "Config History"])

# --- Generate Config tab ---
with tab1:
    st.header("Generate New Config")
    job_description = st.text_area("Enter Job Description", height=150)

    if st.button("Generate Config", key="generate_config"):
        with st.spinner("Generating and analyzing config..."):
            context, original_yaml, conflicts, analysis = run_workflow(job_description)

            st.session_state['original_yaml'] = original_yaml
            st.session_state['analysis'] = analysis
            st.session_state['context'] = context
            st.session_state['conflicts'] = conflicts

            # --- Determine job name ---
            try:
                suggested_name = yaml.safe_load(original_yaml).get("job_name")
            except:
                suggested_name = None

            if not suggested_name:
                suggested_name = f"job_{datetime.now().strftime('%Y%m%d')}"
            st.session_state['job_name'] = st.text_input("Enter Job Name", value=suggested_name)

    if 'original_yaml' in st.session_state:
        st.subheader("🔎 Retrieved Past Configs")
        st.code(st.session_state['context'], language="yaml")

        st.subheader("📄 Generated Config")
        st.code(st.session_state['original_yaml'], language="yaml")

        st.subheader("⚠️ Conflicts")
        for c in st.session_state.get('conflicts', []):
            if "conflict" in c.lower():
                st.error(c)
            else:
                st.success(c)

        st.subheader("✅ Governance Analysis")
        st.text(st.session_state['analysis'])

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Approve & Save", key="approve_save"):
                version = save_configs(
                    st.session_state['job_name'],
                    st.session_state['original_yaml'],
                    st.session_state['analysis']
                )
                st.success(f"Saved job '{st.session_state['job_name']}' v{version}.")
                # Clear session state after save
                for key in ['original_yaml', 'analysis', 'context', 'conflicts', 'job_name']:
                    st.session_state.pop(key, None)

        with col2:
            if st.button("❌ Reject", key="reject_save"):
                st.warning("Config rejected. Nothing saved.")
                # Clear session state after reject
                for key in ['original_yaml', 'analysis', 'context', 'conflicts', 'job_name']:
                    st.session_state.pop(key, None)
# --- Config History Tab ---
with tab2:
    st.header("📜 Config History Dashboard")
    search = st.text_input("🔍 Search by job name")
    cursor.execute("""
        SELECT DISTINCT job_name FROM job_configs
        WHERE job_name LIKE ?
        ORDER BY job_name ASC
    """, (f"%{search}%",))
    job_names = [row[0] for row in cursor.fetchall()]

    if job_names:
        job_choice = st.selectbox("Select Job", job_names)

        cursor.execute("""
            SELECT version, governance_score, created_at, config_yaml
            FROM job_configs
            WHERE job_name = ?
            ORDER BY version DESC
        """, (job_choice,))
        versions = cursor.fetchall()

        st.subheader("📦 Versions")
        for v, score, created_at, cfg in versions:
            with st.expander(f"v{v}"):
                st.write(f"🕒 {created_at}")
                st.write(f"📊 Governance Score: {score if score else 'N/A'} / 10")
                st.code(cfg, language="yaml")
    else:
        st.info("No jobs found. Try generating a config first.")