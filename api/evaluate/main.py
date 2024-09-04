import json

from litellm import completion

from api.src.config import AppConfig


def get_dataset():
    with open('api/evaluate/dataset.json') as f:
        data = f.readline()
        yield json.loads(data)


system_prompt = open('api/evaluate/prompts/system.txt', 'r').read()
zero_shot_prompt = open('api/evaluate/prompts/zero_shot.txt', 'r').read()


def evaluate(model):
    for data in get_dataset():
        user_prompt = zero_shot_prompt.format(
            language='python', code=data['code'])
        messages = [
            {
                'role': 'system',
                'content': system_prompt
            },
            {
                'role': 'user',
                'content': data['code']
            }
        ]
        response = completion(model, messages)


if __name__ == '__main__':
    config = AppConfig.get_config()
    models = config.evaluate.get('models', [])
    for model in models:
        evaluate(model)
