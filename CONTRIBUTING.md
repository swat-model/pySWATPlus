# Contributing to pySWATPlus

Thank you for considering contributing to `pySWATPlus`! This document outlines how to contribute effectively.

## Kinds of Contribution
There are many ways to contribute to this project. To name a few:

- File bug reports or feature requests as GitHub issues
- Contribute a bug fix as a pull request
- Improve the [documentation](https://swat-model.github.io/pySWATPlus/) with new tutorials, better descriptions, or even just by fixing typos

The following sections will give some more guidance for each of these options.

## Reporting Bugs and feature requests
If you've come across some behavior that you think is a bug or a missing feature, the first step is to check if it's already known. For this, take a look at the [GitHub Issues](https://github.com/swat-model/pySWATPlus/issues) page.

If you can't find anything related there, you're welcome to create your own issue. You are also welcome to propose new features.

## Contributing code with a pull request

If you wrote some code to fix a bug or provide some new functionality, we use use pull requests (PRs) to merge these changes into the project.

In a PR, please provide a small description of the changes you made, including a reference to the issue that your PR solves (if one exists). We'll take a look at your PR and do a small code review, where we might outline changes that are necessary before we can merge your PR into the project. Please don't feel overwhelmed by our change requests---it's entirely normal to have a code review go back and forth a few times before the code is ready to be merged.

Once everyone is happy with the changes in the PR, we'll approve and merge it into the master branch.

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
5. **Create a Branch**:

   - Create a descriptive branch for your work:

     ```bash
     git checkout -b feature/your-feature-name
     ```
     - Examples: `fix/txtinout-parsing-error`, `feature/add-parallel-sensitivity`.

6. **Make Changes**:

   - Follow the Coding Guidelines below.
   - Write clear commit messages (e.g., `Add support for parallel SALib analysis`).

7. **Run Tests and Linting**:

   - Run tests with coverage report:

     ```bash
     pytest -rA -Wignore::DeprecationWarning --cov=pySWATPlus --cov-report=xml
     ```
   - Check code style and type hints:

     ```bash
     flake8 pySWATPlus
     mypy pySWATPlus
     ```

8. **Commit and Push**:

   - Commit your changes:

     ```bash
     git add .
     git commit -m "Your descriptive commit message"
     git push origin feature/your-feature-name
     ```

9. **Submit a Pull Request**:

   - Create a pull request (PR) on GitHub from your branch.
   - Reference the relevant issue (e.g., `Closes #123`).
   - Describe your changes, including their purpose and impact.
   - Ensure CI checks (if set up) pass.

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

## Documentation

The pySWATPlus documentation is automatically generated from the files located in the `docs/` folder. If your PR introduces any changes that should be documented, you'll find the relevant files there.

To build the documentation webpage locally and see if everything is rendered correctly, use MkDocs by running the following command in the `docs/` folder:

```bash
mkdocs serve
```

This will start a local development server, typically accessible at `localhost:8000` in your browser. Please check the output of this command to ensure there are no broken links or other issues (these will appear as red warnings or errors in the terminal).

## Code of Conduct

Please follow our Code of Conduct to maintain a welcoming and inclusive environment for all contributors.
