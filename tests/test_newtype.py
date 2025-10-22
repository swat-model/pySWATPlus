import pytest
import pySWATPlus


def test_error_basedict():

    # Error: unit value is less than or equal to 0
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.newtype.BaseDict(
            name='esco',
            change_type='absval',
            units=[-1, 0, 2]
        )
    assert 'For parameter "esco": all values for "units" must be > 0' in str(exc_info.value)


def test_error_bounddict():

    # Error: upper_bound is smaller than lower_bound in BoundDict
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.newtype.BoundDict(
            name='perco',
            change_type='absval',
            lower_bound=1.0,
            upper_bound=0.5
        )
    assert 'For parameter "perco": upper_bound=0.5 must be greater than lower_bound=1.0' in str(exc_info.value)


def test_error_parameters():

    # Error: invalid key in "parameters" list for ModifyDict type
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.utils._parameters_modify_dict_list(
            parameters=[
                {
                    'name': 'perco',
                    'val': 0.3,
                    'change_type': 'pctchg'
                }
            ]
        )
    assert 'Invalid key "val"' in exc_info.value.args[0]

    # Error: invalid key in "parameters" list for BoundDict type
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.utils._parameters_bound_dict_list(
            parameters=[
                {
                    'name': 'perco',
                    'change_type': 'pctchg',
                    'lower_boundd': 0,
                    'upper_bound': 1
                }
            ]
        )
    assert 'Invalid key "lower_boundd"' in exc_info.value.args[0]
