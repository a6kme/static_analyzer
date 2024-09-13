import json
import re
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


def prepend_line_numbers_to_patch(patch: str):
    lines = patch.split('\n')
    return '\n'.join([f'{i + 1} {line}' for i, line in enumerate(lines)])


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
                yield pr, file, review['reviews']


def get_patch_line_to_hunk_line_mapping(patch: str):
    """
        We need to generate patch line number to hunk line number mapping to update the line numbers

        Example:
        @@ -10,3 +10,3 @@
        unchanged
        unchanged
        -line 1
        +line 2

        The mapping will be:
        {
            2: 10,
            3: 11,
            5: 12
        }

        The line numbers in the patch are 1-indexed, i.e the first line is line 1
    """
    lines = patch.splitlines()
    patch_line_to_hunk_line = {}
    line_num = 0

    # Generate a mapping from line number in the patch to line number in the updated file
    for patch_line_number, patch_line_content in enumerate(lines, start=1):
        # Handle the diff context lines (like @@ -1,3 +1,3 @@)
        if patch_line_content.startswith('@@'):
            # Extract the starting line number from the new file section
            match = re.match(r'@@ \-(\d+),\d+ \+(\d+),\d+ @@',
                             patch_line_content)
            if match:
                line_num = int(match.group(2)) - 1

        elif not patch_line_content.startswith('-') and not patch_line_content.startswith('+++'):
            # We will be considering unmodified lines as well as added lines. We will not consider removed lines
            line_num += 1
            patch_line_to_hunk_line[patch_line_number] = line_num

    return patch_line_to_hunk_line


def update_line_numbers(file, predicted_reviews):
    patch_line_to_hunk_line_mapping = get_patch_line_to_hunk_line_mapping(
        file.patch)

    predicted_reviews_list = []

    for review in predicted_reviews.reviews:
        predicted_review_dict = review.model_dump()
        patch_line_number = predicted_review_dict.pop('line_number')
        predicted_review_dict['patch_line_number'] = patch_line_number

        try:
            predicted_review_dict['line_number'] = patch_line_to_hunk_line_mapping[patch_line_number]
        except KeyError:
            logger.warning(
                f'Patch Line number {patch_line_number} not found in the updated file {file.filename}')
            predicted_review_dict['line_number'] = 0
        predicted_reviews_list.append(predicted_review_dict)

    return predicted_reviews_list


def evaluate(model: Models, llm_service: LLMService, user_prompt_file: str):
    for pr, file, reviews in get_dataset():
        file_patch = prepend_line_numbers_to_patch(file.patch)

        predicted_reviews = PredictReviewService(
            model=model.value).predict_from_patch(file_patch)

        # FIXME: There is no unique identifier for the result. If we want to have result for
        # different models in the same file, how will the unique ID work?

        # TODO: Will need to fix how the dataset is being generated to simplify the data generation
        # process. Its better to have trivial one dataset per line rather than having fancy structure
        # currently, just writing the ground truth and prediction to calculate the scores. Later, can
        # add Provenance information to the results to make it more useful for debugging and analysis

        # The line numbers generated in v1 are line numbers of the diff chunk. We need to retrieve
        # the line number of the updated file from the line number of the chunk
        predicted_reviews_list = update_line_numbers(file, predicted_reviews)

        with open('api/evaluate/results_v1.jsonl', 'a') as f:
            f.write(json.dumps({
                'repo': f'{pr.repo.owner}/{pr.repo.name}',
                'pr': pr.id,
                'filename': file.filename,
                'ground_truth': reviews,
                'predictions': predicted_reviews_list,
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
