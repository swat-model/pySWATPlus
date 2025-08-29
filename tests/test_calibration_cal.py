import pySWATPlus
import pytest
import os
import tempfile


@pytest.fixture(scope='class')
def txtinout_reader():

    # set up TxtInOut folder path
    txtinout_folder = os.path.join(os.path.dirname(__file__), 'TxtInOut')

    # initialize TxtinoutReader class
    txtinout_reader = pySWATPlus.TxtinoutReader(
        path=txtinout_folder
    )

    yield txtinout_reader


def test_utils():

    # --- pass test for None input ---
    output = pySWATPlus.utils._validate_calibration_params(params=None)
    assert output is None

    # --- error test for input not dict/list ---
    with pytest.raises(TypeError) as exc_info:
        pySWATPlus.utils._validate_calibration_params(params="not-a-dict")
    assert 'expected a dict' in str(exc_info.value)

    # --- error test for missing "name" ---
    with pytest.raises(KeyError) as exc_info:
        pySWATPlus.utils._validate_calibration_params(params={"value": 1.23})
    assert 'missing required key "name"' in str(exc_info.value)

    # --- error test for missing "value" ---
    with pytest.raises(KeyError) as exc_info:
        pySWATPlus.utils._validate_calibration_params(params={"name": "alpha"})
    assert 'missing required key "value"' in str(exc_info.value)

    # --- error test for "name" not a string ---
    with pytest.raises(TypeError) as exc_info:
        pySWATPlus.utils._validate_calibration_params(params={"name": 123, "value": 1.23})
    assert '"name" must be a string' in str(exc_info.value)

    # --- error test for "value" not numeric ---
    with pytest.raises(TypeError) as exc_info:
        pySWATPlus.utils._validate_calibration_params(params={"name": "alpha", "value": "oops"})
    assert '"value" must be int or float' in str(exc_info.value)

    # --- error test for invalid change_type ---
    with pytest.raises(ValueError) as exc_info:
        pySWATPlus.utils._validate_calibration_params(params={"name": "beta", "value": 0.5, "change_type": "invalid"})
    assert 'invalid change_type "invalid"' in str(exc_info.value)

    # --- pass test for valid single dict ---
    output = pySWATPlus.utils._validate_calibration_params(params={"name": "alpha", "value": 1.23, "change_type": "absval"})
    assert output is None

    # --- pass test for valid list of dicts ---
    output = pySWATPlus.utils._validate_calibration_params(params=[
        {"name": "cn2", "value": 45},
        {"name": "slope_len", "value": 5.0, "change_type": "pctchg"}
    ])
    assert output is None

    # --- pass test: valid list of units ---
    output = pySWATPlus.utils._validate_calibration_params(params={
        "name": "alpha",
        "value": 1.0,
        "units": [1, 2, 3]
    })
    assert output is None

    # --- pass test: valid range of units ---
    output = pySWATPlus.utils._validate_calibration_params(params={
        "name": "beta",
        "value": 2.0,
        "units": range(0, 5)
    })
    assert output is None

    # --- error test: units contains negative IDs ---
    with pytest.raises(ValueError) as exc_info:
        pySWATPlus.utils._validate_calibration_params(params={
            "name": "delta",
            "value": 1.0,
            "units": [0, -1, 2]
        })
    assert 'all elements in "units" must be integers >= 0' in str(exc_info.value)

    # --- error test: units contains non-integer ---
    with pytest.raises(ValueError) as exc_info:
        pySWATPlus.utils._validate_calibration_params(params={
            "name": "epsilon",
            "value": 1.0,
            "units": [0, 1.5, 2]
        })
    assert 'all elements in "units" must be integers >= 0' in str(exc_info.value)

    # --- error test: units is not iterable ---
    with pytest.raises(TypeError) as exc_info:
        pySWATPlus.utils._validate_calibration_params(params={
            "name": "zeta",
            "value": 1.0,
            "units": 123
        })
    assert '"units" must be an iterable of integers' in str(exc_info.value)


@pytest.mark.parametrize(
    "value,expected",
    [
        # Zero
        (0, "               0"),

        # Integers
        (1, "               1"),
        (-1, "              -1"),

        # Positive decimals
        (3.14159265359, "   3.14159265359"),
        (0.00012345, "      0.00012345"),

        # Positive decimals
        (-3.14159265359, "  -3.14159265359"),
        (-0.00012345, "     -0.00012345"),


        # Large integers too big → scientific notation
        (12345678901234567890, "    1.234568e+19"),
        (-12345678901234567890, "   -1.234568e+19"),

        # Edge: exactly 15 digits
        (123456789012345, " 123456789012345"),
        (-12345678901234, " -12345678901234"),
    ]
)
def test_format_val_field_edge_cases(value, expected):
    result = pySWATPlus.utils._format_val_field(value)

    # Check total length = 16
    assert len(result) == 16

    # Check output matches expected string
    assert result == expected


