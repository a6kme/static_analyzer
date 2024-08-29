import abc
import glob
import json
import os
import re
import shutil
from typing import List

import docker

from api.src.models import Config, Language, PullRequest, Review


class StaticAnalyzer:

    def __init__(self, config: Config) -> None:
        self.config = config

    def static_review(self, pr: PullRequest) -> List[Review]:
        """
            Do a static analysis of the pull request and populate the PR files with reviews
        """
        self.get_reviews_from_runtime(pr)

    def get_reviews_from_runtime(self, pr: PullRequest) -> List[Review]:
        """
            Get reviews from runtime
        """
        # ensure that the workspace directory exists and is empty
        shutil.rmtree(self.config.host_workspace_dir, ignore_errors=True)
        os.makedirs(self.config.host_workspace_dir, exist_ok=True)

        # write updated files content (after applying the PR commits) to workspace directory
        self._write_file_blobs_to_workspace(pr)

        # Run the static analysis tools using runtime environment
        for language in self.config.language.keys():
            if self._is_language_in_workspace(language):
                self._analyze_workspace_for_language(language)

        # Parse the results from the runtime exported in workspace directory and
        # populate the PR files with reviews
        self._parse_runtime_results(pr)

    def _analyze_workspace_for_language(self, language):
        # Run the static analysis tool for the language
        if language == Language.PYTHON.value:
            self._run_python_static_analysis()

        # ToDo: Support more languages

    def _run_python_static_analysis(self):
        # Run a container with the directory mounted
        # if python:
        image_name = 'a6kme/static-analyzer-py'
        command = f'python {self.config.runtime_application_dir}/api/runtime/py/main.py' + ' ' + \
            f'-t {self.config.language[Language.PYTHON.value]["supported_tools"]}'

        self._start_runtime(image_name, command)

    def _start_runtime(self, image_name, command):
        # Run the python static analysis tool
        # Send the context to the runtime
        client = docker.from_env()

        workspace_dir_abs_path = os.path.abspath(
            self.config.host_workspace_dir)
        application_dir_abs_path = os.path.abspath('api')

        # write the results in workspace_dir/<tool>.json
        run_result = client.containers.run(
            image_name,
            volumes={
                workspace_dir_abs_path: {
                    'bind': f'/{self.config.runtime_workspace_dir}', 'mode': 'rw'
                },
                application_dir_abs_path: {
                    'bind': f'/{self.config.runtime_application_dir}/api', 'mode': 'rw'
                }
            },
            environment={
                'PYTHONPATH': f'/{self.config.runtime_application_dir}'},
            name='static_analyzer',
            command=command,
            remove=True,
            stdout=True,  # Capture stdout
            stderr=True,   # Capture stderr
        )
        return run_result

    def _parse_runtime_results(self, pr: PullRequest):
        filename_to_file_map = {file.filename: file for file in pr.files}
        with open(f'{self.config.host_workspace_dir}/results.jsonl', 'r') as f:
            for review_line in f:
                review = json.loads(review_line)
                # since the file path is relative to the workspace directory in the runtime, we
                # need to strip that off to get the file name
                file_name = re.sub(
                    r'^\/?' + self.config.runtime_workspace_dir + r'\/', '', review['file'])
                file = filename_to_file_map[file_name]
                file.reviews.append(Review(
                    tool=review['tool'],
                    issue_text=review['issue_text'],
                    line_number=review['line'],
                    file=file,
                    pull_request=pr,
                    cwe=review['cwe'],
                    severity=review['severity'],
                    confidence=review['confidence']
                ))

    def _write_file_blobs_to_workspace(self, pr: PullRequest):
        workspace_dir = self.config.host_workspace_dir
        for file in pr.files:
            os.makedirs(
                f'{workspace_dir}/{os.path.dirname(file.filename)}', exist_ok=True)
            with open(f'{workspace_dir}/{file.filename}', 'w') as f:
                f.write(file.blob)

    def _is_language_in_workspace(self, language):
        # scan for files with language extention in the workspace
        search_pattern = os.path.join(
            self.config.host_workspace_dir, '**', f'*.{language}')
        if glob.glob(search_pattern, recursive=True):
            return True
