# Release Notes


## Version 1.0.3 (July 30, 2025)

- Configured GitHub Actions for automatic documentation builds.

- Configured GitHub Actions for testing with `pytest` and integrated **Codecov** to monitor and report test coverage.

- Switched testing environment from `Ubuntu` to `Windows` with `pytest` to run the `.exe` file of the SWAT+ model.


## Version 1.0.2 (July 25, 2025)

- Updated sample data.

- Added additional test functions.

- Added several badges to the `README` for improved code visibility.

- Fixed code bugs and updated documentation.

- Modified `pySWATPlus` citation.


## Version 1.0.1 (July 23, 2025)

- Added sample data.

- Added more test functions using the sample data.

- Renamed some methods and variables for better consistency and clarity.

- Fixed code bugs and updated documentation.


## Version 1.0.0 (July 22, 2025)

- Refactored `TxtinoutReader` and `FileReader` for improved consistency, clarity, and simplicity.

- Removed `SWATProblem` and `SWATProblemMultimodel` classes due to usability issues; a better user interface for SWAT+ parameter calibration will be developed in the future.

- Fixed bugs in reading TXT files.

- Added GitHub Actions for static type checking with `mypy` to verify annotations throughout the codebase.

- Updated documentation on sensitivity analysis and other code changes.

- Removed `LICENSE` PyPI classifier from `pyproject.toml` and updated configuration according to packaging guidelines.

- Added Development Status PyPI classifier `Beta` to `pyproject.toml`.

- Added new package dependency `typing-extensions`.


## Version 0.2.20 (July 19, 2025)

- Updated key parts of the documentation to reflect recent code changes.


## Version 0.2.19 (July 19, 2025)

- Updated minimum Python requirement from 3.6 to 3.10.

- Added GitHub Actions for linting with `flake8` to enforce PEP8 formatting.

- Added GitHub Actions for testing with `pytest` to ensure code reliability.

- Fixed variable type annotations for static type checking.

- Added classifiers and keywords to `pyproject.toml`.

- Configured `pyproject.toml` to suppress `DeprecationWarning`.

- Removed `numpy` dependency as it is included with other required packages.


## Version 0.2.18 (May 4, 2025)

- Migrated all configurations to `pyproject.toml` for improved packaging.


## Version 0.2.17 (May 4, 2025)

- Renamed several variables to improve consistency across functions.

- Modified input and output variable type annotations to align with advanced-style static type checking.

- Fixed multiple code bugs.

- Improved code documentation.


## Version 0.2.16 (March 30, 2025)

- Introduced `TxtinoutReader` and `FileReader` classes for reading, modifying, and writing files to interact with the SWAT+ model.

- Added `SWATProblem` and `SWATProblemMultimodel` classes for calibrating SWAT+ parameters.

- Implemented GitHub Actions workflow for automated releases to PyPI and GitHub repositories.

- Completed migration from the TestPyPI repository to the main PyPI repository.


