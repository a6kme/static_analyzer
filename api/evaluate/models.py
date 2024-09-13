from typing import List

from pydantic import BaseModel, Field

from api.src.models import Review


class Review(BaseModel):
    issue_text: str = Field(description='The CWE issue text')
    cwe: int = Field(description='The CWE vulnerability number')
    line_number: int = Field(
        description='The line number of the issue in the code')
    severity: str = Field(description='The severity of the issue')


class LLMReviewResponse(BaseModel):
    thought: str = Field(
        description='Step by step thought process to generate the reviews')
    reviews: List[Review] = []
