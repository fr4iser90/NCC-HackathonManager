# Development Environment Setup

All development, testing, and build commands should be run inside the Nix shell environment.

## Steps

1. Install [Nix](https://nixos.org/download.html) if you haven't already.
2. Clone the repository.
3. Enter the shell:
   ```sh
   nix-shell
   ```
4. Run tests:
   ```sh
   nix-shell --run pytest
   ```
5. Use provided shell functions for building, running, and cleaning as described in `shell.nix`.
