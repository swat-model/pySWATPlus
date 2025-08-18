import os
import shutil
import pySWATPlus
import pytest
import tempfile
import pandas


def test_simulation_by_sobol_sample():

    # set up TxtInOut folder path
    txtinout_folder = os.path.join(os.path.dirname(__file__), 'TxtInOut')
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

    # initialize TxtinoutReader class
    txtinout_reader = pySWATPlus.TxtinoutReader(
        path=txtinout_folder
    )

    txtinout_reader.enable_object_in_print_prt(
        obj=None,
        daily=True,
        monthly=True,
        yearly=True,
        avann=False
    )

    # Parallel simulation and output collection
    with tempfile.TemporaryDirectory() as tmp_dir:
        output = pySWATPlus.Scenario().simulation_by_sobol_sample(
            var_names=var_names,
            var_bounds=var_bounds,
            sample_number=1,
            simulation_folder=tmp_dir,
            txtinout_folder=txtinout_folder,
            params=params,
            data_file='channel_sd_yr.txt',
            start_date='2014-01-01',
            filter_rows={'name': ['cha561']},
            retain_cols=['name', 'flo_out']
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

    # error test for invalid simulation folder path
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.Scenario().simulation_by_sobol_sample(
            var_names=var_names,
            var_bounds=var_bounds,
            sample_number=1,
            simulation_folder='nonexist_folder',
            txtinout_folder=txtinout_folder,
            params=params,
            data_file='channel_sd_yr.txt',
        )
    assert exc_info.value.args[0] == 'Provided simulation_folder is not a valid directory path'

    # error test for non-empty simulation folder path
    with tempfile.TemporaryDirectory() as tmp_dir:
        shutil.copy2(
            src=os.path.join(txtinout_folder, 'topography.hyd'),
            dst=os.path.join(tmp_dir, 'topography.hyd')
        )
        with pytest.raises(Exception) as exc_info:
            pySWATPlus.Scenario().simulation_by_sobol_sample(
                var_names=var_names,
                var_bounds=var_bounds,
                sample_number=1,
                simulation_folder=tmp_dir,
                txtinout_folder=txtinout_folder,
                params=params,
                data_file='channel_sd_yr.txt',
            )
        assert exc_info.value.args[0] == 'Provided simulation_folder must be an empty directory'

    with tempfile.TemporaryDirectory() as tmp_dir:
        # error test for mismatch length between number of varibales and their bounds
        with pytest.raises(Exception) as exc_info:
            pySWATPlus.Scenario().simulation_by_sobol_sample(
                var_names=['esco'],
                var_bounds=[[0, 1], [0, 1]],
                sample_number=1,
                simulation_folder=tmp_dir,
                txtinout_folder=txtinout_folder,
                params=params,
                data_file='channel_sd_yr.txt',
            )
        assert exc_info.value.args[0] == 'Mismatch between number of variables (1) and their bounds (2)'
        # error test for mismatch length between number of varibales and sensitive parameters
        with pytest.raises(Exception) as exc_info:
            pySWATPlus.Scenario().simulation_by_sobol_sample(
                var_names=['esco', 'epco'],
                var_bounds=[[0, 1], [0, 1]],
                sample_number=1,
                simulation_folder=tmp_dir,
                txtinout_folder=txtinout_folder,
                params=params,
                data_file='channel_sd_yr.txt',
            )
        assert exc_info.value.args[0] == 'Mismatch between number of variables (2) and sensitivity parameters (1)'
        # error test for unavailable sensitive parameter in the list of variable names
        with pytest.raises(Exception) as exc_info:
            pySWATPlus.Scenario().simulation_by_sobol_sample(
                var_names=['epco'],
                var_bounds=[[0, 1]],
                sample_number=1,
                simulation_folder=tmp_dir,
                txtinout_folder=txtinout_folder,
                params=params,
                data_file='channel_sd_yr.txt',
            )
        assert exc_info.value.args[0] == 'The var_names list does not contain the parameter "esco" from the params dictionary'
        # error test for invalid sensitive parameter an their file mapping
        with pytest.raises(Exception) as exc_info:
            pySWATPlus.Scenario().simulation_by_sobol_sample(
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
                data_file='channel_sd_yr.txt',
            )
        assert exc_info.value.args[0] == 'Parameter "esco" not found in columns of the file "topography.hyd"'


def test_simulated_timeseries_df():

    # set up TxtInOut folder path
    txtinout_folder = os.path.join(os.path.dirname(__file__), 'TxtInOut')

    # error test for mission time series columns
    missing_cols = ['mon', 'day']
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.Scenario().simulated_timeseries_df(
            data_file=os.path.join(txtinout_folder, 'basin_carbon_all.txt')
        )
    assert exc_info.value.args[0] == f'Missing required time series columns "{missing_cols}" in file "basin_carbon_all.txt"'

    # error test for invalid column name to filter rows
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.Scenario().simulated_timeseries_df(
            data_file=os.path.join(txtinout_folder, 'zrecall_yr.txt'),
            filter_rows={'unavailable': 1}
        )
    assert exc_info.value.args[0] == 'Column name "unavailable" to filter rows is not valid'

    # error test for invalid column value type
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.Scenario().simulated_timeseries_df(
            data_file=os.path.join(txtinout_folder, 'zrecall_yr.txt'),
            filter_rows={'name': 1}
        )
    assert exc_info.value.args[0] == 'Filter values for column "name" must be provided as a list'

    # error test for invalid start_date format
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.Scenario().simulated_timeseries_df(
            data_file=os.path.join(txtinout_folder, 'zrecall_yr.txt'),
            start_date='2025/01/01'  # wrong format
        )
    assert exc_info.value.args[0] == "Invalid date format: '2025/01/01'. Expected 'YYYY-MM-DD'."

    # error test for invalid start_date format
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.Scenario().simulated_timeseries_df(
            data_file=os.path.join(txtinout_folder, 'zrecall_yr.txt'),
            start_date='2025/01/01'  # wrong format
        )
    assert exc_info.value.args[0] == "Invalid date format: '2025/01/01'. Expected 'YYYY-MM-DD'."

    # Use a date range that you know does NOT exist in the data
    bad_start_date = '1900-01-01'
    bad_end_date = '1900-12-31'

    with pytest.raises(ValueError) as exc_info:
        pySWATPlus.Scenario().simulated_timeseries_df(
            data_file=os.path.join(txtinout_folder, 'zrecall_yr.txt'),
            start_date=bad_start_date,
            end_date=bad_end_date
        )

    expected_msg = f'No data available between {pandas.to_datetime(bad_start_date).date()} and {pandas.to_datetime(bad_end_date).date()} in file "zrecall_yr.txt"'
    assert exc_info.value.args[0] == expected_msg


if __name__ == '__main__':
    test_simulation_by_sobol_sample()
