from typing import List

from pydantic import BaseModel, Field

from api.src.models import Review


class Review(BaseModel):
    issue_text: str = Field(description='The CWE issue text')
    cwe: str = Field(description='The CWE number')
    line_number: str = Field(
        description='The line number of the issue in the code')


class LLMReviewResponse(BaseModel):
    thought: str = Field(
        description='Step by step thought process to generate the reviews')
    reviews: List[Review] = []
