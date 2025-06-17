# GitHub Actions & Automation

This directory contains GitHub Actions workflows and automation configurations for the reVoAgent repository.

## Workflows

### 1. CI Pipeline (`ci.yml`)
- **Triggers**: Push to `main`/`develop` branches, Pull Requests
- **Purpose**: Runs comprehensive tests, linting, and security checks
- **Features**:
  - Python 3.12 testing
  - Code formatting checks (Black, isort)
  - Linting (flake8)
  - Type checking (mypy)
  - Unit and integration tests
  - Code coverage reporting
  - Security scanning

### 2. Dependabot Auto-Merge (`dependabot-auto-merge.yml`)
- **Triggers**: Dependabot PRs, PR reviews, check suite completions
- **Purpose**: Automatically merges Dependabot PRs when tests pass
- **Safety Features**:
  - Only auto-merges patch and minor version updates
  - Requires all tests to pass
  - Major version updates require manual review
  - Adds appropriate labels for tracking
  - Provides detailed comments for major updates

## Dependabot Configuration (`dependabot.yml`)

Automatically creates PRs for dependency updates:

- **Python dependencies**: Weekly updates on Mondays
- **Frontend dependencies**: Weekly npm/yarn updates
- **Docker dependencies**: Weekly base image updates
- **GitHub Actions**: Weekly action version updates

### Auto-Merge Rules

✅ **Automatically merged**:
- Patch updates (e.g., 1.0.1 → 1.0.2)
- Minor updates (e.g., 1.0.0 → 1.1.0)
- When all tests pass
- When linting passes

⚠️ **Requires manual review**:
- Major updates (e.g., 1.0.0 → 2.0.0)
- Critical dependencies (torch, transformers, langchain)
- Failed tests or linting

### Security

- All workflows use pinned action versions
- Minimal required permissions
- Secure token handling
- No secrets exposed in logs

## Setup Requirements

1. **Repository Settings**:
   - Enable "Allow auto-merge" in repository settings
   - Ensure branch protection rules allow auto-merge
   - Configure required status checks

2. **Labels** (auto-created by workflows):
   - `dependencies`
   - `python`, `frontend`, `docker`, `github-actions`
   - `patch-update`, `minor-update`, `major-update`
   - `auto-mergeable`, `needs-manual-review`

## Monitoring

- Check the Actions tab for workflow runs
- Review Dependabot PRs in the Pull Requests tab
- Monitor security alerts in the Security tab

## Customization

To modify auto-merge behavior:
1. Edit `.github/workflows/dependabot-auto-merge.yml`
2. Adjust the conditions in the "Check if PR is ready for auto-merge" step
3. Modify ignored dependencies in `.github/dependabot.yml`

## Troubleshooting

**Auto-merge not working?**
- Check repository settings for auto-merge permission
- Verify branch protection rules
- Ensure all required checks are passing

**Too many Dependabot PRs?**
- Adjust `open-pull-requests-limit` in `dependabot.yml`
- Add more dependencies to the ignore list
- Change update frequency from "weekly" to "monthly"
