from urllib.parse import parse_qs, urlparse

from github import Github

from api.src.models import Config, File, GithubRepo, PullRequest


class GithubService:
    def __init__(self, config: Config) -> None:
        self.config = config

    def get_pull_request(self, repo: GithubRepo, pr_number: int) -> PullRequest:
        github = Github()
        g_repo = github.get_repo(f'{repo.owner}/{repo.name}')
        g_pr = g_repo.get_pull(pr_number)
        g_files_changed = g_pr.get_files()

        pr = PullRequest()

        for file_changed in g_files_changed:
            if file_changed.filename.endswith(tuple(self.config.supported_languages)):
                self._add_file_content(pr, file_changed, g_repo)
        return pr

    def _add_file_content(self, pr: PullRequest, file_changed, g_repo):
        contents_url = file_changed.contents_url
        ref = parse_qs(urlparse(contents_url).query)['ref'][0]
        file_content = g_repo.get_contents(file_changed.filename, ref=ref)
        file_content = file_content.decoded_content.decode('utf-8')

        file = File(
            filename=file_changed.filename,
            blob=file_content,
            patch=file_changed.patch,
        )
        pr.files.append(file)
