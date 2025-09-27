import os
import shutil
import pySWATPlus
import pytest
import tempfile


@pytest.fixture(scope='class')
def sensitivity_analyzer():

    # initialize TxtinoutReader class
    sensitivity_analyzer = pySWATPlus.SensitivityAnalyzer()

    yield sensitivity_analyzer


def test_simulation_by_sobol_sample(
    sensitivity_analyzer
):

    # set up TxtInOut folder path
    txtinout_folder = os.path.join(os.path.dirname(__file__), 'TxtInOut')

    # initialize TxtinoutReader class
    txtinout_reader = pySWATPlus.TxtinoutReader(
        path=txtinout_folder
    )

    with tempfile.TemporaryDirectory() as tmp1_dir:
        # Copy required files to a target directory
        target_dir = txtinout_reader.copy_required_files(
            target_dir=tmp1_dir
        )
        # Intialize TxtinOutReader class by target direcotry
        target_reader = pySWATPlus.TxtinoutReader(
            path=target_dir
        )
        # Disable CSV file generation to save time
        target_reader.disable_csv_print()
        # Disable all objects for daily time series file in print.prt to save time and space
        target_reader.enable_object_in_print_prt(
            obj=None,
            daily=False,
            monthly=True,
            yearly=True,
            avann=True
        )
        # Set begin and end year
        target_reader.set_begin_and_end_date(
            begin_date='01-Jan-2010',
            end_date='31-Dec-2012'
        )
        # Set warmup year
        target_reader.set_warmup_year(
            warmup=1
        )
        # Sensitivity parameters
        parameters = [
            {
                'name': 'perco',
                'change_type': 'absval',
                'lower_bound': 0,
                'upper_bound': 1
            }
        ]
        # Target data from sensitivity simulation
        simulation_data = {
            'channel_sdmorph_mon.txt': {
                'has_units': True,
                'ref_day': 15,
                'apply_filter': {'gis_id': [561]},
                'usecols': ['gis_id', 'flo_out']
            },
            'channel_sd_yr.txt': {
                'has_units': True,
                'begin_date': '01-Jun-2011',
                'ref_day': 15,
                'ref_month': 6,
                'apply_filter': {'name': ['cha561'], 'yr': [2012]},
                'usecols': ['gis_id', 'flo_out']
            }
        }
        # Pass: sensitivity simulation by Sobol sample
        with tempfile.TemporaryDirectory() as tmp2_dir:
            output = sensitivity_analyzer.simulation_by_sobol_sample(
                parameters=parameters,
                sample_number=1,
                simulation_folder=tmp2_dir,
                txtinout_folder=tmp1_dir,
                simulation_data=simulation_data
            )
            assert 'time' in output
            assert isinstance(output['time'], dict)
            assert len(output['time']) == 3

            assert 'problem' in output
            assert isinstance(output['problem'], dict)
            assert len(output['problem']) == 3

            assert 'sample' in output
            assert not isinstance(output['sample'], dict)
            assert len(output['sample']) == 8

            assert 'simulation' in output
            assert isinstance(output['simulation'], dict)
            assert len(output['simulation']) == 8


def test_error_simulation_by_sobol_sample(
    sensitivity_analyzer
):

    # set up TxtInOut folder path
    txtinout_folder = os.path.join(os.path.dirname(__file__), 'TxtInOut')
    # Sensitivity parameters
    parameters = [
        {
            'name': 'perco',
            'lower_bound': 0,
            'upper_bound': 1,
            'change_type': 'absval'
        }
    ]

    # Sensitivity simulation_data dictionary to extract data
    simulation_data = {
        'channel_sd_yr.txt': {
            'has_units': True,
            'apply_filter': {'name': ['cha561'], 'yr': [2012]},
            'usecols': ['gis_id', 'flo_out']
        }
    }

    # Error: non-empty simulation folder path
    with tempfile.TemporaryDirectory() as tmp_dir:
        shutil.copy2(
            src=os.path.join(txtinout_folder, 'topography.hyd'),
            dst=os.path.join(tmp_dir, 'topography.hyd')
        )
        with pytest.raises(Exception) as exc_info:
            sensitivity_analyzer.simulation_by_sobol_sample(
                parameters=parameters,
                sample_number=1,
                simulation_folder=tmp_dir,
                txtinout_folder=txtinout_folder,
                simulation_data=simulation_data
            )
        assert exc_info.value.args[0] == 'Provided simulation_folder must be an empty directory'

    with tempfile.TemporaryDirectory() as tmp_dir:
        # Error: invalid simulation_data type
        with pytest.raises(Exception) as exc_info:
            sensitivity_analyzer.simulation_by_sobol_sample(
                parameters=parameters,
                sample_number=1,
                simulation_folder=tmp_dir,
                txtinout_folder=txtinout_folder,
                simulation_data=[]
            )
        assert exc_info.value.args[0] == 'Expected "simulation_data" to be "dict", but got type "list"'
        # Error: invalid data type of value for key in simulation_data
        with pytest.raises(Exception) as exc_info:
            sensitivity_analyzer.simulation_by_sobol_sample(
                parameters=parameters,
                sample_number=1,
                simulation_folder=tmp_dir,
                txtinout_folder=txtinout_folder,
                simulation_data={
                    'channel_sd_yr.txt': []
                }
            )
        assert exc_info.value.args[0] == 'Expected "channel_sd_yr.txt" in simulation_date must be a dictionary, but got type "list"'
        # Error: missing has_units subkey for key in simulation_data
        with pytest.raises(Exception) as exc_info:
            sensitivity_analyzer.simulation_by_sobol_sample(
                parameters=parameters,
                sample_number=1,
                simulation_folder=tmp_dir,
                txtinout_folder=txtinout_folder,
                simulation_data={
                    'channel_sd_yr.txt': {}
                }
            )
        assert exc_info.value.args[0] == 'Key has_units is missing for "channel_sd_yr.txt" in simulation_data'
        # Error: invalid sub_key for key in simulation_data
        valid_subkeys = [
            'has_units',
            'begin_date',
            'end_date',
            'ref_day',
            'ref_month',
            'apply_filter',
            'usecols'
        ]
        with pytest.raises(Exception) as exc_info:
            sensitivity_analyzer.simulation_by_sobol_sample(
                parameters=parameters,
                sample_number=1,
                simulation_folder=tmp_dir,
                txtinout_folder=txtinout_folder,
                simulation_data={
                    'channel_sd_yr.txt': {
                        'has_units': True,
                        'begin_datee': None
                    }
                }
            )
        assert exc_info.value.args[0] == f'Invalid key "begin_datee" for "channel_sd_yr.txt" in simulation_data; expected subkeys are {valid_subkeys}'
