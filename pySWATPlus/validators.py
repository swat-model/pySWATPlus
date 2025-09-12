import typing
import types


def _variable_origin_static_type(
    vars_types: dict[str, typing.Any],
    vars_values: dict[str, typing.Any]
) -> None:

    '''
    Validates input variables against their expected types.
    '''

    # iterate name and type of method variables
    for v_name, v_type in vars_types.items():
        # continute if varibale name is return
        if v_name == 'return':
            continue
        # get origin type and value of the variable
        type_origin = typing.get_origin(v_type)
        type_value = vars_values[v_name]
        # if origin type in None
        if type_origin is None:
            if not isinstance(type_value, v_type):
                raise TypeError(
                    f'Expected "{v_name}" to be "{v_type.__name__}", but got type "{type(type_value).__name__}"'
                )
        # if origin type in not None
        else:
            # if origin type is a Union
            if type_origin in (typing.Union, types.UnionType):
                # get argument types
                type_args = tuple(
                    typing.get_origin(arg) or arg for arg in typing.get_args(v_type)
                )
                if not isinstance(type_value, type_args):
                    type_expect = [t.__name__ for t in type_args]
                    raise TypeError(
                        f'Expected "{v_name}" to be one of {type_expect}, but got type "{type(type_value).__name__}"'
                    )
            # if origin type in not a Union
            else:
                if not isinstance(type_value, type_origin):
                    raise TypeError(
                        f'Expected "{v_name}" to be "{type_origin.__name__}", but got type "{type(type_value).__name__}"'
                    )

    return None


# def _calibration_parameter_config(
#     parameters: list[dict[str, typing.Any]]
# ) -> None:

#     params_type = {
#         'name': str,
#         'value': int | float,
#         'change_type': str,
#         'units': collections.abc.Iterable,
#         'conditions': dict
#     }

#     req_keys = [
#         'name',
#         'value',
#         'change_type'
#     ]

#     change_type = [
#         'absval',
#         'abschg',
#         'pctchg'
#     ]

#     conditions_keys = [
#         'hsg',
#         'texture',
#         'plant',
#         'landuse'
#     ]

#     for i_dict in  parameters:
#         # check parameter types
#         try:
#             _variable_origin_static_type(
#                 vars_types={k: v for k, v in params_type.items() if k in i_dict},
#                 vars_values=i_dict
#             )
#         except TypeError as err:
#             print(f'Validation failed for this dictionary: {i_dict}')
#             raise
#         # check required keys
#         unavail_key = [
#             rk for rk in req_keys if rk not in i_dict
#         ]
#         if len(unavail_key) > 0:
#             print(f'Validation failed for dictionary: {i_dict}')
#             raise KeyError(
#                 f'Required keys "[{', '.join(unavail_key)}]" are not available'
#             )
#         if i_dict['change_type'] not in change_type:
#             print(f'Validation failed for dictionary: {i_dict}')
#             raise ValueError(
#                 f'Invalid {i_dict['change_type']} value for "change_type" keys; valid values are {change_type}'
#             )
#         if 'units' in i_dict:
#             if len(i_dict['units']) == 0:
#                 print(f'Validation failed for this dictionary: {i_dict}')
#                 raise ValueError(
#                     'Iterable value for the "units" key cannot be empty'
#                 )
#             # Check that all elements are integers and >= 0
#             if not all(isinstance(unit, int) and unit >= 0 for unit in i_dict['units']):
#                 print(f'Validation failed for this dictionary: {i_dict}')
#                 raise ValueError(
#                     'All elements in "units" must be integers >= 0'
#                 )
#         if 'conditions' in i_dict:
#             if len(i_dict['conditions']) == 0:
#                 print(f'Validation failed for this dictionary: {i_dict}')
#                 raise ValueError(
#                     'Dictionary value for the "conditions" key cannot be empty'
#                 )
#             for key, value in i_dict['conditions'].items():
#                 print(f'Validation failed for this dictionary: {i_dict}')
#                 if key not in conditions_keys:
#                     raise KeyError(
#                         f'Invalid key "{key}" in "condtions" dictionary; expected keys are [{', '.join(conditions_keys)}]'
#                     )

#     return None
