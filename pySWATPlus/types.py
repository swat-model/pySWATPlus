# types.py
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
Defines parameter modifications for one or more SWAT+ input files.

Each key is a SWAT+ input filename (e.g., `plants.plt`). The value is a dictionary
mapping variable names in that file to parameter changes.

The structure is as follows:
```python
{
    "<filename>": {
        "has_units": bool,  # optional
        "<variable_name>": {
            "value": float,
            "change_type": "absval" | "abschg" | "pctchg",  # optional
            "filter_by": str  # optional
        }
        # OR a list of such dictionaries
    },
    ...
}
```

Details:
    - "value": The numeric value to apply.
    - "change_type" (optional):
        - "absval": Set the value directly (default).
        - "abschg": Apply an absolute change (e.g., +10).
        - "pctchg": Apply a percentage change (e.g., +10%).
    - "filter_by" (optional): A pandas `.query()` string to filter rows in the input file.
    - "has_units" (optional): Optional. Whether the file has units information (default is False)

    Set to `None` if no parameter modifications are required.
    
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
