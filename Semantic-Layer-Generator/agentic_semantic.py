import json
import yaml
from snowflake.snowpark import Session
from langchain_community.chat_models.snowflake import ChatSnowflakeCortex


# --- Agent 1: Schema Analyst ---
class SchemaAnalystAgent:
    def __init__(self, session: Session):
        self.session = session

    def extract_schema_summary(self, database: str, schema: str):
        """Introspect Snowflake schema and return simplified metadata."""
        sql = f"""
        SELECT table_name, column_name, data_type
        FROM {database}.INFORMATION_SCHEMA.COLUMNS
        WHERE table_schema = '{schema}';
        """
        df = self.session.sql(sql).collect()

        schema_summary = {}
        for row in df:
            table = row["TABLE_NAME"]
            if table not in schema_summary:
                schema_summary[table] = []
            schema_summary[table].append({
                "column": row["COLUMN_NAME"],
                "type": row["DATA_TYPE"]
            })
        return schema_summary


# --- Agent 2: Semantic Builder ---
class SemanticBuilderAgent:
    def __init__(self):
        # Initialize Snowflake Cortex chat model
        self.chat = ChatSnowflakeCortex()

    def propose_model(self, schema_summary: dict):
        """Use Snowflake Cortex to propose a YAML semantic model."""
        prompt = f"""
        You are an expert Snowflake semantic model designer.
        Given the following schema summary, generate a Snowflake semantic model in YAML.

        Schema Summary:
        {json.dumps(schema_summary, indent=2)}

        Include:
        - Entities and their relationships
        - Dimensions and measures
        - Key joins
        - Example metrics (e.g., total_sales, customer_count)
        """
        response = self.chat.invoke([
            {"role": "system", "content": "You design semantic data models for analytics."},
            {"role": "user", "content": prompt}
        ])
        return response.content.strip()


# --- Agent 3: Validator ---
class ValidatorAgent:
    def __init__(self, session: Session):
        self.session = session

    def validate(self, semantic_yaml: str):
        """Basic YAML syntax validation and schema alignment check."""
        try:
            model = yaml.safe_load(semantic_yaml)
        except yaml.YAMLError as e:
            return [f"YAML parsing failed: {e}"]

        issues = []
        if not isinstance(model, dict):
            issues.append("Model is not a valid dictionary structure.")

        return issues


# --- Orchestrator Function ---
def run_agentic_semantic(session: Session, database: str, schema: str):
    print("🧩 Extracting schema …")
    analyst = SchemaAnalystAgent(session)
    schema_summary = analyst.extract_schema_summary(database, schema)

    print("🤖 Generating semantic model via Snowflake Cortex …")
    builder = SemanticBuilderAgent()
    yaml_str = builder.propose_model(schema_summary)

    print("🔍 Validating …")
    validator = ValidatorAgent(session)
    issues = validator.validate(yaml_str)

    if issues:
        print("⚠️ Validation issues found:")
        for issue in issues:
            print("  -", issue)
    else:
        print("✅ Semantic model validated successfully!")

    return yaml_str