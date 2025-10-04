import snowflake.connector
import yaml
import os

# A resilient semantic model generator with safe defaults
def generate_semantic_model(user=None, password=None, account=None, warehouse=None, database=None, schema=None):
    user = user or os.getenv("SNOW_USER")
    password = password or os.getenv("SNOW_PASS")
    account = account or os.getenv("SNOW_ACCOUNT")
    warehouse = warehouse or os.getenv("SNOW_WAREHOUSE")
    database = database or os.getenv("SNOW_DATABASE")
    schema = schema or os.getenv("SNOW_SCHEMA")

    conn = snowflake.connector.connect(
        user=user,
        password=password,
        account=account,
        warehouse=warehouse,
        database=database,
        schema=schema
    )
    cur = conn.cursor()
    cur.execute(f"SELECT table_name, column_name, data_type FROM information_schema.columns WHERE table_schema = '{schema}'")
    rows = cur.fetchall()

    semantic = {"entities": {}, "metrics": {}, "relationships": []}

    # Build basic entities/fields
    for table_name, column_name, data_type in rows:
        ent = semantic["entities"].setdefault(table_name, {"table": table_name, "fields": {}})
        ent["fields"][column_name] = {"type": data_type}

    # Auto-create simple numeric metrics
    for table, details in semantic["entities"].items():
        for field, meta in details["fields"].items():
            dtype = meta.get("type", "")
            if any(n in dtype.upper() for n in ["NUMBER", "INT", "DECIMAL", "FLOAT"]):
                if any(k in field.lower() for k in ["amount", "price", "revenue", "total"]):
                    semantic["metrics"][f"total_{table.lower()}_{field}"] = f"SUM({table}.{field})"

    # Save YAML snapshot for debugging
    with open("backend/app/semantic_model.yaml", "w") as f:
        yaml.dump(semantic, f)

    return semantic