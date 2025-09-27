from prefect import flow, task
from agents.detector_agent import DetectorAgent
from agents.summarizer_agent import SummarizerAgent
from agents.recovery_agent import RecoveryAgent
from agents.validator_agent import ValidatorAgent
from agents.knowledge_base_agent import KnowledgeBaseAgent
import time
import random

# Initialize agents
detector = DetectorAgent()
summarizer = SummarizerAgent()
recovery = RecoveryAgent()
validator = ValidatorAgent()
kb = KnowledgeBaseAgent()

# ---------------------------
# ETL Task (Prefect Task)
# ---------------------------
@task(retries=1, retry_delay_seconds=30)  # automatic retry for transient errors
def etl_task(pipeline_name, task_id):
    """
    Represents one ETL task in Prefect flow.
    """
    # Simulate ETL logic
    time.sleep(1)

    # Simulate random errors (replace with real ETL code)
    error = None
    if random.random() < 0.3:
        error = random.choice([
            "Missing file",
            "Schema mismatch",
            "Null values detected"
        ])

    event = {
        "pipeline": pipeline_name,
        "task_id": task_id,
        "timestamp": time.time(),
        "error": error
    }

    if detector.detect(event):
        summary, next_steps, severity = summarizer.summarize(event)
        fix, retry_count = recovery.apply_fix(event)
        validation = validator.validate(event, fix)

        kb.log_incident(
            event,
            severity=severity,
            retry_count=retry_count,
            pipeline_type="ETL",
            source_system="Production",
            summary=summary,
            next_steps=next_steps,
            fix=fix,
            validation=validation
        )
        return {"task_id": task_id, "status": validation}
    else:
        # Success case
        kb.log_incident(
            event,
            severity="Low",
            retry_count=0,
            pipeline_type="ETL",
            source_system="Production",
            summary="No incident",
            next_steps="None",
            fix="None",
            validation="Success"
        )
        return {"task_id": task_id, "status": "Success"}

# ---------------------------
# Prefect Flow
# ---------------------------
@flow(name="ETL Prefect Flow")
def etl_flow():
    pipelines = ["pipeline_A", "pipeline_B", "pipeline_C"]
    results = []
    for pipeline in pipelines:
        for i in range(3):  # multiple tasks per pipeline
            results.append(etl_task(pipeline, f"{pipeline}_task_{i+1}"))
    return results

# ---------------------------
# Run flow if executed directly
# ---------------------------
if __name__ == "__main__":
    etl_flow()