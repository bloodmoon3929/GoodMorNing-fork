# Sensitive-data handling

- Never print, paste into chat, commit, or publish actual API keys, access keys, bearer tokens, private connection URLs, or passwords. Report only the name, presence, and result of a check.
- Keep local credentials in ignored `data/` files or process environment variables. Tracked examples must contain empty credential values. GitHub Pages and Actions variables are public configuration only; never place secrets in frontend files or build arguments.
- Before every commit, run `python scripts/check_secrets.py` and the installed Gitleaks staged check. Keep `.githooks/pre-commit` enabled. Do not bypass hooks, suppress a real finding, add an allowlist, or disable the CI security gate to get a commit/deployment through.
- Before deployment, inspect the artifact for private files and known local credential values. Investigate findings without printing matched content. If a genuine credential was already pushed, report its type/location with the value redacted and coordinate rotation; deleting the current file does not remove Git history.
