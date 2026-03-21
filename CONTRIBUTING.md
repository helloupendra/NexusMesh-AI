# Contributing to NexusMesh-AI

Thanks for contributing.

## Development Setup

1. Create a Python environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r orchestrator/requirements.txt
   ```
2. Start infrastructure:
   ```bash
   cd infrastructure/docker
   docker compose --env-file ../../.env up --build -d
   ```

## Quality Gates

- Run Python tests before opening a PR:
  ```bash
  ./venv/bin/python -m unittest discover -s tests -p "test_*.py"
  ```
- Keep task payload format stable across Python and C#:
  - `task_id`
  - `task_type`
  - `request`
- Keep result payload format stable:
  - `task_id`
  - `task_type`
  - `status`
  - `result`
  - `error`

## PR Checklist

- Clear title and summary.
- Include validation steps and output.
- Update README/docs for behavior changes.
- Avoid unrelated formatting-only changes in large PRs.
