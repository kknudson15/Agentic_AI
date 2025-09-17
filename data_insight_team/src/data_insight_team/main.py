#!/usr/bin/env python
import sys
import warnings
import pandas as pd

from datetime import datetime
from crew import DataInsightTeam

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def run():
    """
    Run the crew.
    """
    dataset_path = "sales_data_q3.csv"
    inputs={"data_set": dataset_path}
    
    try:
        return DataInsightTeam().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")

if __name__ == "__main__":
    result = run()

    print("\n--- Final Executive Briefing ---\n")
    print(result)