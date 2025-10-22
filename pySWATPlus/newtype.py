import typing
import typing_extensions  # only for Python 3.10 and will be removed in future
import pydantic


class BaseDict(pydantic.BaseModel):
    name: str
    change_type: typing.Literal['absval', 'abschg', 'pctchg']
    units: typing.Optional[list[int]] = None
    conditions: typing.Optional[dict[str, list[str]]] = None

    @pydantic.model_validator(mode='after')
    def validate_units(
        self
    ) -> typing_extensions.Self:

        # Check that all units are greater than 0
        if self.units is not None and any(num <= 0 for num in self.units):
            raise ValueError(
                f'For parameter "{self.name}": all values for "units" must be > 0, got {list(self.units)}'
            )

        return self


class ModifyDict(BaseDict):
    value: float


class BoundDict(BaseDict):
    upper_bound: float
    lower_bound: float

    @pydantic.model_validator(mode='after')
    def check_bounds(
        self
    ) -> typing_extensions.Self:

        if self.upper_bound <= self.lower_bound:
            raise ValueError(
                f'For parameter "{self.name}": upper_bound={self.upper_bound} must be greater than lower_bound={self.lower_bound}'
            )

        return self


ModifyType: typing.TypeAlias = list[dict[str, typing.Any]]
'''
A list of dictionaries specifying parameter changes in the `calibration.cal` file.
Each dictionary contain the following keys:

- `name` (str): **Required.** Name of the parameter in the `cal_parms.cal` file.
- `change_type` (str): **Required.** Type of change to apply. Must be one of `absval`, `abschg`, or `pctchg`.
- `value` (float): **Required.** Value of the parameter.
- `units` (Iterable[int]): Optional. List of unit IDs to which the parameter change should be constrained.
- `conditions` (dict[str, list[str]]): Optional. Conditions to apply when changing the parameter.
  Supported keys include `'hsg'`, `'texture'`, `'plant'`, and `'landuse'`, each mapped to a list of allowed values.
'''

BoundType: typing.TypeAlias = list[dict[str, typing.Any]]
'''
A list of dictionaries defining parameter configurations for sensitivity simulations.
Each dictionary contain the following keys:

- `name` (str): **Required.** Name of the parameter in the `cal_parms.cal` file.
- `change_type` (str): **Required.** Type of change to apply. Must be one of `absval`, `abschg`, or `pctchg`.
- `lower_bound` (float): **Required.** Lower bound for the parameter.
- `upper_bound` (float): **Required.** Upper bound for the parameter.
- `units` (Iterable[int]): Optional. List of unit IDs to which the parameter change should be constrained.
- `conditions` (dict[str, list[str]]): Optional. Conditions to apply when changing the parameter.
  Supported keys include `'hsg'`, `'texture'`, `'plant'`, and `'landuse'`, each mapped to a list of allowed values.
'''
