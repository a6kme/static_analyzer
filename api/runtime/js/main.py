
# Command line arguments
# noqa
import argparse
import json

from api.runtime.common.semgrep import SemgrepService
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


def get_tool(tool):
    if tool == 'semgrep':
        # TODO: check package.json for frameworks like react / vue / angular and
        # add the appropriate rulesets

        return SemgrepService(
            workspace_dir='/workspace', rulesets=['p/security-audit', 'p/javascript', 'p/typescript']
        )


def run(args):
    tools = args.tools.split(',')

    results_file_obj = open(
        f'/workspace/results.jsonl', 'a')

    for tool in tools:
        tool_obj = get_tool(tool)
        if not tool_obj:
            logger.error(f'Unknown tool: {tool}')
            continue

        logger.info(f'Running {tool}')
        results = tool_obj.analyze()
        for result in results:
            result['tool'] = tool
            results_file_obj.write(json.dumps(result) + '\n')


if __name__ == '__main__':
    parser = get_parser()
    args = parser.parse_args()
    run(args)
