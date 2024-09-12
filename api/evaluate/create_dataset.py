import json
from typing import List

import tqdm
from pydantic import BaseModel

from api.src.config import AppConfig
from api.src.logger import logger
from api.src.models import GithubRepo
from api.src.services.analyzer import StaticAnalyzerService
from api.src.services.github import GithubService


def model_dump(objs: List[BaseModel] = [], mode='json', include=None):
    return [obj.model_dump(mode=mode, include=include) for obj in objs]


class GenerateDataset:

    def __init__(
        self,
        repo: GithubRepo,
        max_pr: int = 1,
        pr_ids: list | None = None,
        dataset_file_path: str = None,
        dataset_append_only: bool = False
    ) -> None:
        """
        @param repo: GithubRepo
        @param max_pr: int Maximum number of PRs to include in the dataset from the repo
        @param pr_ids: list List of PR IDs to include in the dataset
        """
        self.repo = repo
        self.max_pr = max_pr
        self.pr_ids = pr_ids
        self.dataset_file_path = dataset_file_path or 'api/evaluate/dataset.jsonl'
        self.dataset_append_only = dataset_append_only

    def generate(self):
        """
            Generate dataset for the PRs in the repo
        """
        config = AppConfig.get_config()

        file_open_mode = 'a' if self.dataset_append_only else 'w'
        dataset_file = open(self.dataset_file_path, file_open_mode)

        if not self.pr_ids:
            self.pr_ids = GithubService(
                config).get_pull_request_ids(self.repo, self.max_pr)

        logger.info(f"Generating dataset for {len(self.pr_ids)} PRs")

        for pr_id in tqdm.tqdm(self.pr_ids):
            # Also check if the PR is already present in the dataset
            # if yes, skip it

            pr_reviews = []
            logger.debug(
                f"Generating dataset for repo: {self.repo.owner}/{self.repo.name} for PR ID: {pr_id}")
            pr = GithubService(config).get_pull_request(self.repo, pr_id)
            StaticAnalyzerService(config).static_review(pr, diff=True)

            # Collect the static reviews for the given PR
            for file in pr.files:
                file_reviews = []
                for review in file.reviews:
                    file_reviews.append(review.model_dump(include=[
                        'issue_text', 'line_number', 'cwe', 'severity', 'confidence'
                    ]))
                if file_reviews:
                    pr_reviews.append({
                        'filename': file.filename,
                        'language': file.language,
                        'reviews': file_reviews
                    })

            # Write the reviews to the dataset file
            if pr_reviews:
                dataset_file.write(json.dumps({
                    'id': f"{self.repo.owner}_{self.repo.name}_{pr_id}",
                    'reviews': pr_reviews
                }) + '\n')

        dataset_file.flush()
        dataset_file.close()


def create_dataset():
    # Using two PRs for now, which can be extended to more PRs once plumbing is setup
    repos = [
        GithubRepo(name='pygoat', owner='adeyosemanputra'),
        GithubRepo(name='juice-shop', owner='juice-shop')
    ]
    for repo in repos:
        GenerateDataset(repo, max_pr=20, dataset_append_only=True).generate()


if __name__ == '__main__':
    create_dataset()
