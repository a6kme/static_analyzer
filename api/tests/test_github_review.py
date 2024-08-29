import unittest

from api.src.analyzer import StaticAnalyzer
from api.src.config import AppConfig
from api.src.models import GithubRepo
from api.src.services import GithubService
from api.tests import test_vcr


class TestGithubReview(unittest.TestCase):

    def test_github_review(self):
        config = AppConfig.get_config()
        repo = GithubRepo(name='pygoat', owner='adeyosemanputra')
        with test_vcr.use_cassette('github_pull_request.yaml'):
            pr = GithubService(config).get_pull_request(repo, 11)
        StaticAnalyzer(config).static_review(pr)
        file_name = 'pygoat/introduction/views.py'
        file = next((f for f in pr.files if f.filename == file_name), None)

        # Ensure that reviews have been populated
        assert (len(file.reviews) > 0)
