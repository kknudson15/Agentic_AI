from .base_agent import BaseAgent
from .fix_agent import FixAgent

class RuleAgent(BaseAgent):
    async def receive_message(self, message):
        rules = message["rules"]
        # pass data + rules to FixAgent
        return await self.broker.send("FixAgent", message)