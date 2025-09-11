import pySWATPlus
import pytest
import os
import tempfile
from pySWATPlus.types import CalParamModel
import pandas


@pytest.fixture(scope='class')
def txtinout_reader():

    # set up TxtInOut folder path
    txtinout_folder = os.path.join(os.path.dirname(__file__), 'TxtInOut')

    # initialize TxtinoutReader class
    txtinout_reader = pySWATPlus.TxtinoutReader(
        path=txtinout_folder
    )

    yield txtinout_reader


def test_utils(txtinout_reader):

    # ---------------------------
    # CONDITIONS validation tests
    # ---------------------------

    # --- Case 1: parameter exists (cn2) ---
    par_change = [CalParamModel(**{'name': 'cn2', 'value': 0.5})]

    # Should not raise
    pySWATPlus.validators._validate_cal_parameters(txtinout_reader.root_folder, par_change)

    # --- Case 2: parameter does not exist ---
    par_change = [CalParamModel(**{'name': 'obj_that_doesnt_exist', 'value': 0.5})]

    with pytest.raises(ValueError, match="obj_that_doesnt_exist"):
        pySWATPlus.validators._validate_cal_parameters(txtinout_reader.root_folder, par_change)

    with tempfile.TemporaryDirectory() as tmp1_dir:
        # Initialize TxtinOutReader class by target directory
        target_dir = txtinout_reader.copy_required_files(
            target_dir=tmp1_dir
        )

        # Error if cal_parms.cal does not exist
        cal_parms_path = target_dir / 'cal_parms.cal'
        if cal_parms_path.exists():
            cal_parms_path.unlink()

        with pytest.raises(Exception) as exc_info:
            pySWATPlus.validators._validate_cal_parameters(target_dir, par_change)
        assert exc_info.value.args[0] == 'cal_parms.cal file does not exist in the TxtInOut folder'


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

        file_path = target_reader.root_folder / "file.cio"

        fmt = (
            f"{'{:<18}'}"  # chg
            f"{'{:<18}'}"  # cal_parms.cal / null
            f"{'{:<18}'}"  # calibration.cal
            f"{'{:<18}'}"  # null
            f"{'{:<18}'}"  # null
            f"{'{:<18}'}"  # null
            f"{'{:<18}'}"  # null
            f"{'{:<18}'}"  # null
            f"{'{:<18}'}"  # null
            f"{'{:<18}'}"  # null
            f"{'{:<18}'}"  # null
            f"{'{:<4}'}"   # null
        )

        # --- Test adding calibration line ---
        target_reader._add_or_remove_calibration_cal_to_file_cio(add=True)
        lines = file_path.read_text().splitlines()
        expected_line = fmt.format(
            "chg", "cal_parms.cal", "calibration.cal", *["null"] * 9
        )
        assert lines[21] == expected_line

        # --- Test removing calibration line ---
        target_reader._add_or_remove_calibration_cal_to_file_cio(add=False)
        lines = file_path.read_text().splitlines()

        expected_line = fmt.format(
            "chg", "null", "calibration.cal", *["null"] * 9
        )
        assert lines[21] == expected_line


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
        par_change = [CalParamModel(**{'name': 'cn2', 'value': -50.0, "change_type": "pctchg"})]

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


