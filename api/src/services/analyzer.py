import abc
import glob
import json
import os
import re
import shutil
from collections import defaultdict
from typing import List

import docker

from api.src.models import Config, Language, PullRequest, Review


class StaticAnalyzerService:

    def __init__(self, config: Config) -> None:
        self.config = config

    def static_review(self, pr: PullRequest, diff: bool = False) -> List[Review]:
        """
            Do a static analysis of the pull request and populate the PR files with reviews
            @param pr: PullRequest
            @param diff: bool - whether to analyze the diff or the whole file hunks
        """
        self.get_reviews_from_runtime(pr, diff)

    def get_reviews_from_runtime(self, pr: PullRequest, diff: bool = False) -> List[Review]:
        """
            Get reviews from runtime
            @param pr: PullRequest
            @param diff: bool - whether to analyze the diff or the whole file hunks
        """
        # ensure that the workspace directory exists and is empty
        shutil.rmtree(self.config.host_workspace_dir, ignore_errors=True)
        os.makedirs(self.config.host_workspace_dir, exist_ok=True)

        # write updated files content (after applying the PR commits) to workspace directory
        self._write_file_blobs_to_workspace(pr)

        # Create results.jsonl file in the workspace directory which can act as a shared space
        # between writing and reading the reviews
        open(f'{self.config.host_workspace_dir}/results.jsonl', 'w').close()

        # Run the static analysis tools using runtime environment for each language
        for language in self.config.language.keys():
            if self._is_language_in_workspace(language):
                self._analyze_workspace_for_language(language)

        # Dedupe the results from the runtime
        self._dedupe_runtime_results()

        # Parse the results from the runtime exported in workspace directory and
        # populate the PR files with reviews
        self._parse_runtime_results(pr, diff)

    def _analyze_workspace_for_language(self, language):
        # Run the static analysis tool for the language
        if language == Language.PYTHON.value:
            self._run_python_static_analysis()
        elif language in (Language.JAVASCRIPT.value, Language.TYPESCRIPT.value):
            self._run_js_static_analysis()

    def _run_python_static_analysis(self):
        # Run a container with the directory mounted
        # if python:
        image_name = 'a6kme/static-analyzer-py'
        command = f'python {self.config.runtime_application_dir}/api/runtime/py/main.py' + ' ' + \
            f'-t {self.config.language[Language.PYTHON.value]["supported_tools"]}'

        self._start_runtime(image_name, command)

    def _run_js_static_analysis(self):
        # Run a container with the directory mounted
        # if javascript or typescript:
        image_name = 'a6kme/static-analyzer-js'
        command = f'python {self.config.runtime_application_dir}/api/runtime/js/main.py' + ' ' + \
            f'-t {self.config.language[Language.JAVASCRIPT.value]["supported_tools"]}'

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

    def _parse_runtime_results(self, pr: PullRequest, diff: bool = False):
        filename_to_file_map = {file.filename: file for file in pr.files}

        # map the filename to the changed lines in the diff
        filename_to_line_annotations_map = defaultdict(dict)

        with open(f'{self.config.host_workspace_dir}/results.jsonl', 'r') as f:
            for review_line in f:
                review = json.loads(review_line)
                # since the file path is relative to the workspace directory in the runtime, we
                # need to strip that off to get the file name
                file_name = re.sub(
                    r'^\/?' + self.config.runtime_workspace_dir + r'\/', '', review['file'])
                file = filename_to_file_map[file_name]

                # if diff is True, then we need to check if the review line is in the diff
                if diff and file.patch:
                    if file_name not in filename_to_line_annotations_map:
                        filename_to_line_annotations_map[file_name] = self._line_annotations_from_patch(
                            file.patch)

                    # If the line is not changed in the diff, then skip the review
                    if not filename_to_line_annotations_map[file_name].get(review['line'], False):
                        continue

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

    def _dedupe_runtime_results(self):
        # TODO: Figure out better complexity than O(n^2)
        unique_results = []
        unique_result_keys = set()
        with open(f'{self.config.host_workspace_dir}/results.jsonl', 'r') as f:
            for review in f:
                review_dict = json.loads(review)

                # Dedupe the results based on the file, line number and CWE since
                # different issue text can be generated for same CWE by different analysis tools or rulesets
                unique_key = f"{review_dict['file']}_{review_dict['line']}_{review_dict['cwe']}"
                if unique_key not in unique_result_keys:
                    unique_results.append(review)
                    unique_result_keys.add(unique_key)

        # override the results file with the deduped results
        with open(f'{self.config.host_workspace_dir}/results.jsonl', 'w') as f:
            for review in unique_results:
                f.write(review)

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

    def _line_annotations_from_patch(self, patch: str):
        """
            Parse the patch and return the line numbers that have been added or modified
            TODO: Not sure if this is the right place for this function
        """
        lines = patch.splitlines()
        line_annotations = {}
        line_num = 0
        for line in lines:
            # Handle the diff context lines (like @@ -1,3 +1,3 @@)
            if line.startswith('@@'):
                # Extract the starting line number from the new file section
                match = re.match(r'@@ \-(\d+),\d+ \+(\d+),\d+ @@', line)
                if match:
                    line_num = int(match.group(2)) - 1
            elif line.startswith('+') and not line.startswith('+++'):
                line_num += 1
                line_annotations[line_num] = True
            elif line.startswith('-') and not line.startswith('---'):
                # Skip lines removed from the original file
                continue
            else:
                line_num += 1
                line_annotations[line_num] = False

        return line_annotations
