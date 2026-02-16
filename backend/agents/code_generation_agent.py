import logging
from agents.base_agent import BaseAgent
from models.code import CodePrototype, CodeFile

logger = logging.getLogger("agent.code_generation")


class CodeGenerationAgent(BaseAgent):
    """Agent 7: Code Generation — generates prototype implementation code."""

    def __init__(self, llm_service):
        super().__init__("code_generation", llm_service)

    async def run(self, input_data) -> CodePrototype:
        if hasattr(input_data, "model_dump"):
            knowledge = input_data.model_dump()
        else:
            knowledge = input_data

        methodology = knowledge.get("methodology", {})
        algorithms = methodology.get("algorithms", [])
        approach = methodology.get("approach", "")
        steps = methodology.get("steps", [])
        model_arch = methodology.get("model_architecture", "")

        prompt = f"""You are a research software engineer. Generate a Python prototype implementation based on this paper's methodology.

METHODOLOGY:
Approach: {approach}
Steps: {steps}
Algorithms: {algorithms}
Model Architecture: {model_arch or 'Not specified'}

Problem: {knowledge.get('problem_statement', '')}
Datasets: {knowledge.get('datasets', [])}

Generate a complete, runnable Python prototype. Return a JSON object with:
- language: "python"
- files: Array of objects with: filename, content (the actual Python code), description
  Include at minimum:
  1. main.py - Core implementation of the methodology
  2. model.py - Model/algorithm implementation (if applicable)
  3. utils.py - Helper functions
- requirements: Array of Python package names needed
- readme_content: A README.md explaining how to run the prototype
- architecture_description: Brief description of the code architecture"""

        result = await self.llm.generate_json(prompt)

        files = []
        for f in result.get("files", []):
            files.append(CodeFile(
                filename=f.get("filename", "main.py"),
                content=f.get("content", "# No code generated"),
                description=f.get("description", ""),
            ))

        if not files:
            files = [CodeFile(
                filename="main.py",
                content="# Prototype implementation\n# Based on the paper's methodology\nprint('Hello, Research!')",
                description="Main implementation file",
            )]

        return CodePrototype(
            language=result.get("language", "python"),
            files=files,
            requirements=result.get("requirements", ["numpy", "torch"]),
            readme_content=result.get("readme_content", "# Prototype\nRun `python main.py`"),
            architecture_description=result.get("architecture_description", ""),
        )
