# Testing Guidelines

All tests should be run inside the Nix shell environment for consistency.

## Running Tests

```sh
nix-shell --run pytest
```

Refer to `shell.nix` for additional test and build commands.
