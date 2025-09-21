import asyncio

class MCPBroker:
    def __init__(self):
        self.agents = {}

    def register(self, name, agent):
        self.agents[name] = agent

    async def send(self, agent_name, message):
        agent = self.agents.get(agent_name)
        if agent:
            return await agent.receive_message(message)
        else:
            return {"error": f"Agent {agent_name} not found"}