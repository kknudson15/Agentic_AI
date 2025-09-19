import streamlit as st
import sqlite3, yaml, io, re, difflib
from datetime import datetime
from html import escape
from langchain_community.chat_models import ChatOpenAI
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
    auto_fixed BOOLEAN DEFAULT 0,
    governance_score INTEGER
)
""")
conn.commit()

# --- LLM Setup ---
llm = ChatOpenAI(model="gpt-4o-mini")

# --- Prompts ---
gen_prompt = ChatPromptTemplate.from_template("""
You are a pipeline config generator.
Job description: {job_description}
Past configs for context:
{context}
Generate a YAML config.
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

fix_prompt = ChatPromptTemplate.from_template("""
You are a pipeline auto-fixer.
Based on the analysis, output ONLY a corrected YAML config.
Analysis:
{analysis}
""")

# --- Retrieval ---
def retrieve_similar_configs(job_description: str, top_n: int = 3):
    keywords = [kw.strip().lower() for kw in job_description.split() if len(kw) > 3]
    cursor.execute("SELECT job_name, config_yaml FROM job_configs")
    rows = cursor.fetchall()
    scored = []
    for job_name, cfg in rows:
        score = sum(1 for kw in keywords if kw in cfg.lower())
        if score > 0:
            scored.append((score, job_name, cfg))
    scored.sort(reverse=True)
    return scored[:top_n]

# --- Workflow functions ---
def run_workflow(job_description: str):
    past_configs = retrieve_similar_configs(job_description)
    context_str = "\n\n".join([f"Job: {j}\nConfig:\n{c}" for _, j, c in past_configs])
    if not context_str:
        context_str = "No similar past jobs found."

    # Generate YAML
    resp = (gen_prompt | llm).invoke({"job_description": job_description, "context": context_str})
    original_yaml = resp.content.strip()

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
            parsed_cfg = yaml.safe_load(cfg)
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

    # Auto-fix
    resp = (fix_prompt | llm).invoke({"analysis": analysis})
    fixed_yaml = resp.content.strip()

    return context_str, original_yaml, conflicts, analysis, fixed_yaml

# --- Governance Score Extractor ---
def extract_score(analysis: str) -> int:
    match = re.search(r"(\d+)\s*/?\s*10", analysis)
    if match:
        return int(match.group(1))
    return None

# --- Save Configs ---
def save_configs(job_name: str, original_yaml: str, fixed_yaml: str, analysis: str):
    cursor.execute("SELECT MAX(version) FROM job_configs WHERE job_name = ?", (job_name,))
    last_version = cursor.fetchone()[0]
    version = (last_version + 1) if last_version else 1

    score = extract_score(analysis)

    cursor.execute(
        "INSERT INTO job_configs (job_name, config_yaml, version, auto_fixed, governance_score) VALUES (?, ?, ?, 0, ?)",
        (job_name, original_yaml, version, score)
    )
    cursor.execute(
        "INSERT INTO job_configs (job_name, config_yaml, version, auto_fixed, governance_score) VALUES (?, ?, ?, 1, ?)",
        (job_name, fixed_yaml, version, score)
    )
    conn.commit()
    return version

# --- Diff Helpers ---
def yaml_diff_html(cfg1: str, cfg2: str) -> str:
    diff = difflib.ndiff(cfg1.splitlines(), cfg2.splitlines())
    html_lines = []
    for line in diff:
        if line.startswith("+ "):
            html_lines.append(f"<div style='background-color:#e6ffed;color:#22863a;'>+ {escape(line[2:])}</div>")
        elif line.startswith("- "):
            html_lines.append(f"<div style='background-color:#ffeef0;color:#b31d28;'>- {escape(line[2:])}</div>")
        elif line.startswith("? "):
            continue
        else:
            html_lines.append(f"<div style='background-color:#f6f8fa;color:#24292e;'>{escape(line[2:])}</div>")
    return "<pre style='font-family:monospace;'>" + "\n".join(html_lines) + "</pre>"

def export_yaml(config: str, filename: str):
    return io.BytesIO(config.encode("utf-8")), filename

def export_diff(cfg1: str, cfg2: str, job_choice: str, v1: int, v2: int):
    diff_plain = difflib.unified_diff(
        cfg1.splitlines(), cfg2.splitlines(),
        fromfile=f"{job_choice}_v{v1}", tofile=f"{job_choice}_v{v2}", lineterm=""
    )
    diff_text = "\n".join(diff_plain)
    return io.BytesIO(diff_text.encode("utf-8")), f"{job_choice}_diff_v{v1}_vs_v{v2}.md"

