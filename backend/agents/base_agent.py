from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Any, TypeVar, Generic, Optional
import logging
import time
import asyncio


class AgentStatus:
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


class AgentResult(BaseModel):
    status: str
    output: Optional[dict] = None
    error: Optional[str] = None
    execution_time_seconds: float = 0.0
    retry_count: int = 0


class BaseAgent(ABC):
    """Abstract base class for all ResearchPilot agents."""

    def __init__(self, name: str, llm_service=None, config: dict = {}):
        self.name = name
        self.llm = llm_service
        self.config = config
        self.logger = logging.getLogger(f"agent.{name}")
        self.status = AgentStatus.IDLE
        self.max_retries = config.get("max_retries", 2)

    async def execute(self, input_data: Any) -> AgentResult:
        """Execute with retry logic and timing."""
        start = time.time()
        self.status = AgentStatus.RUNNING
        retry_count = 0

        while retry_count <= self.max_retries:
            try:
                self.logger.info(f"[{self.name}] Executing (attempt {retry_count + 1})")
                output = await self.run(input_data)
                validated = await self.validate(output)
                self.status = AgentStatus.SUCCESS

                output_dict = validated.model_dump() if hasattr(validated, "model_dump") else validated
                return AgentResult(
                    status=AgentStatus.SUCCESS,
                    output=output_dict,
                    execution_time_seconds=time.time() - start,
                    retry_count=retry_count,
                )
            except Exception as e:
                retry_count += 1
                self.logger.error(f"[{self.name}] Error: {e} (retry {retry_count})")
                self.status = AgentStatus.RETRYING
                if retry_count > self.max_retries:
                    self.status = AgentStatus.FAILED
                    return AgentResult(
                        status=AgentStatus.FAILED,
                        error=str(e),
                        execution_time_seconds=time.time() - start,
                        retry_count=retry_count,
                    )
                await asyncio.sleep(2 ** retry_count)

        return AgentResult(
            status=AgentStatus.FAILED,
            error="Max retries exceeded",
            execution_time_seconds=time.time() - start,
            retry_count=retry_count,
        )

    @abstractmethod
    async def run(self, input_data: Any) -> Any:
        """Core agent logic — must be implemented by subclasses."""
        ...

    async def validate(self, output: Any) -> Any:
        """Optional validation hook. Override for custom validation."""
        return output

    def get_system_prompt(self) -> str:
        """Return the agent's system prompt."""
        return ""
