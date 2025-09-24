import typing
from pydantic import BaseModel, field_validator


class ParameterBase(BaseModel):
    name: str
    change_type: typing.Literal['absval', 'abschg', 'pctchg']
    units: typing.Optional[list[int]] = None
    conditions: typing.Optional[dict[str, list[str]]] = None

    @field_validator('units')
    @classmethod
    def validate_units(cls, v: typing.Optional[typing.Iterable[int]]) -> typing.Optional[typing.Iterable[int]]:
        if v is not None and any(num <= 0 for num in v):
            raise ValueError(f'All unit IDs must be > 0, got {list(v)}')
        return list(v) if v is not None else None


class ParameterModel(ParameterBase):
    value: float


class ParameterBoundedModel(ParameterBase):
    upper_bound: float
    lower_bound: float


ParametersType: typing.TypeAlias = list[dict[str, typing.Any]]
"""
Defines parameter modifications for SWAT+ model input files.

Example:
    ```python
    parameters = [
        {
            "name": 'cn2',
            "change_type": "pctchg",
            "value": 50,
        },
        {
            "name": 'perco',
            "change_type": "absval",
            "value": 0.5,
            "conditions": {"hsg": ["A"]}
        },
        {
            'name': 'bf_max',
            "change_type": "absval",
            "value": 0.3,
            "units": range(1, 194)
        }
    ]
    ```

Keys for each parameter change:

| Key          | Type (default)                  | Description                                                    |
|--------------|---------------------------------|----------------------------------------------------------------|
| name         | str (required)                  | Name of the parameter to which the changes will be applied.    |
| change_type  | str (required)                  | Type of change: 'absval', 'abschg', or 'pctchg'.               |
| value        | float (required)                | Value of the parameter.                                        |
| units        | Iterable[int] (optional)        | List of 1-based unit IDs to constrain the parameter change.    |
| conditions   | dict[str, list[str]] (optional) | Dictionary of conditions to apply when changing the parameter. |
"""

ParametersBoundedType: typing.TypeAlias = list[dict[str, typing.Any]]
"""
Defines bounded parameter modifications for SWAT+ model input files.

This follows the same logic as `ParametersType`, but instead of a single `value`,
each parameter specifies `lower_bound` and `upper_bound`. Used for sensitivity analysis and calibration.

Example:
    ```python
    parameters = [
        {
            "name": "bf_max",
            "change_type": "absval",
            "lower_bound": 0.2,
            "upper_bound": 0.3,
            "units": range(1, 194)
        }
    ]
    ```

Keys for each parameter change:

| Key          | Type (default)                  | Description                                                    |
|--------------|---------------------------------|----------------------------------------------------------------|
| name         | str (required)                  | Name of the parameter to which the changes will be applied.    |
| change_type  | str (required)                  | Type of change: 'absval', 'abschg', or 'pctchg'.               |
| lower_bound  | float (required)                | Lower bound for the parameter.                                 |
| upper_bound  | float (required)                | Upper bound for the parameter.                                 |
| units        | Iterable[int] (optional)        | List of 1-based unit IDs to constrain the parameter change.    |
| conditions   | dict[str, list[str]] (optional) | Dictionary of conditions to apply when changing the parameter. |
"""
