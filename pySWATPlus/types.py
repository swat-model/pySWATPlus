import typing
from pydantic import BaseModel, model_validator, field_validator


def ensure_list(val: typing.Any) -> list[typing.Any]:
    """
    Ensure the input is returned as a list
    """
    if isinstance(val, list):
        return val
    return [val]


def reshape_input(values: dict[str, typing.Any]) -> dict[str, typing.Any]:
    """
    Extract 'has_units' and normalize other keys into lists under 'params'.
    """
    has_units = values.get("has_units")
    params = {k: v for k, v in values.items() if k != "has_units"}

    # Normalize dicts into lists
    normalized_params = {}
    for key, val in params.items():
        normalized_params[key] = ensure_list(val)

    return {"has_units": has_units, "params": normalized_params}


M = typing.TypeVar("M", bound=BaseModel)


# ======================================================
# Param and ParamBounded
# ======================================================

class ParamChangeBase(BaseModel):
    change_type: typing.Literal['absval', 'abschg', 'pctchg'] = 'absval'
    filter_by: str | None = None


class ParamChangeModel(ParamChangeBase):
    value: float


class ParamBoundedChangeModel(ParamChangeBase):
    upper_bound: float
    lower_bound: float


class FileParamsModelBase(BaseModel):
    has_units: bool

    @model_validator(mode="before")
    @classmethod
    def reshape_input(cls, values: dict[str, typing.Any]) -> dict[str, typing.Any]:
        return reshape_input(values)


class FileParamsModel(FileParamsModelBase):
    params: dict[str, list[ParamChangeModel]]


class FileParamsBoundedModel(FileParamsModelBase):
    params: dict[str, list[ParamBoundedChangeModel]]


T = typing.TypeVar("T", bound=BaseModel)


def from_dict_generic(cls: typing.Type[M], data: dict[str, typing.Any], file_cls: typing.Type[T]) -> M:
    """Generic constructor for top-level Params models."""
    return cls(file_params={k: file_cls(**v) for k, v in data.items()})


class ParamsModel(BaseModel):
    file_params: dict[str, FileParamsModel]

    @classmethod
    def from_dict(cls, data: dict[str, typing.Any]) -> "ParamsModel":
        return from_dict_generic(cls, data, FileParamsModel)


class ParamsBoundedModel(BaseModel):
    file_params: dict[str, FileParamsBoundedModel]

    @classmethod
    def from_dict(cls, data: dict[str, typing.Any]) -> "ParamsBoundedModel":
        return from_dict_generic(cls, data, FileParamsBoundedModel)


ParamsType: typing.TypeAlias = dict[str, dict[str, typing.Any]]
"""
Defines parameter modifications for SWAT+ model input files.

Example:
    ```python
    params: ParamsType = {
        'plants.plt': {
            'has_units': False,
            'bm_e': [
                {'value': 100.0, 'change_type': 'absval', 'filter_by': 'name == "agrl"'},
                {'value': 110.0, 'change_type': 'absval', 'filter_by': 'name == "almd"'}
            ]
        },
        'hydrology.hyd': {
            'has_units': False,
            'epco': {'value': 0.25, 'change_type': 'abschg'},
            'perco': {'value': 0.1, 'change_type': 'absval'}
        }
    }
    ```

Keys for each parameter change:

| Key          | Type   | Default   | Description                                             |
|--------------|--------|-----------|---------------------------------------------------------|
| change_type  | str    | 'absval'  | Type of change: 'absval', 'abschg', or 'pctchg'.        |
| value        | float  | —         | The value to apply to the parameter.                    |
| filter_by    | str    | None      | Pandas `.query()` string to filter rows for the change. |

Notes:
    - Each parameter (`<param_name>`) can be a **single dictionary** or a **list of dictionaries**.
    - The `has_units` key is **required** for each file.

"""


ParamsBoundedType: typing.TypeAlias = dict[str, dict[str, typing.Any]]
"""
Defines bounded parameter modifications for SWAT+ model input files.

This follows the same logic as `ParamsType`, but instead of a single `value`,
each parameter specifies an `upper_bound` and `lower_bound`. Used for sensitivity analysis.

Example:
    ```python
    params: ParamsType = {
        'plants.plt': {
            'has_units': False,
            'bm_e': [
                {'lower_bound': 90.0, 'lower_bound': 100.0, 'change_type': 'absval', 'filter_by': 'name == "agrl"'},
            ]
        },
    }
    ```

Keys for each parameter change:

| Key          | Type   | Default   | Description                                             |
|--------------|--------|-----------|---------------------------------------------------------|
| change_type  | str    | 'absval'  | Type of change: 'absval', 'abschg', or 'pctchg'.       |
| lower_bound  | float  | —         | The lower bound for the parameter.                     |
| upper_bound  | float  | —         | The upper bound for the parameter.                     |
| filter_by    | str    | None      | Pandas `.query()` string to filter rows for the change.|

Notes:
    - Each parameter (`<param_name>`) can be a **single dictionary** or a **list of dictionaries**.
    - The `has_units` key is **required** for each file.

"""


