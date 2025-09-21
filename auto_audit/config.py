DB_TYPE = "sqlite"  # "sqlite" or "snowflake"

# SQLite config
SQLITE_PATH = "data/audit.db"

# Snowflake config (defaults if credentials not provided via UI)
SNOWFLAKE = {
    "auth_type": "password",  # options: "password", "keypair", "oauth"
    "user": "YOUR_USERNAME",
    "password": "YOUR_PASSWORD",
    "account": "YOUR_ACCOUNT_ID",
    "warehouse": "COMPUTE_WH",
    "database": "AUDIT_DB",
    "schema": "PUBLIC",
    "private_key_path": "rsa_key.p8",
    "private_key_passphrase": "mypassword",
    "oauth_token": None
}