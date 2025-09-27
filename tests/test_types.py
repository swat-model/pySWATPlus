import pytest
import pySWATPlus


def test_error_basedict():

    # Error: unit value is less than or equal to 0
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.types.BaseDict(
            name='esco',
            change_type='absval',
            units=[-1, 0, 2]
        )
    assert 'For parameter "esco": all values for "units" must be > 0' in str(exc_info.value)


def test_error_bounddict():

    # Error: upper_bound is smaller than lower_bound in BoundDict
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.types.BoundDict(
            name='perco',
            change_type='absval',
            lower_bound=1.0,
            upper_bound=0.5
        )
    assert 'For parameter "perco": upper_bound=0.5 must be greater than lower_bound=1.0' in str(exc_info.value)
