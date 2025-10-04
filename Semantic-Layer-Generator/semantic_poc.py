from snowflake.snowpark import Session
from agentic_semantic import run_agentic_semantic

# Example Snowflake connection config
connection_parameters = {
    "account": "YOUR_ACCOUNT",
    "user": "YOUR_USERNAME",
    "password": "YOUR_PASSWORD",
    "role": "YOUR_ROLE",
    "warehouse": "YOUR_WAREHOUSE",
    "database": "YOUR_DATABASE",
    "schema": "PUBLIC"
}

if __name__ == "__main__":
    session = Session.builder.configs(connection_parameters).create()

    # Replace with your target DB/schema
    database = "YOUR_DATABASE"
    schema = "PUBLIC"

    yaml_str = run_agentic_semantic(session, database, schema)

    print("\n📄 Proposed Semantic Model (YAML):\n")
    print(yaml_str)