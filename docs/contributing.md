# Contributing Guide

> **Note:** All development, testing, and build commands should be run inside the Nix shell environment. Enter the shell with:
> 
> ```sh
> nix-shell
> ```
> 
> For running tests, always use:
> 
> ```sh
> nix-shell --run pytest
> ```

## How to Contribute
- Fork the repository and create a feature branch.
- Make your changes, following the coding standards and commit message conventions.
- Write or update tests and documentation as needed.
- Submit a pull request for review (by human or AI).

## Code Review Process
- All changes must be reviewed by at least one reviewer (human or AI).
- Use the issue tracker to discuss and track changes.
- Follow the branching and PR strategy outlined in the project docs.

## AI-Specific Protocols
- AI agents must log all autonomous actions and decisions.
- AI must escalate ambiguous or high-impact changes to a human reviewer.
- See `/docs/ai/rules/` for detailed AI protocols.

## Style Guides
- Follow the coding standards in `/docs/ai/rules/coding-standards.md`.
- Use consistent formatting and naming conventions.

## Commit Messages
- Use clear, descriptive commit messages.
- Reference related issues or feature requests where applicable.
