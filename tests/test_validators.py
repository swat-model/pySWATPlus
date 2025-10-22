import pySWATPlus
import pytest
import os
import pandas


@pytest.fixture(scope='class')
def txtinout_reader():

    # TxtInOut direcotry path
    tio_dir = os.path.join(os.path.dirname(__file__), 'TxtInOut')

    # Initialize TxtinoutReader class
    output = pySWATPlus.TxtinoutReader(
        tio_dir=tio_dir
    )

    yield output


def test_calibration_parameters(
    txtinout_reader
):

    # Pass: parameter exists
    parameters = [
        pySWATPlus.newtype.ModifyDict(**{'name': 'cn2', 'value': 0.5, 'change_type': 'absval'})
    ]
    pySWATPlus.validators._calibration_parameters(
        input_dir=txtinout_reader.root_dir,
        parameters=parameters
    )

    # Error: parameter does not exist
    parameters = [
        pySWATPlus.newtype.ModifyDict(**{'name': 'obj_that_doesnt_exist', 'value': 0.5, 'change_type': 'absval'})
    ]
    with pytest.raises(ValueError, match='obj_that_doesnt_exist'):
        pySWATPlus.validators._calibration_parameters(
            input_dir=txtinout_reader.root_dir,
            parameters=parameters
        )


def test_calibration_units(
    txtinout_reader
):

    # Pass: parameter that supports units
    param_change = pySWATPlus.newtype.ModifyDict(name='cn2', change_type='pctchg', value=-50, units=[1, 2, 3])
    pySWATPlus.validators._calibration_units(
        input_dir=txtinout_reader.root_dir,
        param_change=param_change
    )

    # Pass: parameter that supports units with range
    param_change = pySWATPlus.newtype.ModifyDict(name='cn2', change_type='pctchg', value=-50, units=range(1, 4))
    pySWATPlus.validators._calibration_units(
        input_dir=txtinout_reader.root_dir,
        param_change=param_change
    )

    # Pass: parameter that supports units with set
    param_change = pySWATPlus.newtype.ModifyDict(name='cn2', change_type='pctchg', value=-50, units={1, 2, 3})
    pySWATPlus.validators._calibration_units(
        input_dir=txtinout_reader.root_dir,
        param_change=param_change
    )

    # Error: Parameter that does not support units
    param_change = pySWATPlus.newtype.ModifyDict(name='organicn', change_type='pctchg', value=-50, units=[1, 2, 3])
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.validators._calibration_units(
            input_dir=txtinout_reader.root_dir,
            param_change=param_change
        )
    assert 'does not support "units" key' in exc_info.value.args[0]

    # Error: check units that does not exist
    df = pandas.read_csv(
        filepath_or_buffer=txtinout_reader.root_dir / 'hru-data.hru',
        skiprows=1,
        sep=r'\s+',
        usecols=['id']
    )
    param_change = pySWATPlus.newtype.ModifyDict(name='cn2', change_type='pctchg', value=-50, units=[len(df) + 1])
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.validators._calibration_units(
            input_dir=txtinout_reader.root_dir,
            param_change=param_change
        )
    assert 'Invalid units for parameter' in exc_info.value.args[0]


def test_calibration_conditions(
    txtinout_reader
):

    # Pass: No conditions
    param_change = pySWATPlus.newtype.ModifyDict(name="cn2", change_type="pctchg", value=-50)
    pySWATPlus.validators._calibration_conditions(
        input_dir=txtinout_reader.root_dir,
        param_change=param_change
    )

    # Pass: Supported conditions with valid values
    df_textures = pandas.read_fwf(txtinout_reader.root_dir / 'soils.sol', skiprows=1)
    valid_textures = df_textures['texture'].dropna().unique()

    df_plants = pandas.read_fwf(txtinout_reader.root_dir / 'plants.plt', sep=r'\s+', skiprows=1)
    valid_plants = df_plants['name'].dropna().unique()

    df_landuse = pandas.read_csv(txtinout_reader.root_dir / 'landuse.lum', sep=r'\s+', skiprows=1)
    valid_landuse = df_landuse['plnt_com'].dropna().unique()

    conditions = {
        'hsg': ['A', 'B'],
        'texture': [valid_textures[0]],
        'plant': [valid_plants[0]],
        'landuse': [valid_landuse[0]]
    }

    param_change = pySWATPlus.newtype.ModifyDict(name='cn2', change_type='pctchg', value=-50, conditions=conditions)
    pySWATPlus.validators._calibration_conditions(
        input_dir=txtinout_reader.root_dir,
        param_change=param_change
    )

    # Error: Unsupported condition name
    conditions = {
        'invalid_cond': ['A', 'B'],
    }

    param_change = pySWATPlus.newtype.ModifyDict(name='cn2', change_type='pctchg', value=-50, conditions=conditions)
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.validators._calibration_conditions(
            input_dir=txtinout_reader.root_dir,
            param_change=param_change
        )
    assert 'is not supported' in exc_info.value.args[0]

    # Error: Invalid value for supported condition

    conditions = {
        'hsg': ['invalid'],
    }
    param_change = pySWATPlus.newtype.ModifyDict(name='cn2', change_type='pctchg', value=-50, conditions=conditions)
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.validators._calibration_conditions(
            input_dir=txtinout_reader.root_dir,
            param_change=param_change
        )
    assert 'has invalid value' in exc_info.value.args[0]

    conditions = {
        'texture': ['invalid'],
    }
    param_change = pySWATPlus.newtype.ModifyDict(name='cn2', change_type='pctchg', value=-50, conditions=conditions)
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.validators._calibration_conditions(
            input_dir=txtinout_reader.root_dir,
            param_change=param_change
        )
    assert 'has invalid value' in exc_info.value.args[0]

    conditions = {
        'plant': ['invalid'],
    }
    param_change = pySWATPlus.newtype.ModifyDict(name='cn2', change_type='pctchg', value=-50, conditions=conditions)
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.validators._calibration_conditions(
            input_dir=txtinout_reader.root_dir,
            param_change=param_change
        )
    assert 'has invalid value' in exc_info.value.args[0]

    conditions = {
        'landuse': ['invalid'],
    }
    param_change = pySWATPlus.newtype.ModifyDict(name='cn2', change_type='pctchg', value=-50, conditions=conditions)
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.validators._calibration_conditions(
            input_dir=txtinout_reader.root_dir,
            param_change=param_change
        )
    assert 'has invalid value' in exc_info.value.args[0]
