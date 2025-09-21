from .base_agent import BaseAgent
from .rule_agent import RuleAgent

class ScannerAgent(BaseAgent):
    async def receive_message(self, message):
        # For demo, just pass rules to RuleAgent
        rules = "Check nulls, duplicates, ranges"
        return await self.broker.send("RuleAgent", {"data": message["data"], "rules": rules, "db_choice": message.get("db_choice"), "auth_type": message.get("auth_type"), "creds": message.get("creds")})