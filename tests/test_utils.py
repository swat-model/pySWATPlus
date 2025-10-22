import pySWATPlus
import pytest


@pytest.mark.parametrize(
    'value,expected',
    [
        # Zero
        (0, '               0'),

        # Integers
        (1, '               1'),
        (-1, '              -1'),

        # Positive decimals
        (3.14159265359, '   3.14159265359'),
        (0.00012345, '      0.00012345'),

        # Positive decimals
        (-3.14159265359, '  -3.14159265359'),
        (-0.00012345, '     -0.00012345'),


        # Large integers too big → scientific notation
        (12345678901234567890, '    1.234568e+19'),
        (-12345678901234567890, '   -1.234568e+19'),

        # Edge: exactly 15 digits
        (123456789012345, ' 123456789012345'),
        (-12345678901234, ' -12345678901234'),
    ]
)
def test_calibration_val_field_str(
    value,
    expected
):

    result = pySWATPlus.utils._calibration_val_field_str(value)

    # Check total length = 16
    assert len(result) == 16

    # Check output matches expected string
    assert result == expected


def test_dict_units_compact():

    # --- empty input ---
    assert pySWATPlus.utils._dict_units_compact([]) == []

    # --- id 0 in array ---
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.utils._dict_units_compact([0, 1])
    assert exc_info.value.args[0] == 'All unit IDs must be 1-based (Fortran-style).'

    # --- single element ---
    assert pySWATPlus.utils._dict_units_compact([1]) == [1]

    # --- consecutive sequence ---
    assert pySWATPlus.utils._dict_units_compact([1, 2, 3, 4]) == [1, -4]

    # --- non-consecutive numbers ---
    assert pySWATPlus.utils._dict_units_compact([1, 2, 3, 5]) == [1, -3, 5]

    # --- unordered input ---
    assert pySWATPlus.utils._dict_units_compact([5, 2, 4, 1, 3]) == [1, -5]

    # --- input with duplicates ---
    assert pySWATPlus.utils._dict_units_compact([3, 3, 1, 1, 2]) == [1, -3]

    # --- large range ---
    large_range = list(range(1, 1001))
    assert pySWATPlus.utils._dict_units_compact(large_range) == [1, -1000]

    # --- single non-consecutive elements ---
    assert pySWATPlus.utils._dict_units_compact([1, 2, 4, 6]) == [1, -2, 4, 6]
