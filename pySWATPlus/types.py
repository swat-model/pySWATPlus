import typing
import typing_extensions


class ParamChange(
    typing.TypedDict
):

    '''
    Describes a dictionary structure to change a parameter value in an input file of the SWAT+ model.

    Attributes:
        value (float): The value to apply to the parameter.

        change_type (str): An optional key with a string value that specifies the type of change to apply, with options:

            - `'absval'`: Use the absolute value (default).
            - `'abschg'`: Apply an absolute change (e.g., -0.5).
            - `'pctchg'`: Apply a percentage change (e.g., +10%).

        filter_by (str): An optional key with a string value that filters `DataFrame` rows using `.query()` syntax.
    '''

    value: float
    change_type: typing_extensions.NotRequired[typing.Literal['absval', 'abschg', 'pctchg']]
    filter_by: typing_extensions.NotRequired[str]


ParamSpec = ParamChange | list[ParamChange]

'''
Represents one or more parameter value changes,
specified as either a single `ParamChange` or a list of them.
'''

FileParams = dict[str, bool | ParamSpec]

'''
Maps a parameter from an input file (e.g., `bm_e` from `plants.plt` or `epco` from `hydrology.hyd`)
to the SWAT+ model as either a single `ParamChange` or a list of them.

Special key:
    - `'has_units'` (bool): Key indicating whether the
            input file contains a row of units for columns.

Example:
```python
# Example from `plants.plt` file with a list of `ParamChange` objects
{
    'has_units': False,
    'bm_e': [
        {'value': 100, 'change_type': 'absval'},
        {'value': 110, 'filter_by': 'name == "almd"'}
    ]
}

# Example from `hydrology.hyd` file with a single `ParamChange` object
{
    'has_units': False,
    'epco': {'value': 0.5, 'change_type': 'absval'}
}
```
'''

ParamsType = dict[str, FileParams]

'''
Defines parameter modifications for one or more input files to the SWAT+ model.
Each key is a input filename and the value is a `FileParams` object.

The structure is as follows:
```python
{
    '<file_1>': {
        'has_units': bool,
        '<variable_1>': {
            'value': float,
            'change_type': 'absval' | 'abschg' | 'pctchg',  # optional (default 'absval')
            'filter_by': str  # optional
        }
        # OR a list of such dictionaries
    },
    '<file_2>': {
        'has_units': bool,
        '<variable_21>': {'value': float},
        '<variable_22>': {'value': float, 'change_type': 'abschg'}
    },
    '<file_3>': {
        'has_units': bool,
        '<variable_3>': [
            {'value': float, 'change_type': 'absval', 'filter_by': '<query_31>'},
            {'value': float, 'change_type': 'pctchg', 'filter_by': '<query_32>'},
        ],
    },
    # More file keys mapped to corresponding FileParams objects
}
```

Example:
```python
params={
    'plants.plt': {
        'has_units': False,
        'bm_e': [
            {'value': 100, 'change_type': 'absval', 'filter_by': 'name == "agrl"'},
            {'value': 110, 'change_type': 'absval', 'filter_by': 'name == "almd"'},
        ],
    },
    'hydrology.hyd': {
        'has_units': False,
        'epco': {'value': 0.25, 'change_type': 'abschg'},
        'perco': {'value': 0.1, 'change_type': 'absval'}
    }
}
```
'''