# --- Streamlit App ---
st.title("🛠️ Data Pipeline Config Governance Assistant")

tab1, tab2 = st.tabs(["⚡ Generate Config", "📜 Config History"])

with tab1:
    st.header("Generate New Config")
    job_description = st.text_area("Enter Job Description", height=150)

    if st.button("Generate Config"):
        with st.spinner("Generating and analyzing config..."):
            context, original_yaml, conflicts, analysis, fixed_yaml = run_workflow(job_description)

        st.subheader("🔎 Retrieved Past Configs")
        st.code(context, language="yaml")

        st.subheader("📄 Original Config")
        st.code(original_yaml, language="yaml")

        st.subheader("⚠️ Conflicts")
        for c in conflicts:
            st.error(c) if "conflict" in c.lower() else st.success(c)

        st.subheader("✅ Governance Analysis")
        st.text(analysis)

        st.subheader("🛠️ Auto-Fixed Config")
        st.code(fixed_yaml, language="yaml")

        # Extract job name
        try:
            job_name = yaml.safe_load(fixed_yaml).get("job_name", f"job_{datetime.now().strftime('%Y%m%d%H%M')}")
        except:
            job_name = f"job_{datetime.now().strftime('%Y%m%d%H%M')}"

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Approve & Save"):
                version = save_configs(job_name, original_yaml, fixed_yaml, analysis)
                st.success(f"Saved job '{job_name}' v{version} (with auto-fix).")
        with col2:
            if st.button("❌ Reject"):
                st.warning("Config rejected. Nothing saved.")

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
            SELECT version, auto_fixed, governance_score, created_at, config_yaml
            FROM job_configs
            WHERE job_name = ?
            ORDER BY version DESC, auto_fixed ASC
        """, (job_choice,))
        versions = cursor.fetchall()

        st.subheader("📦 Versions")
        for v, auto_fixed, score, created_at, cfg in versions:
            with st.expander(f"v{v} ({'Auto-fixed' if auto_fixed else 'Original'})"):
                st.write(f"🕒 {created_at}")
                st.write(f"📊 Governance Score: {score if score else 'N/A'} / 10")
                st.code(cfg, language="yaml")

        st.subheader("🔀 Compare Versions")
        version_options = sorted(set(v[0] for v in versions), reverse=True)
        col1, col2 = st.columns(2)
        with col1:
            v1 = st.selectbox("Version A", version_options, key="v1")
        with col2:
            v2 = st.selectbox("Version B", version_options, key="v2")

        if v1 and v2 and v1 != v2:
            cursor.execute("""
                SELECT config_yaml FROM job_configs
                WHERE job_name = ? AND version = ? AND auto_fixed = 0
            """, (job_choice, v1))
            cfg1 = cursor.fetchone()[0]

            cursor.execute("""
                SELECT config_yaml FROM job_configs
                WHERE job_name = ? AND version = ? AND auto_fixed = 1
            """, (job_choice, v2))
            cfg2 = cursor.fetchone()[0]

            view_mode = st.radio("Choose comparison view:", ["📝 Side-by-Side YAML", "📊 Inline Diff (highlighted)"])

            if view_mode == "📝 Side-by-Side YAML":
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Version {v1} (Original)**")
                    st.code(cfg1, language="yaml")
                with col2:
                    st.markdown(f"**Version {v2} (Auto-fixed)**")
                    st.code(cfg2, language="yaml")

            elif view_mode == "📊 Inline Diff (highlighted)":
                diff_output_html = yaml_diff_html(cfg1, cfg2)
                st.markdown(diff_output_html, unsafe_allow_html=True)

            # Export buttons
            st.subheader("⬇️ Export Options")
            col1, col2, col3 = st.columns(3)
            with col1:
                yaml_file, yaml_name = export_yaml(cfg1, f"{job_choice}_v{v1}_original.yaml")
                st.download_button("📥 Export Version A (YAML)", data=yaml_file, file_name=yaml_name, mime="text/yaml")
            with col2:
                yaml_file, yaml_name = export_yaml(cfg2, f"{job_choice}_v{v2}_autofixed.yaml")
                st.download_button("📥 Export Version B (YAML)", data=yaml_file, file_name=yaml_name, mime="text/yaml")
            with col3:
                if view_mode == "📊 Inline Diff (highlighted)":
                    diff_file, diff_name = export_diff(cfg1, cfg2, job_choice, v1, v2)
                    st.download_button("📥 Export Diff (MD)", data=diff_file, file_name=diff_name, mime="text/markdown")
        else:
            st.info("Select two different versions to compare.")
    else:
        st.info("No jobs found. Try generating a config first.")