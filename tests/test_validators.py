import pySWATPlus
import pytest
import os
import tempfile
from pySWATPlus.types import ParamModel
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


def test_validate_cal_parameters(txtinout_reader):

    # ---------------------------
    # CONDITIONS validation tests
    # ---------------------------

    # --- Case 1: parameter exists (cn2) ---
    par_change = [ParamModel(**{'name': 'cn2', 'value': 0.5, 'change_type': 'absval'})]

    # Should not raise
    pySWATPlus.validators._validate_cal_parameters(txtinout_reader.root_folder, par_change)

    # --- Case 2: parameter does not exist ---
    par_change = [ParamModel(**{'name': 'obj_that_doesnt_exist', 'value': 0.5, 'change_type': 'absval'})]

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


def test_validate_units(
    txtinout_reader
):

    # parameter that support units
    par_change = ParamModel(name="cn2", change_type="pctchg", value=-50, units=[1, 2, 3])
    pySWATPlus.validators._validate_units(par_change, txtinout_reader.root_folder)

    # parameter that support units with range
    par_change = ParamModel(name="cn2", change_type="pctchg", value=-50, units=range(1, 4))
    pySWATPlus.validators._validate_units(par_change, txtinout_reader.root_folder)

    # parameter that support units with set
    par_change = ParamModel(name="cn2", change_type="pctchg", value=-50, units={1, 2, 3})
    pySWATPlus.validators._validate_units(par_change, txtinout_reader.root_folder)

    # Parameter that does not support units
    par_change = ParamModel(name="organicn", change_type="pctchg", value=-50, units=[1, 2, 3])
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

    par_change = ParamModel(name="cn2", change_type="pctchg", value=-50, units=[len(df) + 1])

    with pytest.raises(Exception) as exc_info:
        pySWATPlus.validators._validate_units(par_change, txtinout_reader.root_folder)
    assert "Invalid units for parameter" in exc_info.value.args[0]


def test_validate_conditions(txtinout_reader):
    folder = txtinout_reader.root_folder

    # Case 1: No conditions → pass
    param_change = ParamModel(name="cn2", change_type="pctchg", value=-50)
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

    param_change = ParamModel(name="cn2", change_type="pctchg", value=-50, conditions=conditions)
    pySWATPlus.validators._validate_conditions(param_change, folder)

    # Case 3: Unsupported condition name
    conditions = {
        "invalid_cond": ["A", "B"],
    }

    param_change = ParamModel(name="cn2", change_type="pctchg", value=-50, conditions=conditions)

    with pytest.raises(ValueError) as exc_info:
        pySWATPlus.validators._validate_conditions(param_change, folder)
    assert "is not supported" in str(exc_info.value)

    # Case 4: Invalid value for supported condition
    conditions = {
        "hsg": ["invalid"],
    }

    param_change = ParamModel(name="cn2", change_type="pctchg", value=-50, conditions=conditions)

    with pytest.raises(ValueError) as exc_info:
        pySWATPlus.validators._validate_conditions(param_change, folder)
    assert "has invalid value" in str(exc_info.value)

    conditions = {
        "texture": ["invalid"],
    }

    param_change = ParamModel(name="cn2", change_type="pctchg", value=-50, conditions=conditions)

    with pytest.raises(ValueError) as exc_info:
        pySWATPlus.validators._validate_conditions(param_change, folder)
    assert "has invalid value" in str(exc_info.value)

    conditions = {
        "plant": ["invalid"],
    }

    param_change = ParamModel(name="cn2", change_type="pctchg", value=-50, conditions=conditions)

    with pytest.raises(ValueError) as exc_info:
        pySWATPlus.validators._validate_conditions(param_change, folder)
    assert "has invalid value" in str(exc_info.value)

    conditions = {
        "landuse": ["invalid"],
    }

    param_change = ParamModel(name="cn2", change_type="pctchg", value=-50, conditions=conditions)

    with pytest.raises(ValueError) as exc_info:
        pySWATPlus.validators._validate_conditions(param_change, folder)
    assert "has invalid value" in str(exc_info.value)
