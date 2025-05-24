# Dev Setup

## With Nix
```sh
nix-shell
# then e.g. pytest, uvicorn, etc.
```

## Without Nix
```sh
pip install -r requirements.txt
cd frontend && npm install
uvicorn api.app.main:app --reload
```

For more details: [environment.md](./environment.md)
