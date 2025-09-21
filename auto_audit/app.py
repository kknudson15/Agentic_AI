from flask import Flask, render_template, request, session, jsonify
import pandas as pd
import os
from openai import OpenAI
from dotenv import load_dotenv



# ----------------------
# Config
# ----------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Please set OPENAI_API_KEY environment variable!")

client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)
app.secret_key = "super-secret-key"  # for session storage

# ----------------------
# Agent definitions
# ----------------------

def scanner_agent(data_preview):
    prompt = f"""
You are a data quality scanner. Look at the following CSV preview and identify potential issues like missing values, duplicates, and outliers:

{data_preview}
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role":"user","content":prompt}]
    )
    return response.choices[0].message.content

def rule_agent(scanner_output):
    prompt = f"""
Based on the scanner output, generate quality checks in Python/pandas or SQL to detect these issues. Provide only the code.

{scanner_output}
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role":"user","content":prompt}]
    )
    return response.choices[0].message.content

def fix_agent(rule_output):
    prompt = f"""
You are a data engineer. Generate Python/pandas or SQL code to automatically fix the issues described here:

{rule_output}
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role":"user","content":prompt}]
    )
    return response.choices[0].message.content

def reporter_agent(scanner_output, fix_code):
    prompt = f"""
Generate a concise, human-readable audit report based on the detected issues and the fixes applied:

Issues: {scanner_output}
Fixes applied: {fix_code}
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role":"user","content":prompt}]
    )
    return response.choices[0].message.content

# ----------------------
# Routes
# ----------------------

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["data_file"]
        df = pd.read_csv(file)

        # Use only first 5 rows for OpenAI prompts to save tokens
        preview_text = df.head(5).to_csv(index=False)

        # Run agents
        scanner_output = scanner_agent(preview_text)
        rules_code = rule_agent(scanner_output)
        fixes_code = fix_agent(rules_code)
        audit_report = reporter_agent(scanner_output, fixes_code)

        # Store in session (in-memory)
        session["original_preview"] = df.head(5).to_dict(orient="records")
        session["fixed_preview"] = df.head(5).to_dict(orient="records")
        session["fixes_code"] = fixes_code
        session["audit_report"] = audit_report

        return render_template("report.html",
                               original_preview=session["original_preview"],
                               fixed_preview=session["fixed_preview"],
                               fixes_code=session["fixes_code"],
                               audit_report=session["audit_report"],
                               db_choice=request.form["db_choice"])
    return render_template("index.html")


@app.route("/apply_fixes", methods=["POST"])
def apply_fixes():
    data = request.json
    db_choice = data.get("db_choice")
    # Session-only demo: no real DB writes
    return jsonify({"status": f"Fixes applied to {db_choice} (in-session demo)"})


if __name__ == "__main__":
    app.run(debug=True, port=5001)