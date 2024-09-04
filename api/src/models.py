from enum import Enum
from typing import Any, ForwardRef, List, Literal

from pydantic import BaseModel


class GithubRepo(BaseModel):
    name: str
    owner: str


class Review(BaseModel):
    tool: str
    issue_text: str
    line_number: int
    file: 'File'
    pull_request: 'PullRequest'
    cwe: int
    severity: str
    confidence: str


class File(BaseModel):
    filename: str
    blob: str  # Contents of the file after applying commits in the PR
    patch: str  # Diff of the file after applying commits in the PR
    language: str
    reviews: List[Review] = []


class PullRequest(BaseModel):
    files: List[File] = []


class LanguageConfig(BaseModel):
    supported_tools: str


class PythonConfig(LanguageConfig):
    ...


class Config(BaseModel):
    supported_languages: str
    host_workspace_dir: str
    runtime_workspace_dir: str
    runtime_application_dir: str
    language: dict = {}
    evaluate: dict = {}


class Language(Enum):
    PYTHON = 'py'
    JAVASCRIPT = 'js'
    TYPESCRIPT = 'ts'


class Models(Enum):
    GPT4o = 'gpt-4o'
    Sonnet3_5 = 'claude-3-5-sonnet-20240620'
