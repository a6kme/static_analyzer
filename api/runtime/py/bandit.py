import json
import logging
import os
import subprocess

from api.src.logger import logger


class BanditService:
    def __init__(self, workspace_dir) -> None:
        self.workspace_dir = workspace_dir

    def analyze(self, *args, **kwargs):
        # run bandit analysis on the file using shell
        try:
            files = os.listdir(self.workspace_dir)
            logger.debug("workspace directory: {}, files - {}",
                         self.workspace_dir, files[:5])
            result = subprocess.run(
                ["bandit", "-r", self.workspace_dir, "-f", "json"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            json_result = json.loads(result.stdout)
            return self.format_output(json_result)
        except subprocess.CalledProcessError as e:
            print(e.stderr)
            return None
        except json.JSONDecodeError as e:
            print(e)
            return None

    def format_output(self, json_result):
        output = []
        for result in json_result["results"]:
            output.append({
                'file': result['filename'],
                'line': result['line_number'],
                'cwe': result['issue_cwe']['id'],
                'severity': result['issue_severity'],
                'confidence': result['issue_confidence'],
                'issue_text': result['issue_text']
            })
        return output
