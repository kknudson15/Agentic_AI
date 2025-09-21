from .base_agent import BaseAgent
from db_manager import DBManager

class ReporterAgent(BaseAgent):
    async def receive_message(self, message):
        db = DBManager(message.get("db_choice"), message.get("auth_type"), message.get("creds"))
        original = db.read_table("original_data", limit=5)
        fixed = db.read_table("fixed_data", limit=5)

        audit_report = f"Applied fixes: {message.get('fixes_code')}"

        return {
            "audit_report": audit_report,
            "original_preview": original,
            "fixed_preview": fixed,
            "fixes_code": message.get("fixes_code")
        }