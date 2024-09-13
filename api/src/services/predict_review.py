from string import Template
from typing import List

from langchain.output_parsers import PydanticOutputParser

from api.evaluate.models import LLMReviewResponse
from api.src.models import File, PullRequest
from api.src.services.llm import LLMService


class PredictReviewService:

    def __init__(self, model: str = 'gpt-4o') -> None:
        self.model = model
        self.system_prompt_template = open(
            'api/evaluate/prompts/system.txt', 'r').read()
        self.user_prompt_template = open(
            'api/evaluate/prompts/review_with_patch.txt', 'r').read()

    def predict_from_patch(self, file_patch: str):
        """
            Take diff as input and predict reviews as per instructions given in 
            the user prompt template api/evaluate/prompts/review_with_patch.txt
        """
        parser = PydanticOutputParser(
            pydantic_object=LLMReviewResponse
        )
        user_message_template = Template(self.user_prompt_template)
        user_prompt = user_message_template.substitute(
            code_patch=file_patch,
            format_instructions=parser.get_format_instructions()
        )
        llm_response = self._get_llm_response(
            self.system_prompt_template, user_prompt)

        return parser.parse(llm_response)

    def _get_llm_response(self, system_prompt: str, user_prompt: str):
        # FIXME: Instantiating the LLM service every time leads to a new trajectory file
        # TODO: The trajectory file in the current shape is not very useful. Either similify
        # it or create a simple UI on top of it to extract relevant information
        llm_service = LLMService()
        messages = [
            {
                'role': 'system',
                'content': system_prompt
            },
            {
                'role': 'user',
                'content': user_prompt
            }
        ]
        return llm_service.completion(self.model, messages)
