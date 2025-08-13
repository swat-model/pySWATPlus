# Contributing to pySWATPlus

Thank you for considering contributing to `pySWATPlus`, an open-source Python package to provide a programmatic interface to the SWAT+ model. We welcome contributions to enhance its functionality for navigating `TxtInOut` folders, modifying input parameters, running simulations, and performing sensitivity analysis and calibration. This document outlines how to contribute effectively.

## Getting Started

### Prerequisites

To contribute, ensure you have the following installed:

- **Python**: Version 3.10 or higher.
- **Git**: For version control.
- **pip** or **conda** (if using Conda environments).
- A code editor (e.g., VS Code, PyCharm).

### Setting Up the Development Environment

1. **Fork the Repository**:

   - Fork the repository on GitHub by clicking the "Fork" button.
   - Clone your fork to your local machine:

     ```bash
     git clone https://github.com/swat-model/pySWATPlus.git
     cd pySWATPlus
     ```

2. **Create a Virtual Environment**:

   - Set up a virtual environment to isolate dependencies:

     ```bash
     python -m venv venv
     source venv/bin/activate  # On Windows: venv\Scripts\activate
     ```
     - Alternatively, use Conda:

       ```bash
       conda create -n pySWATPlus python=3.10
       conda activate pySWATPlus
       ```

3. **Install Dependencies**:

   - Install required dependencies:

     ```bash
     pip install -r requirements.txt
     ```
   - Install development tools for linting, type checking, testing, and building:

     ```bash
     pip install flake8 mypy pytest pytest-cov
     ```

4. **Install in Editable Mode**:

   - Install the package in editable mode for development:

     ```bash
     pip install --editable .
     ```

5. **Verify Setup**:

- Open Python and ensure the package can be imported without errors:

  ```python
  import pySWATPlus
  ```

## How to Contribute

1. **Find an Issue**:

   - Browse the Issues page for open tasks.
   - Propose new features or bug fixes by creating an issue to discuss with maintainers.

2. **Create a Branch**:

   - Create a descriptive branch for your work:

     ```bash
     git checkout -b feature/your-feature-name
     ```
     - Examples: `fix/txtinout-parsing-error`, `feature/add-parallel-sensitivity`.

3. **Make Changes**:

   - Follow the Coding Guidelines below.
   - Write clear commit messages (e.g., `Add support for parallel SALib analysis`).

4. **Run Tests and Linting**:

   - Run tests with coverage report:

     ```bash
     pytest -rA -Wignore::DeprecationWarning --cov=pySWATPlus --cov-report=xml
     ```
   - Check code style and type hints:

     ```bash
     flake8 pySWATPlus
     mypy pySWATPlus
     ```

5. **Commit and Push**:

   - Commit your changes:

     ```bash
     git add .
     git commit -m "Your descriptive commit message"
     git push origin feature/your-feature-name
     ```

6. **Submit a Pull Request**:

   - Create a pull request (PR) on GitHub from your branch.
   - Reference the relevant issue (e.g., `Closes #123`).
   - Describe your changes, including their purpose and impact.
   - Ensure CI checks (if set up) pass.

7. **Code Review**:

   - Respond to maintainer feedback promptly.
   - Update your PR with requested changes.

## Coding Guidelines

- **Code Style**:

  - Adhere to PEP 8 for Python code.
  - Run `flake8` to catch style issues:

    ```bash
    flake8 pySWATPlus
    ```

- **Type Hints**:

  - Use `mypy` for static type checking:

    ```bash
    mypy pySWATPlus
    ```
  - Add type hints to all new functions and classes where applicable.

- **Documentation**:

  - Write Google-style docstrings for all functions, classes, and modules.
  - Update the pySWATPlus documentation if your changes affect usage or introduce new features.

- **Testing**:

  - Write unit tests using `pytest` for new features or bug fixes.
  - Place tests in the `tests/` directory.
  - Aim for at least 80% test coverage, verifiable with the coverage report:

    ```bash
    pytest -rA -Wignore::DeprecationWarning --cov=pySWATPlus --cov-report=xml
    ```

- **Commit Messages**:

  - Reference issue numbers (e.g., `Fix #123: Resolve simulation crash`).

## Code of Conduct

Please follow our Code of Conduct to maintain a welcoming and inclusive environment for all contributors.

## Questions?

For help or clarification:

- Open an issue on GitHub.
- Contact the maintainers via [GitHub Issues](https://github.com/swat-model/pySWATPlus/issues).

Thank you for contributing to `pySWATPlus`!
