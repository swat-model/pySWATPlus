# Contributing to pySWATPlus

Thank you for considering contributing to `pySWATPlus`, an open-source Python package that provides a programmatic interface for interacting with the `SWAT+` model. We welcome contributions that enhance its functionality, including navigating `TxtInOut` folders, modifying input parameters, running simulations, performing sensitivity analyses, and calibrating models. This document outlines the steps to contribute effectively.


## Getting Started

### Prerequisites

To contribute, ensure you have the following installed:

- **Python**: Version 3.10 or higher.
- **Git**: For version control.
- **pip** or **conda** (if using `conda` environments).
- A code editor (e.g., JuputerLab, VS Code, PyCharm).

### Development Setting

- Create a Virtual Environment:

    - Set up a virtual environment to isolate dependencies:

        ```bash
        python -m venv venv
        source venv/bin/activate  # On Windows: venv\Scripts\activate
        ```

    - Alternatively, use `conda`:

        ```bash
        conda create --name pySWATPlus
        conda activate pySWATPlus
        conda install pip
        ```
        

- Clone the `GitHub` Repository:

    - Fork the repository on GitHub by clicking the **Fork** button.

    - Clone your fork to your local machine at the desired folder path:

        ```bash
        cd C:\\users\\username\\folder_path
        git clone https://github.com/swat-model/pySWATPlus.git
        cd pySWATPlus
        ```

- Install Dependencies:

    - Install required dependencies:

        ```bash
        pip install -r requirements.txt
        ```

    - Install development dependencies:

        ```bash
        pip install flake8       # Code style check
        pip install mypy         # Static type checking
        pip install pytest       # Run tests
        pip install pytest-cov   # Test coverage report
        pip install build        # Build distribution package
        pip install mkdocs mkdocs-material  # Documentation site generation
        pip install mkdocstrings-python     # Documentation for Python docstrings
        ```

- Install `pySWATPlus` in Editable Mode:

    ```bash
    python -m build
    pip install --editable .
    ```

- Verify Installation:

    ```python
    import pySWATPlus  # should execute with no error
    ```

## How to Contribute

The following steps describe how to contribute to the project.

### Types of Contributions

- Solve the existing [GitHub Issues](https://github.com/swat-model/pySWATPlus/issues).
- Fix a code bug.
- Propose a new feature.
- Improve documenation.
- Suggest a new idea.


### Code and Testing Guidelines:

- Modify codes for the feature you want to work.

- Test the Modified Code:

    - Write test functions for the modified code in the `tests/` directory.  
      Use file and function names with the prefix `test_`.
    - Run tests and verify test coverage from the generated `cov_pySWATPlus` directory:

        ```bash
        pytest tests/
        ```

- Test Code Style:

    - Adhere to [PEP 8](https://peps.python.org/pep-0008/) style for Python code.
    - Run the following command to catch style issues:

        ```bash
        flake8
        ```

- Test Type Hints:

    - Add type hints to all variables where applicable.
    - Run the following command to check type hints:

        ```bash
        mypy
        ```

- Test Documentation:

    - Update documentation if the changes affect usage or introduce new features.
    - Run the following command to build documentation:

        ```bash
        mkdocs build
        ```

- If all test functions, code style checks, type hints, and documentation build successfully without any errors, the modified code is ready to be submitted.


### Submit Contributions

- Create a Separate Branch:

    ```bash
    git checkout -b <feature>/<your-feature-name>
    ```
    
- Commit and Push Changes:

    - Commit an individual file (recommended):

        ```bash
        git add <filename>
        git commit -m "Specific commit message related to the file"
        git push origin <feature>/<your-feature-name>
        ```

    - Commit all changes together:

        ```bash
        git add .
        git commit -m "Descriptive commit message for all changes"
        git push origin <feature>/<your-feature-name>
        ```

- Open a Pull Request (PR):

    - Create a PR on GitHub from your branch `<feature>/<your-feature-name>`.
    - Describe your changes, including their purpose and impact, and reference any open issues if applicable (e.g., `fixes #123`).
    - Ensure the pull request passes all CI/CD workflows.

## Code Review Process

- Maintainers will provide feedback on your PR to improve the code.
- Update your PR according to the feedback.
- Maintainers will review the changes and, if satisfactory, approve the PR for merging.


## Code of Conduct

Please follow our [Code of Conduct](https://github.com/swat-model/pySWATPlus/blob/main/CODE_OF_CONDUCT.md) to maintain a welcoming and inclusive environment for all contributors.


## Further Queries

For any help or clarification, contact the maintainers via [GitHub Issues](https://github.com/swat-model/pySWATPlus/issues).  
Thank you for contributing to `pySWATPlus`!
