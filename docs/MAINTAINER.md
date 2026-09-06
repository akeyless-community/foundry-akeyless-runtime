# Maintainer guide: repository access controls

Settings applied to restrict changes so **people outside the Akeyless org must be reviewed and approved** before code lands on `main` or ships to PyPI.

## What is enforced

| Control | Effect |
|---------|--------|
| **Branch protection on `main`** | No direct pushes; changes only via pull request |
| **Push restrictions** | Only `@akeyless-community/cs-admin` can push or merge to `main` |
| **CODEOWNERS** (`@akeyless-community/cs-admin`) | PRs require approval from a `cs-admin` team member |
| **CI required** | `ci-success` must pass before merge |
| **Stale review dismissal** | New commits invalidate prior approvals |
| **Last-push approval** | Re-approval required after new commits |
| **`pypi` environment** | PyPI publish requires approval from a maintainer |

## Files in this repo

- [`.github/CODEOWNERS`](../.github/CODEOWNERS)
- [`.github/pull_request_template.md`](../.github/pull_request_template.md)
- [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)
- [`.github/workflows/publish.yml`](../.github/workflows/publish.yml)

## Org settings (verify in GitHub UI)

These are **organization-level** and cannot be stored in the repo. An org admin should confirm:

### 1. Base permissions

**Organization settings** → **Member privileges** → **Base permissions**

- Recommended: **Read** for org members who are not maintainers

### 2. Fork PR workflows

**Organization settings** → **Actions** → **General** → **Fork pull request workflows**

- Enable: **Require approval for all outside collaborators**

### 3. Add maintainers to the team

**Organization** → **Teams** → **cs-admin** → add Akeyless reviewers.

## Re-applying branch protection

```bash
gh api \
  --method PUT \
  repos/akeyless-community/foundry-akeyless-runtime/branches/main/protection \
  --input - <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "checks": [
      { "context": "ci-success" }
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "required_approving_review_count": 1,
    "require_last_push_approval": true
  },
  "restrictions": {
    "users": [],
    "teams": ["cs-admin"],
    "apps": []
  },
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": true
}
EOF
```

## PyPI environment

**Repository** → **Settings** → **Environments** → **pypi** → **Required reviewers** from `@akeyless-community/cs-admin`.

## External contributor flow

1. Fork the public repo
2. Open a PR from their fork
3. CI runs after maintainer approves workflow (if fork)
4. A `cs-admin` member reviews, approves, and merges
