import os
import shutil
import pySWATPlus
import pytest
import tempfile


@pytest.fixture(scope='class')
def sensitivity_analyzer():

    # initialize SensitivityAnalyzer class
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
        # Update necessary objects in print.prt
        target_reader.enable_object_in_print_prt(
            obj=None,
            daily=False,
            monthly=True,
            yearly=True,
            avann=True
        )
        # Set begin and end year
        target_reader.set_begin_and_end_year(
            begin=2010,
            end=2012
        )
        # Set warmup year
        target_reader.set_warmup_year(
            warmup=1
        )
        # Sensitivity variable names
        var_names = [
            'esco'
        ]
        # Sensitivity variable bounds
        var_bounds = [
            [0, 1]
        ]
        # Sensitivity 'params' dictionary to run SWAT+ model
        params = {
            'hydrology.hyd': {
                'has_units': False,
                'esco': {'value': 0}
            }
        }
        # Sensitivity simulation_data dictionary to extract data
        simulation_data = {
            'channel_sdmorph_mon.txt': {
                'has_units': True,
                'start_date': '2011-06-01',
                'end_date': '2012-06-01',
                'apply_filter': {'gis_id': [561]},
                'usecols': ['gis_id', 'flo_out']
            },
            'channel_sd_yr.txt': {
                'has_units': True,
                'apply_filter': {'name': ['cha561'], 'yr': [2012]},
                'usecols': ['gis_id', 'flo_out']
            }
        }
        with tempfile.TemporaryDirectory() as tmp2_dir:
            output = sensitivity_analyzer.simulation_by_sobol_sample(
                var_names=var_names,
                var_bounds=var_bounds,
                sample_number=1,
                simulation_folder=tmp2_dir,
                txtinout_folder=tmp1_dir,
                params=params,
                simulation_data=simulation_data
            )
            # pass test for simulation by Sobol sample
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
    # Sensitivity 'params' dictionary to run SWAT+ model
    params = {
        'hydrology.hyd': {
            'has_units': False,
            'esco': {'value': 0}
        }
    }
    # Sensitivity simulation_data dictionary to extract data
    simulation_data = {
        'channel_sd_yr.txt': {
            'has_units': True,
            'apply_filter': {'name': ['cha561'], 'yr': [2012]},
            'usecols': ['gis_id', 'flo_out']
        }
    }
    # error test for invalid simulation folder path
    with pytest.raises(Exception) as exc_info:
        sensitivity_analyzer.simulation_by_sobol_sample(
            var_names=['esco'],
            var_bounds=[[0, 1]],
            sample_number=1,
            simulation_folder='nonexist_folder',
            txtinout_folder=txtinout_folder,
            params=params,
            simulation_data=simulation_data
        )
    assert exc_info.value.args[0] == 'Provided simulation_folder is not a valid directory path'

    # error test for non-empty simulation folder path
    with tempfile.TemporaryDirectory() as tmp_dir:
        shutil.copy2(
            src=os.path.join(txtinout_folder, 'topography.hyd'),
            dst=os.path.join(tmp_dir, 'topography.hyd')
        )
        with pytest.raises(Exception) as exc_info:
            sensitivity_analyzer.simulation_by_sobol_sample(
                var_names=['esco'],
                var_bounds=[[0, 1]],
                sample_number=1,
                simulation_folder=tmp_dir,
                txtinout_folder=txtinout_folder,
                params=params,
                simulation_data=simulation_data
            )
        assert exc_info.value.args[0] == 'Provided simulation_folder must be an empty directory'

    with tempfile.TemporaryDirectory() as tmp_dir:
        # error test for invalid simulation data type
        with pytest.raises(Exception) as exc_info:
            sensitivity_analyzer.simulation_by_sobol_sample(
                var_names=['esco'],
                var_bounds=[[0, 1]],
                sample_number=1,
                simulation_folder=tmp_dir,
                txtinout_folder=txtinout_folder,
                params=params,
                simulation_data={
                    'channel_sd_yr.txt': []
                }
            )
        assert exc_info.value.args[0] == 'Value for key "channel_sd_yr.txt" in simulation_data must be a dictinary type, got list'
        # error test for invalid simulation data type
        with pytest.raises(Exception) as exc_info:
            sensitivity_analyzer.simulation_by_sobol_sample(
                var_names=['esco'],
                var_bounds=[[0, 1]],
                sample_number=1,
                simulation_folder=tmp_dir,
                txtinout_folder=txtinout_folder,
                params=params,
                simulation_data={
                    'channel_sd_yr.txt': {}
                }
            )
        assert exc_info.value.args[0] == 'key has_units is missing for "channel_sd_yr.txt" in simulation_data'
        # error test for invalid simulation data type
        sim_validkeys = [
            'start_date',
            'end_date',
            'apply_filter',
            'usecols'
        ]
        with pytest.raises(Exception) as exc_info:
            sensitivity_analyzer.simulation_by_sobol_sample(
                var_names=['esco'],
                var_bounds=[[0, 1]],
                sample_number=1,
                simulation_folder=tmp_dir,
                txtinout_folder=txtinout_folder,
                params=params,
                simulation_data={
                    'channel_sd_yr.txt': {
                        'has_units': True,
                        'start_datee': None
                    }
                }
            )
        assert exc_info.value.args[0] == f'Invalid key "start_datee" for "channel_sd_yr.txt" in simulation_data. Expected one of: {sim_validkeys}'
        # error test for mismatch length between number of varibales and their bounds
        with pytest.raises(Exception) as exc_info:
            sensitivity_analyzer.simulation_by_sobol_sample(
                var_names=['esco'],
                var_bounds=[[0, 1], [0, 1]],
                sample_number=1,
                simulation_folder=tmp_dir,
                txtinout_folder=txtinout_folder,
                params=params,
                simulation_data=simulation_data
            )
        assert exc_info.value.args[0] == 'Mismatch between number of variables (1) and their bounds (2)'
        # error test for mismatch length between number of varibales and sensitive parameters
        with pytest.raises(Exception) as exc_info:
            sensitivity_analyzer.simulation_by_sobol_sample(
                var_names=['esco', 'epco'],
                var_bounds=[[0, 1], [0, 1]],
                sample_number=1,
                simulation_folder=tmp_dir,
                txtinout_folder=txtinout_folder,
                params=params,
                simulation_data=simulation_data
            )
        assert exc_info.value.args[0] == 'Mismatch between number of variables (2) and sensitivity parameters (1)'
        # error test for unavailable sensitive parameter in the list of variable names
        with pytest.raises(Exception) as exc_info:
            sensitivity_analyzer.simulation_by_sobol_sample(
                var_names=['epco'],
                var_bounds=[[0, 1]],
                sample_number=1,
                simulation_folder=tmp_dir,
                txtinout_folder=txtinout_folder,
                params=params,
                simulation_data=simulation_data
            )
        assert exc_info.value.args[0] == 'The var_names list does not contain the parameter "esco" from the params dictionary'
        # error test for invalid sensitive parameter an their file mapping
        with pytest.raises(Exception) as exc_info:
            sensitivity_analyzer.simulation_by_sobol_sample(
                var_names=['esco'],
                var_bounds=[[0, 1]],
                sample_number=1,
                simulation_folder=tmp_dir,
                txtinout_folder=txtinout_folder,
                params={
                    'topography.hyd': {
                        'has_units': False,
                        'esco': {'value': 0}
                    }
                },
                simulation_data=simulation_data
            )
        assert exc_info.value.args[0] == 'Parameter "esco" not found in columns of the file "topography.hyd"'
