# CI/CD Setup

All CI/CD pipelines should use the Nix shell environment to ensure consistent builds and tests.

## Example (GitHub Actions)

```yaml
- name: Enter Nix Shell and Run Tests
  run: nix-shell --run pytest
```

Refer to `shell.nix` for available commands and environment setup.
