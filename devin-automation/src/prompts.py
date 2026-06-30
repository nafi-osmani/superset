"""Prompt templates for Devin remediation sessions."""


def build_remediation_prompt(
    issue_number: int,
    issue_title: str,
    issue_body: str,
    repo: str,
) -> str:
    owner, name = repo.split("/", 1)
    issue_url = f"https://github.com/{owner}/{name}/issues/{issue_number}"

    return f"""You are remediating a tech-debt GitHub issue in the Apache Superset repository.

## Issue
- Number: #{issue_number}
- Title: {issue_title}
- URL: {issue_url}

## Description
{issue_body}

## Instructions
1. Clone the repository `{repo}` and create a branch named `fix/issue-{issue_number}` from the default branch.
2. Make the minimal change required to resolve the issue. Do not refactor unrelated code.
3. Follow project conventions in AGENTS.md at the repo root:
   - Run `pre-commit run` on changed files before committing
   - Use proper type hints in Python; avoid `any` in TypeScript
   - Keep the diff focused and small
4. Run the verification commands listed in the issue description and ensure they pass.
5. Open a pull request against the default branch with title: `fix: {issue_title}` and body referencing `Fixes #{issue_number}`.
6. Post a comment on issue #{issue_number} summarizing your changes and linking the PR.
   Use the GitHub REST API with the `$GITHUB_TOKEN` environment variable:
   POST https://api.github.com/repos/{repo}/issues/{issue_number}/comments

## Deliverables
- A working PR with passing verification
- A comment on the GitHub issue with the PR link
"""
