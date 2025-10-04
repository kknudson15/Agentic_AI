import os
from openai import OpenAI
import snowflake.connector
import dotenv

dotenv.load_dotenv()

# Toggles
USE_DYNAMIC_SEMANTIC = os.getenv("USE_DYNAMIC_SEMANTIC", "False").lower() == "true"
USE_SNOWFLAKE = os.getenv("USE_SNOWFLAKE", "False").lower() == "true"

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

def llm_client(prompt: str, temperature: float = 0.0) -> str:
    # Simple chat-style invocation - keep deterministic for SQL generation
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[{"role": "system", "content": "You are an assistant that plans and generates Snowflake SQL."}, {"role": "user", "content": prompt}],
        temperature=temperature
    )
    return response.choices[0].message.content

# Snowflake connection (shared)
SNOWFLAKE_CONN = None
if USE_SNOWFLAKE:
    SNOWFLAKE_CONN = snowflake.connector.connect(
        user=os.getenv("SNOW_USER"),
        password=os.getenv("SNOW_PASS"),
        account=os.getenv("SNOW_ACCOUNT"),
        warehouse=os.getenv("SNOW_WAREHOUSE"),
        database=os.getenv("SNOW_DATABASE"),
        schema=os.getenv("SNOW_SCHEMA")
    )

# Expose a simple wrapper to generate the semantic model dynamically when enabled
from backend.app.utils.semantic_generator import generate_semantic_model

def generate_semantic_model():
    if not USE_SNOWFLAKE:
        raise RuntimeError("Cannot generate semantic model without Snowflake connection")
    return generate_semantic_model(os.getenv("SNOW_USER"), os.getenv("SNOW_PASS"), os.getenv("SNOW_ACCOUNT"), os.getenv("SNOW_WAREHOUSE"), os.getenv("SNOW_DATABASE"), os.getenv("SNOW_SCHEMA"))


