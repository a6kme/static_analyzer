
# Command line arguments
# noqa
import argparse
import json

from api.runtime.py.bandit import BanditService
from api.runtime.py.semgrep import SemgrepService
from api.src.logger import logger


def get_parser() -> argparse.ArgumentParser:
    """Get the parser for the command line arguments."""
    parser = argparse.ArgumentParser(
        description='Analyze files in the docker runtime')
    parser.add_argument(
        '-t',
        '--tools',
        type=str,
        help='Tools to run on the files. Example: "bandit,semgrep"',
    )
    return parser


def run(args):
    tools = args.tools.split(',')

    results_file_obj = open(
        f'/workspace/results.jsonl', 'a')

    for tool in tools:
        try:
            tool_class = {
                'bandit': BanditService,
                'semgrep': SemgrepService
            }[tool]
        except KeyError:
            logger.error(f'Unknown tool: {tool}')
            continue

        logger.info(f'Running {tool}')
        tool_instance = tool_class(workspace_dir='/workspace')
        results = tool_instance.analyze()
        for result in results:
            result['tool'] = tool
            results_file_obj.write(json.dumps(result) + '\n')


if __name__ == '__main__':
    parser = get_parser()
    args = parser.parse_args()
    run(args)
