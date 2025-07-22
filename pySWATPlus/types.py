from typing import TypedDict, Literal
from typing_extensions import NotRequired


class ParamChange(
    TypedDict
):

    """
    Describes a single change to apply to a parameter in a SWAT input file.

    Attributes:
        value (float): The value to apply to the parameter.
        change_type (Literal['absval', 'abschg', 'pctchg'], optional):
            - `'absval'`: Use the absolute value (default).
            - `'abschg'`: Apply an absolute change.
            - `'pctchg'`: Apply a percentage change.
        filter_by (str, optional): Pandas `.query()` string to filter the dataframe rows.
    """
    value: float
    change_type: NotRequired[Literal['absval', 'abschg', 'pctchg']]
    filter_by: NotRequired[str]


ParamSpec = ParamChange | list[ParamChange]

"""
One or more parameter changes to apply to a SWAT variable.

Can be a single `ParamChange` or a list of them.
"""

FileParams = dict[str, bool | ParamSpec]

"""
Maps a SWAT+ input file’s variables to their parameter changes.

Special key:
    - `"has_units"` (bool): Indicates if the file has units (default is False).

All other keys are variable names (e.g., `"bm_e"`, `"CN2"`) mapped to:
    - A `ParamChange`, or
    - A list of `ParamChange`s.

Example:
```python
{
    'has_units': False,
    'bm_e': [
        {'value': 100, 'change_type': 'absval'},
        {'value': 110, 'filter_by': 'name == "almd"'}
    ]
}
```
"""

ParamsType = dict[str, FileParams] | None

"""
Top-level structure mapping SWAT input filenames to parameter modifications.

Each file maps to:
    - `"has_units"`: Whether it contains multiple blocks (optional).
    - Variable names: Mapped to one or more parameter changes.

Example:
```python
params = {
    'plants.plt': {
        'has_units': False,
        'bm_e': [
            {'value': 100, 'change_type': 'absval', 'filter_by': 'name == "agrl"'},
            {'value': 110, 'change_type': 'absval', 'filter_by': 'name == "almd"'},
        ],
    },
}
```
"""
