import json
import logging
import os
from datetime import datetime

from litellm import InternalServerError, completion, completion_cost
from tenacity import (before_sleep_log, retry, retry_if_exception_type,
                      stop_after_attempt, wait_exponential)

from api.src.logger import DEBUG, logger
from api.src.models import Models


class LLMService:

    def __init__(self, traj_dir: str = 'trajectories') -> None:
        os.makedirs(traj_dir, exist_ok=True)
        current_time = datetime.now()
        self.traj_file_path = f'{traj_dir}/traj_{current_time.strftime("%Y-%m-%d_%H-%M")}.jsonl'

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(InternalServerError),
        before_sleep=before_sleep_log(logger, logging.DEBUG)
    )
    def completion(self, model: Models, messages, temperature: float = 0.0):
        """
            Get the completion from the model
        """
        response = completion(
            model=model.value,
            messages=messages,
            temperature=temperature
        )
        response_content = response.choices[0].message.content

        if DEBUG:
            with open(self.traj_file_path, 'a') as traj_file_obj:
                traj_file_obj.write(json.dumps({
                    'messages': messages,
                    'response': response_content,
                    'model': model.value,
                    'cost': completion_cost(response),
                    'usage': {
                        'prompt_tokens': response.usage.prompt_tokens,
                        'completion_tokens': response.usage.completion_tokens
                    }
                }) + '\n')
        return response_content
