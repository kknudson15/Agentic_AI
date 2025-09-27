import os
from dotenv import load_dotenv
import openai

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

class SummarizerAgent:
    def summarize(self, event):
        if not event["error"]:
            return "No incident.", "No next steps", "Low"

        prompt = f"""
        You are a data engineering assistant.
        Summarize this incident for a data engineer,
        classify severity (High, Medium, Low), and suggest next steps:

        Pipeline: {event['pipeline']}
        Task ID: {event['task_id']}
        Error: {event['error']}
        """
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        content = response.choices[0].message.content.strip()

        # Parse AI output for summary, next steps, severity
        # Expect format: Summary | Next Steps | Severity
        try:
            summary, next_steps, severity = [s.strip() for s in content.split("|")]
        except:
            summary = content
            next_steps = "Check logs and manual intervention"
            severity = "Medium"

        return summary, next_steps, severity