from simulation.pipeline_simulator import simulate_pipeline_events
from agents.detector_agent import DetectorAgent
from agents.summarizer_agent import SummarizerAgent
from agents.recovery_agent import RecoveryAgent
from agents.validator_agent import ValidatorAgent
from agents.knowledge_base_agent import KnowledgeBaseAgent

detector = DetectorAgent()
summarizer = SummarizerAgent()
recovery = RecoveryAgent()
validator = ValidatorAgent()
kb = KnowledgeBaseAgent()

def process_event(event):
    if detector.detect(event):
        summary, next_steps, severity = summarizer.summarize(event)
        fix, retry_count = recovery.apply_fix(event)
        validation = validator.validate(event, fix)
        kb.log_incident(
            event,
            severity=severity,
            retry_count=retry_count,
            pipeline_type="ETL",
            source_system="Local",
            summary=summary,
            next_steps=next_steps,
            fix=fix,
            validation=validation
        )
        print(f"Incident processed: {event['task_id']} - {validation}")

def run_simulation():
    for event in simulate_pipeline_events(n=15, delay=1):
        process_event(event)

if __name__ == "__main__":
    run_simulation()