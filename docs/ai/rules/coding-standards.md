# Coding Standards

> **Note:** All build and test commands are executed autonomously by the AI inside the Nix shell environment. The AI never instructs the user to run commands.
> 
> ```sh
> nix-shell
> ```
> 
> For running tests:
> 
> ```sh
> nix-shell --run pytest
> ```

- Use consistent indentation (spaces over tabs, 2 or 4 spaces as per language convention).
- Follow language-specific style guides (e.g., PEP8 for Python, Airbnb for JS/TS).
- Use descriptive variable, function, and class names.
- Write clear, concise comments and documentation.
- Keep functions and classes small and focused.
- Avoid code duplication; use DRY principles.
- Write tests for all new features and bug fixes.
- Use version control best practices (atomic commits, meaningful messages).
- Ensure code passes all linters and tests before merging.
