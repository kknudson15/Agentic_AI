import sqlparse

def validate_sql(sql: str) -> str:
    try:
        parsed = sqlparse.parse(sql)
        if not parsed:
            return "Invalid SQL syntax"
        return "Valid SQL syntax"
    except Exception as e:
        return f"Validation error: {str(e)}"