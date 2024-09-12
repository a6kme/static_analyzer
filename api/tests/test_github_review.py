import unittest

from api.src.config import AppConfig
from api.src.models import GithubRepo
from api.src.services.analyzer import StaticAnalyzerService
from api.src.services.github import GithubService
from api.tests import test_vcr


class TestGithubReview(unittest.TestCase):

    def test_github_review_python(self):
        """
            Test the static review of a Python file
        """
        config = AppConfig.get_config()

        # Using a deliberate vulnerable codebase for testing
        # The project is listed on the OWASP Vulnerable Web Applications Directory (VWAD)
        # https://owasp.org/www-project-vulnerable-web-applications-directory
        repo = GithubRepo(name='pygoat', owner='adeyosemanputra')

        with test_vcr.use_cassette('github_pull_request.yaml'):
            pr = GithubService(config).get_pull_request(repo, 11)
        StaticAnalyzerService(config).static_review(pr)

        file_name = 'pygoat/introduction/views.py'
        file = next((f for f in pr.files if f.filename == file_name), None)

        # Ensure that reviews have been populated
        assert (len(file.reviews) > 0)

    def test_github_review_js(self):
        """
            Test the static review of a JavaScript file
        """
        config = AppConfig.get_config()

        # Using a deliberate vulnerable codebase for testing
        # The project is listed on the OWASP Vulnerable Web Applications Directory (VWAD)
        # https://owasp.org/www-project-vulnerable-web-applications-directory
        repo = GithubRepo(name='juice-shop', owner='juice-shop')

        with test_vcr.use_cassette('github_pull_request_js.yaml'):
            pr = GithubService(config).get_pull_request(repo, 35)
        StaticAnalyzerService(config).static_review(pr)
        file_name = 'server.js'
        file = next((f for f in pr.files if f.filename == file_name), None)

        assert (len(file.reviews) > 0)

    def test_github_review_with_diff(self):
        """
            Test the static review which only considers diff and not entire hunk
        """
        config = AppConfig.get_config()

        repo = GithubRepo(name='juice-shop', owner='juice-shop')

        with test_vcr.use_cassette('github_pull_request_with_diff.yaml'):
            pr_35 = GithubService(config).get_pull_request(repo, 35)
            pr_40 = GithubService(config).get_pull_request(repo, 40)

        # In https://github.com/juice-shop/juice-shop/pull/35/files, we don't have any vulnerability
        # in the diff of the file server.js. So, the reviews should be empty
        StaticAnalyzerService(config).static_review(pr_35, diff=True)
        file_name = 'server.js'
        file = next((f for f in pr_35.files if f.filename == file_name), None)
        assert (len(file.reviews) == 0)

        # In https://github.com/juice-shop/juice-shop/pull/40/files, we have new vulnerabilities
        # through the diff of the file middleware.js. So, the reviews should not be empty
        StaticAnalyzerService(config).static_review(pr_40, diff=True)
        file_name = 'middleware.js'
        file = next((f for f in pr_40.files if f.filename == file_name), None)
        assert (len(file.reviews) != 0)
