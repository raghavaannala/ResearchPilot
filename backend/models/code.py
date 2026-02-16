from pydantic import BaseModel


class CodeFile(BaseModel):
    filename: str
    content: str
    description: str = ""


class CodePrototype(BaseModel):
    language: str = "python"
    files: list[CodeFile] = []
    requirements: list[str] = []
    readme_content: str = ""
    architecture_description: str = ""