def test_add_or_remove_calibration_cal_to_file_cio(
    txtinout_reader
):

    with tempfile.TemporaryDirectory() as tmp1_dir:
        # Intialize TxtinOutReader class by target direcotry
        target_dir = txtinout_reader.copy_required_files(
            target_dir=tmp1_dir
        )
        target_reader = pySWATPlus.TxtinoutReader(
            path=target_dir
        )

        # --- Test adding calibration line ---
        target_reader._add_or_remove_calibration_cal_to_file_cio(add=True)
        file_path = target_reader.root_folder / "file.cio"
        lines = file_path.read_text().splitlines()

        expected_add_line = (
            "chg               cal_parms.cal     calibration.cal   null              "
            "null              null              null              null              "
            "null              null              null              null"
        )
        assert lines[21] == expected_add_line

        # --- Test removing calibration line ---
        target_reader._add_or_remove_calibration_cal_to_file_cio(add=False)
        lines = file_path.read_text().splitlines()

        expected_remove_line = (
            "chg               null              calibration.cal   null              "
            "null              null              null              null              "
            "null              null              null              null"
        )
        assert lines[21] == expected_remove_line


def test_check_swatplus_parameters(
    txtinout_reader
):
    with tempfile.TemporaryDirectory() as tmp1_dir:
        # Initialize TxtinOutReader class by target directory
        target_dir = txtinout_reader.copy_required_files(
            target_dir=tmp1_dir
        )
        target_reader = pySWATPlus.TxtinoutReader(
            path=target_dir
        )

        # --- Case 1: parameter exists (cn2) ---
        par_change = [{"name": "cn2"}]
        # Should not raise
        target_reader._check_swatplus_parameters(par_change)

        # --- Case 2: parameter does not exist ---
        par_change = [{"name": "obj_that_doesnt_exist"}]
        with pytest.raises(ValueError, match="obj_that_doesnt_exist"):
            target_reader._check_swatplus_parameters(par_change)

        # Error if cal_parms.cal does not exist
        cal_parms_path = target_dir / 'cal_parms.cal'
        if cal_parms_path.exists():
            cal_parms_path.unlink()

        with pytest.raises(Exception) as exc_info:
            target_reader._check_swatplus_parameters(par_change)
        assert exc_info.value.args[0] == 'cal_parms.cal file does not exist in the TxtInOut folder'


def test_write_calibration_file(
    txtinout_reader
):
    with tempfile.TemporaryDirectory() as tmp1_dir:
        # Initialize TxtinOutReader class by target directory
        target_dir = txtinout_reader.copy_required_files(
            target_dir=tmp1_dir
        )
        target_reader = pySWATPlus.TxtinoutReader(
            path=target_dir
        )

        # Parameter changes: 1 row
        par_change = [{
            "name": "cn2",
            "chg_type": "pctchg",
            "value": -50.0
        }]

        # Run the method
        target_reader._write_calibration_file(par_change)

        # Expected output
        expected_content = (
            "Number of parameters:\n"
            "1\n"
            "NAME        CHG_TYPE             VAL           CONDS    LYR1    LYR2   YEAR1   YEAR2    DAY1    DAY2 OBJ_TOT\n"
            "cn2           pctchg           -50.0               0       0       0       0       0       0       0       0\n"
        )

        # Compare file content
        cal_file = target_reader.root_folder / "calibration.cal"
        content = cal_file.read_text()
        assert content == expected_content


def test_compact_units():
    # --- empty input ---
    assert pySWATPlus.utils._compact_units([]) == []

    # --- id 0 in array ---
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.utils._compact_units([0, 1])
    assert exc_info.value.args[0] == 'All unit IDs must be 1-based (Fortran-style).'

    # --- single element ---
    assert pySWATPlus.utils._compact_units([1]) == [1]

    # --- consecutive sequence ---
    assert pySWATPlus.utils._compact_units([1, 2, 3, 4]) == [1, -4]

    # --- non-consecutive numbers ---
    assert pySWATPlus.utils._compact_units([1, 2, 3, 5]) == [1, -3, 5]

    # --- unordered input ---
    assert pySWATPlus.utils._compact_units([5, 2, 4, 1, 3]) == [1, -5]

    # --- input with duplicates ---
    assert pySWATPlus.utils._compact_units([3, 3, 1, 1, 2]) == [1, -3]

    # --- large range ---
    large_range = list(range(1, 1001))
    assert pySWATPlus.utils._compact_units(large_range) == [1, -1000]

    # --- single non-consecutive elements ---
    assert pySWATPlus.utils._compact_units([1, 2, 4, 6]) == [1, -2, 4, 6]
