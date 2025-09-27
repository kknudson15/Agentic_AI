import random
import time

PIPELINES = ["load_csv", "transform_data", "aggregate_table"]

ERRORS = [
    None,
    "Missing file",
    "Schema mismatch",
    "Null values in primary key",
]

def generate_pipeline_event():
    pipeline = random.choice(PIPELINES)
    task_id = f"{pipeline}_{random.randint(1,10)}"
    error = random.choice(ERRORS)
    return {
        "pipeline": pipeline,
        "task_id": task_id,
        "error": error,
        "timestamp": time.time()
    }

def simulate_pipeline_events(n=5, delay=2):
    for _ in range(n):
        event = generate_pipeline_event()
        yield event
        time.sleep(delay)