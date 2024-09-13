import json
from typing import List

from api.src.config import AppConfig
from api.src.logger import logger
from api.src.models import GithubRepo, Models
from api.src.services.github import GithubService
from api.src.services.llm import LLMService
from api.src.services.predict_review import PredictReviewService


def get_pr_from_dataset_id(dataset_id: str):
    # FIXME: assuming no underscores in the repo owner and repo name, which is wrong
    repo_owner, repo_name, pr_id = dataset_id.split('_')
    pr_id = int(pr_id)
    repo = GithubRepo(owner=repo_owner, name=repo_name)
    pr = GithubService(AppConfig.get_config()).get_pull_request(repo, pr_id)
    return pr


def get_dataset():
    with open('api/evaluate/dataset.jsonl') as f:
        for line in f:
            data_row = json.loads(line)
            pr = get_pr_from_dataset_id(data_row['id'])
            for review in data_row['reviews']:
                filename = review['filename']
                file = next(
                    (file for file in pr.files if file.filename == filename), None)

                # return file diff and reviews as ground truth
                yield file.patch, review['reviews']


def evaluate(model: Models, llm_service: LLMService, user_prompt_file: str):
    for file_patch, reviews in get_dataset():
        predicted_reviews = PredictReviewService(
            model=model.value).predict_from_patch(file_patch)

        # TODO: Will need to fix how the dataset is being generated to simplify the data generation
        # process. Its better to have trivial one dataset per line rather than having fancy structure
        # currently, just writing the ground truth and prediction to calculate the scores. Later, can
        # add Provenance information to the results to make it more useful for debugging and analysis
        with open('api/evaluate/results.jsonl', 'a') as f:
            f.write(json.dumps({
                'ground_truth': reviews,
                'predictions': [review.model_dump() for review in predicted_reviews.reviews],
                'model': model.value
            }) + '\n')


if __name__ == '__main__':
    config = AppConfig.get_config()
    llm_service = LLMService(traj_dir='api/evaluate/trajectories')
    models: List[Models] = config.evaluate.get('models', [])
    for model in models:
        evaluate(
            model,
            llm_service,
            'api/evaluate/prompts/review_with_patch.txt'
        )
