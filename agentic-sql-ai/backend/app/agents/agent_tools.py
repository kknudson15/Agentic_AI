import json
import yaml
from backend.app.config import llm_client, USE_SNOWFLAKE, SNOWFLAKE_CONN
from backend.app.utils.prompt_templates import SQL_COT_PROMPT
import sqlparse

# Tool: generate_sql
def generate_sql_tool(user_query: str, semantic_model: dict) -> dict:
    semantic_text = yaml.dump(semantic_model, default_flow_style=False)
    prompt = SQL_COT_PROMPT.format(semantic_model=semantic_text, user_query=user_query)
    resp = llm_client(prompt)

    # Attempt to parse JSON from the model's output
    try:
        parsed = json.loads(resp)
        sql = parsed.get("sql")
        notes = parsed.get("notes", "")
        return {"ok": True, "sql": sql, "notes": notes}
    except Exception:
        # Fallback: try to extract SQL heuristically
        # strip leading/trailing quotes
        text = resp.strip()
        # If it looks like SQL, return it
        return {"ok": False, "sql": text, "notes": "Could not parse JSON response; returning raw model output."}

# Tool: validate_sql
def validate_sql_tool(sql: str) -> dict:
    # Basic syntactic validation using sqlparse
    try:
        parsed = sqlparse.parse(sql)
        if not parsed:
            return {"ok": False, "error": "Invalid SQL syntax"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

    # Optional: run EXPLAIN in Snowflake if configured
    if USE_SNOWFLAKE and SNOWFLAKE_CONN:
        try:
            conn = SNOWFLAKE_CONN
            cur = conn.cursor()
            # Use EXPLAIN to check query plan without running
            cur.execute(f"EXPLAIN USING TEXT {sql}")
            plan = cur.fetchall()
            return {"ok": True, "explain": plan}
        except Exception as e:
            return {"ok": False, "error": f"Snowflake EXPLAIN failed: {str(e)}"}

    return {"ok": True, "explain": None}

# Tool: execute_sql
def execute_sql_tool(sql: str, limit: int = 1000) -> dict:
    if not USE_SNOWFLAKE or not SNOWFLAKE_CONN:
        return {"ok": False, "error": "Snowflake execution not enabled or connection missing."}
    try:
        conn = SNOWFLAKE_CONN
        cur = conn.cursor()
        cur.execute(sql)
        cols = [c[0] for c in cur.description]
        rows = cur.fetchmany(limit)
        results = [dict(zip(cols, r)) for r in rows]
        return {"ok": True, "results": results, "columns": cols}
    except Exception as e:
        return {"ok": False, "error": str(e)}