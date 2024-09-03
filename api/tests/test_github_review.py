import unittest

from api.src.analyzer import StaticAnalyzer
from api.src.config import AppConfig
from api.src.models import GithubRepo
from api.src.services import GithubService
from api.tests import test_vcr


class TestGithubReview(unittest.TestCase):

    def test_github_review_python(self):
        config = AppConfig.get_config()

        # Using a deliberate vulnerable codebase for testing
        # The project is listed on the OWASP Vulnerable Web Applications Directory (VWAD)
        # https://owasp.org/www-project-vulnerable-web-applications-directory
        repo = GithubRepo(name='pygoat', owner='adeyosemanputra')

        with test_vcr.use_cassette('github_pull_request.yaml'):
            pr = GithubService(config).get_pull_request(repo, 11)
        StaticAnalyzer(config).static_review(pr)
        file_name = 'pygoat/introduction/views.py'
        file = next((f for f in pr.files if f.filename == file_name), None)

        # Ensure that reviews have been populated
        assert (len(file.reviews) > 0)

    def test_github_review_js(self):
        config = AppConfig.get_config()

        # Using a deliberate vulnerable codebase for testing
        # The project is listed on the OWASP Vulnerable Web Applications Directory (VWAD)
        # https://owasp.org/www-project-vulnerable-web-applications-directory
        repo = GithubRepo(name='juice-shop', owner='juice-shop')

        with test_vcr.use_cassette('github_pull_request_js.yaml'):
            pr = GithubService(config).get_pull_request(repo, 35)
        StaticAnalyzer(config).static_review(pr)
        file_name = 'server.js'
        file = next((f for f in pr.files if f.filename == file_name), None)

        assert (len(file.reviews) > 0)
