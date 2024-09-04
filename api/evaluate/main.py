import json
import re
from typing import List

from langchain.output_parsers import PydanticOutputParser

from api.evaluate.models import LLMReviewResponse
from api.src.config import AppConfig
from api.src.llm import LLMService
from api.src.logger import logger
from api.src.models import Models


def get_dataset():
    with open('api/evaluate/dataset.jsonl') as f:
        for line in f:
            yield json.loads(line)


system_prompt = open('api/evaluate/prompts/system.txt', 'r').read()
zero_shot_prompt = open('api/evaluate/prompts/zero_shot.txt', 'r').read()


def parse_response(response):
    try:
        response = json.loads(response)
        return response
    except json.JSONDecodeError:
        # Fix some common issues
        response = re.sub(r'(^```json|```$)', '', response)

    try:
        response = json.loads(response)
        return response
    except json.JSONDecodeError:
        logger.error(f"Error in parsing response: {response}")
        return {'reviews': 'PARSE_ERROR'}


def evaluate(model: Models, llm_service: LLMService):
    for data in get_dataset():
        pydantic_parser = PydanticOutputParser(
            pydantic_object=LLMReviewResponse
        )
        user_prompt = zero_shot_prompt.format(
            language=data['language'],
            code=data['code'],
            format_instructions=pydantic_parser.get_format_instructions()
        )
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
        response = llm_service.completion(model, messages, temperature=0.0)

        # fix some common issues in response
        response = parse_response(response)

        with open('api/evaluate/results.jsonl', 'a') as f:
            f.write(json.dumps({
                'id': data['id'],
                'ground_truth': data['reviews'],
                'predictions': response['reviews'],
                'model': model.value
            }) + '\n')


if __name__ == '__main__':
    config = AppConfig.get_config()
    llm_service = LLMService(traj_dir='api/evaluate/trajectories')
    models: List[Models] = config.evaluate.get('models', [])
    for model in models:
        evaluate(model, llm_service)