# ======================================================
# CalParam and CalParamBounded
# ======================================================


class CalParamChangeBase(BaseModel):
    change_type: typing.Literal['absval', 'abschg', 'pctchg'] = 'absval'
    units: typing.Optional[list[int]] = None
    conditions: typing.Optional[dict[str, list[str]]] = None

    @field_validator("units")
    @classmethod
    def validate_units(cls, v: typing.Optional[typing.Iterable[int]]) -> typing.Optional[typing.Iterable[int]]:
        if v is not None and any(num <= 0 for num in v):
            raise ValueError(f"All unit IDs must be > 0, got {list(v)}")
        return list(v) if v is not None else None


class CalParamChangeModel(CalParamChangeBase):
    value: float


class CalParamBoundedChangeModel(CalParamChangeBase):
    upper_bound: float
    lower_bound: float


U = typing.TypeVar("U", bound=CalParamChangeBase)


def cal_from_dict_generic(cls: typing.Type[M], data: dict[str, typing.Any], param_cls: typing.Type[U]) -> M:
    return cls(params={k: [param_cls(**item) for item in ensure_list(v)] for k, v in data.items()})


class CalParamsModel(BaseModel):
    params: dict[str, list[CalParamChangeModel]]

    @classmethod
    def from_dict(cls, data: dict[str, typing.Any]) -> "CalParamsModel":
        return cal_from_dict_generic(cls, data, CalParamChangeModel)


class CalParamsBoundedModel(BaseModel):
    params: dict[str, list[CalParamBoundedChangeModel]]

    @classmethod
    def from_dict(cls, data: dict[str, typing.Any]) -> "CalParamsBoundedModel":
        return cal_from_dict_generic(cls, data, CalParamBoundedChangeModel)


CalParamsType: typing.TypeAlias = dict[str, typing.Any]
"""
Defines parameter modifications for SWAT+ model input files.

Example:
    ```python
    params = {
        "cn2":    {
            "change_type": "pctchg",
            "value": 50,
        },
        "perco": {
            "change_type": "absval",
            "value": 0.5,
            "conditions": {"hsg": ["A"]}
        },
        "bf_max": [{
            "change_type": "absval",
            "value": 0.3,
            "units": range(1, 194)
        }]
    }
    ```

Keys for each parameter change:

| Key          | Type                       | Default   | Description                                                                                  |
|--------------|----------------------------|-----------|----------------------------------------------------------------------------------------------|
| change_type  | str                        | 'absval'  | Type of change: 'absval', 'abschg', or 'pctchg'.                                             |
| value        | float                      | —         | The value to apply to the parameter.                                                        |
| units        | Iterable[int], optional    | None      | Optional list of 1-based unit IDs to constrain the parameter change.                        |
| conditions   | dict[str, list[str]], optional | None  | Optional dictionary of conditions to apply when changing the parameter.                      |
Notes:
    - Each parameter (`<param_name>`) can be a **single dictionary** or a **list of dictionaries**.

"""

CalParamsBoundedType: typing.TypeAlias = dict[str, typing.Any]
"""
Defines bounded parameter modifications for SWAT+ model input files.

This follows the same logic as `CalParamsType`, but instead of a single `value`,
each parameter specifies `lower_bound` and `upper_bound`. Used for sensitivity analysis.

Example:
    ```python
    params = {
        "bf_max": [{
            "change_type": "absval",
            "lower_bound": 0.2,
            "upper_bound": 0.3,
            "units": range(1, 194)
        }]
    }
    ```

Keys for each parameter change:

| Key          | Type                       | Default   | Description                                                                                  |
|--------------|----------------------------|-----------|----------------------------------------------------------------------------------------------|
| change_type  | str                        | 'absval'  | Type of change: 'absval', 'abschg', or 'pctchg'.                                             |
| lower_bound  | float                      | —         | The lower bound for the parameter.                                                          |
| upper_bound  | float                      | —         | The upper bound for the parameter.                                                          |
| units        | Iterable[int], optional    | None      | Optional list of 1-based unit IDs to constrain the parameter change.                        |
| conditions   | dict[str, list[str]], optional | None  | Optional dictionary of conditions to apply when changing the parameter.                      |

Notes:
    - Each parameter (`<param_name>`) can be a **single dictionary** or a **list of dictionaries**.
"""
