import os
import pySWATPlus
import pytest
import tempfile


@pytest.fixture(scope='class')
def sensitivity_analyzer():

    # initialize SensitivityAnalyzer class
    output = pySWATPlus.SensitivityAnalyzer()

    yield output


@pytest.fixture(scope='class')
def performance_metrics():

    # initialize PerformanceMetrics class
    output = pySWATPlus.PerformanceMetrics()

    yield output


def test_simulation_by_sobol_sample(
    sensitivity_analyzer,
    performance_metrics
):

    # set up TxtInOut folder path
    txtinout_folder = os.path.join(os.path.dirname(__file__), 'TxtInOut')

    # initialize TxtinoutReader class
    txtinout_reader = pySWATPlus.TxtinoutReader(
        path=txtinout_folder
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
        'channel_sd_mon.txt': {
            'has_units': True,
            'ref_day': 1,
            'apply_filter': {'name': ['cha561']},
            'usecols': ['gis_id', 'flo_out']
        }
    }

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
        target_reader.set_simulation_period(
            begin_date='01-Jan-2010',
            end_date='31-Dec-2012'
        )
        # Set warmup year
        target_reader.set_warmup_year(
            warmup=1
        )

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

            # Pass: read sensitive DataFrame of scenarios
            output = pySWATPlus.DataManager().read_sensitive_dfs(
                sim_file=os.path.join(tmp2_dir, 'sensitivity_simulation.json'),
                df_name='channel_sd_mon_df',
                add_problem=True,
                add_sample=True
            )
            assert isinstance(output, dict)
            assert len(output) == 3
            assert len(output['scenario']) == 8
            assert len(output['sample']) == 8

            # Indicator list
            indicators = list(performance_metrics.indicator_names.keys())

            # Pass: indicator values
            output = performance_metrics.scenario_indicators(
                sim_file=os.path.join(tmp2_dir, 'sensitivity_simulation.json'),
                df_name='channel_sd_mon_df',
                sim_col='flo_out',
                obs_file=os.path.join(txtinout_folder, 'a_observe_discharge_monthly.csv'),
                date_format='%Y-%m-%d',
                obs_col='mean',
                indicators=indicators,
                json_file=os.path.join(tmp2_dir, 'indicators.json')
            )
            assert isinstance(output, dict)
            assert len(output) == 2
            assert len(output['indicator']) == 8

            # Pass: Sobol sensitivity indices
            output = sensitivity_analyzer.sobol_indices(
                sim_file=os.path.join(tmp2_dir, 'sensitivity_simulation.json'),
                df_name='channel_sd_mon_df',
                sim_col='flo_out',
                obs_file=os.path.join(txtinout_folder, 'a_observe_discharge_monthly.csv'),
                date_format='%Y-%m-%d',
                obs_col='mean',
                indicators=indicators,
                json_file=os.path.join(tmp2_dir, 'sobol_indices.json')
            )
            assert isinstance(output, dict)
            assert len(output) == 2
            sobol_indices = output['sobol_indices']
            assert isinstance(sobol_indices, dict)
            assert len(sobol_indices) == 6
            assert all([isinstance(sobol_indices[i]['S1'][0], float) for i in indicators])

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
            assert 'Invalid key "begin_datee" for "channel_sd_yr.txt" in simulation_data' in exc_info.value.args[0]


def test_error_scenario_indicators(
    performance_metrics
):

    # Error: invalid indicator name
    with pytest.raises(Exception) as exc_info:
        performance_metrics.scenario_indicators(
            sim_file='sensitivity_simulation.json',
            df_name='channel_sd_mon_df',
            sim_col='flo_out',
            obs_file='a_observe_discharge_monthly.csv',
            date_format='%Y-%m-%d',
            obs_col='mean',
            indicators=['NSEE']
        )
    assert 'Invalid name "NSEE" in "indicatiors" list' in exc_info.value.args[0]


def test_create_sobol_problem(
    sensitivity_analyzer
):

    parameters = [
        {
            'name': 'perco',
            'change_type': 'absval',
            'lower_bound': 0,
            'upper_bound': 1
        },
        {
            'name': 'perco',
            'change_type': 'absval',
            'lower_bound': 0,
            'upper_bound': 1,
            'units': [1, 2, 3]
        }
    ]

    params_bounds = [
        pySWATPlus.types.BoundDict(**param) for param in parameters
    ]

    output = sensitivity_analyzer._create_sobol_problem(
        params_bounds=params_bounds
    )

    assert output['names'][0] == 'perco|1'
    assert output['names'][1] == 'perco|2'
