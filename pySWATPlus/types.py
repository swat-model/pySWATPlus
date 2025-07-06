# types.py
from typing import TypedDict, Literal, Optional, Union, Dict, List

class ParamChange(TypedDict, total=False):
    """
    Defines a single change to apply to a SWAT input parameter.

    Attributes:
        value (float): 
            The new value to apply.

        change_type (Literal['absval', 'abschg', 'pctchg'], optional): 
            The type of change:
            - 'absval': Replace with absolute value (default if omitted).
            - 'abschg': Add or subtract the specified value.
            - 'pctchg': Apply a percentage change (e.g., 0.10 for +10%).

        filter_by (str, optional): 
            A pandas `.query()` string used to filter rows before applying the change.
    """
    value: float
    change_type: Literal['absval', 'abschg', 'pctchg']
    filter_by: Optional[str]


ParamSpec = Union[ParamChange, List[ParamChange]]
"""
Defines one or more changes to apply to a specific parameter.

- Can be a single `ParamChange` or a list of them.
- Each change is independently applied to the same parameter name.
"""

FileParams = Dict[str, Union[bool, ParamSpec]]
"""
Defines modifications for a specific SWAT input file.

Structure:
    {
        'has_units': bool,                # Optional. True if file contains unit-separated blocks (e.g., HRUs). Defaults to False.
        'parameter_name': ParamSpec       # One or more changes to apply to that parameter.
    }
- Parameter names (e.g., 'CN2', 'SOL_AWC') map to changes.
- If 'has_units' is omitted, it defaults to False.
"""

ParamsType = Optional[Dict[str, FileParams]]
"""
Top-level structure mapping SWAT input filenames to parameter modifications.

Example:
    {
        'plants.plt': {
            'has_units': False,
            'bm_e': [
                {'value': 100, 'change_type': 'absval', 'filter_by': 'name == "agrl"'},
                {'value': 110, 'change_type': 'absval', 'filter_by': 'name == "almd"'},
            ],
        },
    }
"""