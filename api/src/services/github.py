import os
import subprocess
from urllib.parse import parse_qs, urlparse

import requests
from github import Auth as GithubAuth
from github import Github

from api.src.logger import logger
from api.src.models import Config, File, GithubRepo, PullRequest

token = os.environ.get('GITHUB_TOKEN')


class GithubService:
    def __init__(self, config: Config) -> None:
        self.config = config
        if not token:
            logger.info(
                "Github Token is not set. Strict rate limits from Github will apply."
            )
            self.github = Github()
        else:
            auth = GithubAuth.Token(token)
            self.github = Github(auth=auth)

    def get_pull_request(self, repo: GithubRepo, pr_number: int) -> PullRequest:
        g_repo = self.github.get_repo(f'{repo.owner}/{repo.name}')
        g_pr = g_repo.get_pull(pr_number)
        g_files_changed = g_pr.get_files()

        pr = PullRequest()
        pr.repo = repo
        pr.base = g_pr.base.sha

        pr.diff = self._get_diff(g_pr.diff_url)

        for file_changed in g_files_changed:
            if file_changed.filename.endswith(tuple(self.config.supported_languages)) \
                    and file_changed.patch is not None:
                self._add_file_content(pr, file_changed, g_repo)
        return pr

    def get_pull_request_ids(self, repo: GithubRepo, max_pr: int) -> list:
        g_repo = self.github.get_repo(f'{repo.owner}/{repo.name}')
        branches = g_repo.get_branches()

        # Get the main branch
        main_branch = next(
            (branch for branch in branches if branch.name in ['main', 'master']), None)

        g_prs = g_repo.get_pulls(
            state='closed', sort='created', base=main_branch.name)

        pr_ids = []
        for pr in g_prs:
            # Only consider merged PRs
            if pr.merged:
                pr_ids.append(pr.number)
                if len(pr_ids) >= max_pr:
                    break
        return pr_ids

    def _add_file_content(self, pr: PullRequest, file_changed, g_repo):
        contents_url = file_changed.contents_url
        ref = parse_qs(urlparse(contents_url).query)['ref'][0]
        file_content = g_repo.get_contents(file_changed.filename, ref=ref)
        file_content = file_content.decoded_content.decode('utf-8')

        file = File(
            filename=file_changed.filename,
            blob=file_content,
            patch=file_changed.patch,
            language=self._get_language(file_changed.filename)
        )
        pr.files.append(file)

    def _get_language(self, filename: str) -> str:
        if filename.endswith('.py'):
            return 'python'
        elif filename.endswith('.js'):
            return 'javascript'
        elif filename.endswith('.ts'):
            return 'typescript'
        else:
            raise ValueError(f"Unsupported language for file: {filename}")

    def _get_diff(self, diff_url: str) -> str:
        headers = {
            'Accept': 'application/vnd.github.v3.diff',
        }
        response = requests.get(diff_url, headers=headers)
        return response.text

    def _clone_repo(self, repo: GithubRepo, checkout_path: str = None, base_sha: str = None) -> None:
        clone_url = f"https://github.com/{repo.owner}/{repo.name}.git"

        try:
            # Clone the repository
            subprocess.run(["git", "clone", clone_url,
                           checkout_path], check=True)

            # Change directory to the cloned repo
            ret = subprocess.run(
                ["git", "checkout", base_sha],
                cwd=checkout_path,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if ret.returncode != 0:
                raise subprocess.CalledProcessError(
                    ret.returncode, ret.args, output=ret.stdout, stderr=ret.stderr)

            logger.info(
                f"Successfully cloned {repo.name} and checked out commit {base_sha}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error during git operations: {e}")

    def _apply_diff(self, checkout_dir, diff_text):
        try:
            ret = subprocess.run(
                ["git", "apply", "--reject", "-"],
                cwd=checkout_dir,
                input=diff_text,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if ret.returncode != 0:
                raise subprocess.CalledProcessError(
                    ret.returncode, ret.args, output=ret.stdout, stderr=ret.stderr)

            logger.info(f"Successfully applied diff to {checkout_dir}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error during git operations: {e}")
