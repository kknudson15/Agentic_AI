from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task


@CrewBase
class DataInsightTeam():
    """DataInsightTeam crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def ingestion_agent(self) -> Agent:
      return Agent(
            config=self.agents_config['ingestion_agent'],
            verbose=True,
            allow_code_execution=True,
            code_execution_mode="safe",  # Uses Docker for safety
            max_execution_time=500, 
            max_retry_limit=1 
        )

    @agent
    def cleaning_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['cleaning_agent'],
            verbose=True,
            allow_code_execution=True,
            code_execution_mode="safe",  # Uses Docker for safety
            max_execution_time=500, 
            max_retry_limit=3 
        )

    @agent
    def analysis_agent(self) -> Agent:
      return Agent(
            config=self.agents_config['analysis_agent'],
            verbose=True,
        )

    @agent
    def executive_insights_agent(self) -> Agent:
      return Agent(
            config=self.agents_config['executive_insights_agent'],
            verbose=True,
        )

    @agent
    def presentation_agent(self) -> Agent:
      return Agent(
            config=self.agents_config['presentation_agent'],
            verbose=True,
            allow_code_execution=True,
            code_execution_mode="safe",  # Uses Docker for safety
            max_execution_time=500, 
            max_retry_limit=3 
        )

    @task
    def task_ingest (self) -> Task:
        return Task(
            config=self.tasks_config['task_ingest'], # type: ignore[index]
        )

    @task
    def task_clean (self) -> Task:
        return Task(
            config=self.tasks_config['task_clean'], # type: ignore[index]
        )

    @task
    def task_analyze (self) -> Task:
        return Task(
            config=self.tasks_config['task_analyze'], # type: ignore[index]
        )
    
    @task
    def task_insight (self) -> Task:
        return Task(
            config=self.tasks_config['task_insight'], # type: ignore[index]
        )

    @task
    def task_present (self) -> Task:
        return Task(
            config=self.tasks_config['task_present'], # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the DataInsightTeam crew"""

        return Crew(
            agents=self.agents, 
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
