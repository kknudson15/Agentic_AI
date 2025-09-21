class BaseAgent:
    def __init__(self, name, broker):
        self.name = name
        self.broker = broker
        self.broker.register(name, self)

    async def call_openai(self, prompt):
        # Placeholder for OpenAI API call
        return "# OpenAI generated code or text"

    async def receive_message(self, message):
        raise NotImplementedError