def test_validate_units(
    txtinout_reader
):

    # parameter that support units
    par_change = CalParamModel(name="cn2", change_type="pctchg", value=-50, units=[1, 2, 3])
    pySWATPlus.validators._validate_units(par_change, txtinout_reader.root_folder)

    # parameter that support units with range
    par_change = CalParamModel(name="cn2", change_type="pctchg", value=-50, units=range(1, 4))
    pySWATPlus.validators._validate_units(par_change, txtinout_reader.root_folder)

    # parameter that support units with set
    par_change = CalParamModel(name="cn2", change_type="pctchg", value=-50, units={1, 2, 3})
    pySWATPlus.validators._validate_units(par_change, txtinout_reader.root_folder)

    # Parameter that does not support units
    par_change = CalParamModel(name="organicn", change_type="pctchg", value=-50, units=[1, 2, 3])
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.validators._validate_units(par_change, txtinout_reader.root_folder)
    assert "does not support units" in exc_info.value.args[0]

    # check units that does not exist
    df = pandas.read_csv(
        filepath_or_buffer=txtinout_reader.root_folder / 'hru-data.hru',
        skiprows=1,
        sep=r'\s+',
        usecols=['id']
    )

    par_change = CalParamModel(name="cn2", change_type="pctchg", value=-50, units=[len(df) + 1])

    with pytest.raises(Exception) as exc_info:
        pySWATPlus.validators._validate_units(par_change, txtinout_reader.root_folder)
    assert "Invalid units for parameter" in exc_info.value.args[0]


def test_validate_conditions(txtinout_reader):
    folder = txtinout_reader.root_folder

    # Case 1: No conditions → pass
    param_change = CalParamModel(name="cn2", change_type="pctchg", value=-50)
    pySWATPlus.validators._validate_conditions(param_change, folder)

    # Case 2: Supported conditions with valid values

    # Patch soils.sol
    df_textures = pandas.read_fwf(folder / 'soils.sol', skiprows=1)
    valid_textures = df_textures['texture'].dropna().unique()

    # Patch plants.plt
    df_plants = pandas.read_fwf(folder / 'plants.plt', sep=r'\s+', skiprows=1)
    valid_plants = df_plants['name'].dropna().unique()

    # Patch landuse.lum
    df_landuse = pandas.read_csv(folder / 'landuse.lum', sep=r'\s+', skiprows=1)
    valid_landuse = df_landuse['plnt_com'].dropna().unique()

    conditions = {
        "hsg": ["A", "B"],
        "texture": [valid_textures[0]],
        "plant": [valid_plants[0]],
        "landuse": [valid_landuse[0]]
    }

    param_change = CalParamModel(name="cn2", change_type="pctchg", value=-50, conditions=conditions)
    pySWATPlus.validators._validate_conditions(param_change, folder)

    # Case 3: Unsupported condition name
    conditions = {
        "invalid_cond": ["A", "B"],
    }

    param_change = CalParamModel(name="cn2", change_type="pctchg", value=-50, conditions=conditions)

    with pytest.raises(ValueError) as exc_info:
        pySWATPlus.validators._validate_conditions(param_change, folder)
    assert "is not supported" in str(exc_info.value)

    # Case 4: Invalid value for supported condition
    conditions = {
        "hsg": ["invalid"],
    }

    param_change = CalParamModel(name="cn2", change_type="pctchg", value=-50, conditions=conditions)

    with pytest.raises(ValueError) as exc_info:
        pySWATPlus.validators._validate_conditions(param_change, folder)
    assert "has invalid value" in str(exc_info.value)

    conditions = {
        "texture": ["invalid"],
    }

    param_change = CalParamModel(name="cn2", change_type="pctchg", value=-50, conditions=conditions)

    with pytest.raises(ValueError) as exc_info:
        pySWATPlus.validators._validate_conditions(param_change, folder)
    assert "has invalid value" in str(exc_info.value)

    conditions = {
        "plant": ["invalid"],
    }

    param_change = CalParamModel(name="cn2", change_type="pctchg", value=-50, conditions=conditions)

    with pytest.raises(ValueError) as exc_info:
        pySWATPlus.validators._validate_conditions(param_change, folder)
    assert "has invalid value" in str(exc_info.value)

    conditions = {
        "landuse": ["invalid"],
    }

    param_change = CalParamModel(name="cn2", change_type="pctchg", value=-50, conditions=conditions)

    with pytest.raises(ValueError) as exc_info:
        pySWATPlus.validators._validate_conditions(param_change, folder)
    assert "has invalid value" in str(exc_info.value)
