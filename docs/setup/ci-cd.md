# CI/CD Setup

All CI/CD pipelines use the Nix shell environment to ensure consistent builds and tests.

## Example (GitHub Actions)

```yaml
- name: Enter Nix Shell and Run Tests
  run: nix-shell --run pytest
```

For local development without Nix, see `docs/setup/environment.md` (requirements.txt, npm install, Docker).

Reference: `shell.nix` for available commands and environment setup.
