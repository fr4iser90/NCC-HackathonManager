# Environment Setup

**Recommended:** For maximum reproducibility, use the Nix shell environment (`nix-shell`) for development, build, and test. See `shell.nix` for details.

## With Nix (e.g., NixOS, CI/CD)
```sh
nix-shell
```
All tools and commands described in the documentation are available.

## Without Nix (e.g., Ubuntu, Mac, Windows)
1. Python dependencies:
   ```sh
   pip install -r requirements.txt
   ```
2. Node dependencies:
   ```sh
   cd frontend && npm install
   ```
3. Start the backend:
   ```sh
   uvicorn api.app.main:app --reload
   # or via Docker: docker-compose up
   ```

**Note:** The CI/CD pipeline always uses Nix for maximum reproducibility.

# 
use npm dev blablabla