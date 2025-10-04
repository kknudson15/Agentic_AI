import json
import yaml
from backend.app.utils.prompt_templates import PLANNER_PROMPT
from backend.app.agents.agent_tools import (
    generate_sql_tool,
    validate_sql_tool,
    execute_sql_tool,
)
from backend.app.config import USE_DYNAMIC_SEMANTIC, generate_semantic_model, llm_client

# Load semantic model (dynamic optional)
if USE_DYNAMIC_SEMANTIC:
    # generate_semantic_model reads Snowflake creds from config or env
    SEMANTIC_MODEL = generate_semantic_model()
else:
    try:
        with open("backend/app/semantic_model.yaml", "r") as f:
            SEMANTIC_MODEL = yaml.safe_load(f)
    except FileNotFoundError:
        SEMANTIC_MODEL = {"entities": {}, "metrics": {}, "relationships": []}

class AgentOrchestrator:
    def __init__(self, semantic_model: dict = None):
        self.semantic_model = semantic_model or SEMANTIC_MODEL

    def plan(self, user_query: str) -> dict:
        # Ask the model to produce a JSON plan of tools to run
        semantic_text = yaml.dump(self.semantic_model, default_flow_style=False)
        planner_prompt = PLANNER_PROMPT + f"\nsemantic_model:\n{semantic_text}\nuser_query:\n{user_query}\n"
        planner_response = llm_client(planner_prompt)
        try:
            plan = json.loads(planner_response)
            return plan
        except Exception:
            # If planner fails to return JSON, fallback to a simple linear plan
            return {"steps": [{"tool": "generate_sql", "input": user_query}, {"tool": "validate_sql", "input": "<from_generate>"}]}

    def run(self, user_query: str, execute: bool = False) -> dict:
        plan = self.plan(user_query)
        last_sql = None
        result = {"sql": None, "validation": None, "execution": None}

        for step in plan.get("steps", []):
            tool = step.get("tool")
            inp = step.get("input")

            if tool == "generate_sql":
                gen_in = inp if inp else user_query
                gen = generate_sql_tool(gen_in, self.semantic_model)
                last_sql = gen.get("sql")
                result["sql"] = last_sql

            elif tool == "validate_sql":
                to_validate = last_sql if inp in [None, "<from_generate>"] else inp
                val = validate_sql_tool(to_validate)
                result["validation"] = val
                if not val.get("ok"):
                    # stop early on validation failure
                    return result

            elif tool == "execute_sql":
                # Only allow execute if flag enabled at runtime
                if not execute:
                    result["execution"] = {"ok": False, "error": "Execution skipped (execute=False)"}
                else:
                    to_exec = last_sql if inp in [None, "<from_generate>"] else inp
                    exec_res = execute_sql_tool(to_exec)
                    result["execution"] = exec_res

        return result


# Helper: convenience function used by routes
def orchestrate_query(user_query: str, execute: bool = False) -> dict:
    orchestrator = AgentOrchestrator()
    return orchestrator.run(user_query, execute=execute)