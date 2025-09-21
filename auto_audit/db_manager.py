import pandas as pd
from sqlalchemy import create_engine
import config
from snowflake.sqlalchemy import URL

class DBManager:
    def __init__(self, db_type=None, auth_type=None, creds=None):
        if db_type is None:
            db_type = config.DB_TYPE
        self.db_type = db_type

        if db_type == "sqlite":
            self.engine = create_engine(f"sqlite:///{config.SQLITE_PATH}")

        elif db_type == "snowflake":
            if creds is None:
                creds = config.SNOWFLAKE
            if auth_type is None:
                auth_type = creds.get("auth_type", config.SNOWFLAKE["auth_type"])

            if auth_type == "password":
                self.engine = create_engine(URL(
                    user=creds["user"],
                    password=creds["password"],
                    account=creds["account"],
                    warehouse=creds["warehouse"],
                    database=creds["database"],
                    schema=creds.get("schema", "PUBLIC")
                ))

            elif auth_type == "keypair":
                from cryptography.hazmat.primitives import serialization
                with open(creds["private_key_path"], "rb") as key:
                    p_key = serialization.load_pem_private_key(
                        key.read(),
                        password=creds["private_key_passphrase"].encode()
                        if creds.get("private_key_passphrase") else None,
                    )
                pkb = p_key.private_bytes(
                    encoding=serialization.Encoding.DER,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                )
                self.engine = create_engine(URL(
                    user=creds["user"],
                    account=creds["account"],
                    warehouse=creds["warehouse"],
                    database=creds["database"],
                    schema=creds.get("schema", "PUBLIC"),
                    authenticator="snowflake",
                    private_key=pkb
                ))

            elif auth_type == "oauth":
                self.engine = create_engine(URL(
                    user=creds["user"],
                    account=creds["account"],
                    warehouse=creds["warehouse"],
                    database=creds["database"],
                    schema=creds.get("schema", "PUBLIC"),
                    authenticator="oauth",
                    token=creds["oauth_token"]
                ))
            else:
                raise ValueError(f"Unsupported Snowflake auth_type: {auth_type}")

        else:
            raise ValueError(f"Unsupported DB_TYPE: {db_type}")

    def write_table(self, df: pd.DataFrame, table_name: str, replace=True):
        df.to_sql(
            table_name,
            con=self.engine,
            if_exists="replace" if replace else "append",
            index=False
        )

    def read_table(self, table_name: str, limit=5):
        query = f"SELECT * FROM {table_name} LIMIT {limit}"
        return pd.read_sql(query, self.engine).to_dict(orient="records")

    def copy_table(self, source: str, dest: str):
        with self.engine.connect() as conn:
            conn.execute(f"DROP TABLE IF EXISTS {dest}")
            conn.execute(f"CREATE TABLE {dest} AS SELECT * FROM {source}")