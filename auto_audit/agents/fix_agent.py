from .base_agent import BaseAgent
import pandas as pd
import io
from db_manager import DBManager
from .reporter_agent import ReporterAgent

class FixAgent(BaseAgent):
    async def receive_message(self, message):
        df_csv = message["data"]
        df = pd.read_csv(io.StringIO(df_csv))

        # Example: pretend OpenAI returns code that fixes nulls
        fixes_code = "df = df.fillna(0)"

        local_vars = {'df': df}
        exec(fixes_code, {}, local_vars)
        df_fixed = local_vars['df']

        db = DBManager(message.get("db_choice"), message.get("auth_type"), message.get("creds"))
        db.write_table(df, "original_data")
        db.write_table(df_fixed, "fixed_data")

        return await self.broker.send("ReporterAgent", {
            "rules": message.get("rules"),
            "fixes_code": fixes_code,
            "db_choice": message.get("db_choice"),
            "auth_type": message.get("auth_type"),
            "creds": message.get("creds")
        })