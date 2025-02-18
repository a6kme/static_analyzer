import json
import re
import subprocess


class SemgrepService:
    def __init__(self, workspace_dir, rulesets=['p/security-audit']) -> None:
        self.workspace_dir = workspace_dir
        self.rulesets = rulesets

    def analyze(self):
        # generate configuration for rulesets
        ruleset_config = []
        for ruleset in self.rulesets:
            ruleset_config.append('--config')
            ruleset_config.append(ruleset)

        # run semgrep analysis on the file using shell

        try:
            result = subprocess.run(
                ["semgrep", "--json"] + ruleset_config + [self.workspace_dir],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            json_result = json.loads(result.stdout)
            return self.format_output(json_result['results'])
        except subprocess.CalledProcessError as e:
            print(e.stderr)
            return None
        except json.JSONDecodeError as e:
            print(e)
            return None

    def format_output(self, json_result):
        output = []
        for result in json_result:
            metadata = result['extra']['metadata']

            cwe_ids = []

            # extract CWE ids from the metadata
            for cwe in metadata['cwe']:
                cwe_id = re.search('CWE-(\d+)', cwe).group(1)
                cwe_ids.append(cwe_id)

            output.append({
                'file': result['path'],
                'line': result['start']['line'],
                'cwe': ', '.join(cwe_ids),
                'severity': metadata['impact'],
                'confidence': metadata['confidence'],
                'issue_text': result['extra']['message']
            })
        return output
