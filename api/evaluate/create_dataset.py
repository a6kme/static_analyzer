import json
from typing import List

import tqdm
from pydantic import BaseModel

from api.src.analyzer import StaticAnalyzer
from api.src.config import AppConfig
from api.src.logger import logger
from api.src.models import GithubRepo
from api.src.services import GithubService


def model_dump(objs: List[BaseModel] = [], mode='json', include=None):
    return [obj.model_dump(mode=mode, include=include) for obj in objs]


def create_dataset():
    # Using two PRs for now, which can be extended to more PRs once plumbing is setup
    data = [
        {
            'repo_owner': 'adeyosemanputra',
            'repo_name': 'pygoat',
            'files': ['pygoat/introduction/views.py'],
            'pr_number': 11
        },
        {
            'repo_owner': 'juice-shop',
            'repo_name': 'juice-shop',
            'files': ['server.js'],
            'pr_number': 35
        }
    ]

    config = AppConfig.get_config()
    dataset_file = open('api/evaluate/dataset.jsonl', 'w')
    logger.info(f"Generating dataset for {len(data)} PRs")
    for entry in tqdm.tqdm(data):
        logger.debug(
            f"Generating dataset for repo: {entry['repo_owner']}/{entry['repo_name']}")
        repo = GithubRepo(name=entry['repo_name'], owner=entry['repo_owner'])
        pr = GithubService(config).get_pull_request(repo, entry['pr_number'])
        StaticAnalyzer(config).static_review(pr)
        for file_name in entry['files']:
            file = next((f for f in pr.files if f.filename == file_name), None)
            reviews = file.reviews
            dataset_file.write(json.dumps({
                'id': f"{entry['repo_owner']}_{entry['repo_name']}_{entry['pr_number']}_{file_name}",
                'code': file.blob,
                'reviews': model_dump(
                    reviews,
                    include=['issue_text', 'line_number',
                             'cwe', 'severity', 'confidence']
                ),
                'language': file.language
            }) + '\n')
    dataset_file.flush()
    dataset_file.close()


if __name__ == '__main__':
    create_dataset()
