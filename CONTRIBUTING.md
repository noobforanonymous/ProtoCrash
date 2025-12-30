# Contributing to ProtoCrash

Thank you for your interest in contributing to ProtoCrash! We welcome contributions from the community to make this tool better for everyone.

## Getting Started

1.  **Fork the repository** on GitHub.
2.  **Clone your fork** locally:
    ```bash
    git clone https://github.com/YOUR_USERNAME/ProtoCrash.git
    cd ProtoCrash
    ```
3.  **Create a virtual environment** and install dependencies:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -e ".[dev]"
    ```

## Development Workflow

1.  **Create a branch** for your feature or fix:
    ```bash
    git checkout -b feature/my-new-feature
    ```
2.  **Make your changes.** Ensure code is clean and documented.
3.  **Run tests** to ensure no regressions:
    ```bash
    pytest
    ```
4.  **Run linting** to check code style:
    ```bash
    ruff check src/
    pylint src/protocrash
    ```

## Pull Request Process

1.  Push your branch to GitHub:
    ```bash
    git push origin feature/my-new-feature
    ```
2.  Open a **Pull Request** against the `main` branch.
3.  Describe your changes clearly in the PR description.
4.  Wait for review. We may ask for changes or clarifications.

## Coding Standards

-   **Python Version:** 3.11+
-   **Style:** Follow PEP 8. We use `ruff` and `pylint` for enforcement.
-   **Type Hinting:** Use type hints for function arguments and return values.
-   **Documentation:** Add docstrings to all modules, classes, and functions.

## Reporting Issues

If you find a bug or have a feature request, please open an issue on GitHub.
-   Check existing issues first to avoid duplicates.
-   Provide clear steps to reproduce bugs.
-   Include system information (OS, Python version).

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
