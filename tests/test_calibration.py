import os
import pySWATPlus
import pytest
import tempfile


def test_calibration():

    # set up TxtInOut directory path
    txtinout_dir = os.path.join(os.path.dirname(__file__), 'TxtInOut')

    # initialize TxtinoutReader class
    txtinout_reader = pySWATPlus.TxtinoutReader(
        tio_dir=txtinout_dir
    )

    # Calibration parameters
    parameters = [
        {
            'name': 'perco',
            'change_type': 'absval',
            'lower_bound': 0,
            'upper_bound': 1
        }
    ]
    # Extract data configuration
    extract_data = {
        'channel_sd_mon.txt': {
            'has_units': True,
            'ref_day': 1,
            'apply_filter': {'name': ['cha771']}
        }
    }

    # Observe data configuration
    observe_data = {
        'channel_sd_mon.txt': {
            'obs_file': os.path.join(txtinout_dir, 'a_observe_discharge_monthly.csv'),
            'date_format': '%Y-%m-%d'
        }
    }

    # Objective configuration
    objective_config = {
        'channel_sd_mon.txt': {
            'sim_col': 'flo_out',
            'obs_col': 'mean',
            'indicator': 'RMSE'
        }
    }

    with tempfile.TemporaryDirectory() as tmp1_dir:
        # Copy required files to a simulation directory
        sim_dir = txtinout_reader.copy_required_files(
            sim_dir=tmp1_dir
        )
        # Intialize TxtinOutReader class by simulation direcotry
        sim_reader = pySWATPlus.TxtinoutReader(
            tio_dir=sim_dir
        )
        # Disable all objects for daily time series file in print.prt to save time and space
        sim_reader.enable_object_in_print_prt(
            obj=None,
            daily=False,
            monthly=True,
            yearly=True,
            avann=True
        )
        # Set begin and end year
        sim_reader.set_simulation_period(
            begin_date='01-Jan-2010',
            end_date='31-Dec-2013'
        )
        # Set warmup year
        sim_reader.set_warmup_year(
            warmup=1
        )

        # Pass: calibration of model parameters
        with tempfile.TemporaryDirectory() as tmp2_dir:
            calibration = pySWATPlus.Calibration(
                parameters=parameters,
                calsim_dir=tmp2_dir,
                txtinout_dir=tmp1_dir,
                extract_data=extract_data,
                observe_data=observe_data,
                objective_config=objective_config,
                algorithm='NSGA2',
                n_gen=2,
                pop_size=3
            )

            output = calibration.parameter_optimization()

            assert isinstance(output, dict)
            assert len(output) == 7
            assert 'variables' in output
            assert 'objectives' in output
            assert os.path.exists(os.path.join(tmp2_dir, 'optimization_history.json'))
            assert os.path.exists(os.path.join(tmp2_dir, 'optimization_result.json'))

        # Pass: compute sensitivity indices directly
        with tempfile.TemporaryDirectory() as tmp3_dir:
            output = pySWATPlus.SensitivityAnalyzer().simulation_and_indices(
                parameters=parameters,
                sample_number=1,
                sensim_dir=tmp3_dir,
                txtinout_dir=tmp1_dir,
                extract_data=extract_data,
                observe_data=observe_data,
                metric_config=objective_config
            )

            assert isinstance(output, dict)
            assert len(output) == 1
            assert os.path.exists(os.path.join(tmp3_dir, 'sensitivity_indices.json'))
            assert os.path.exists(os.path.join(tmp3_dir, 'time.json'))


def test_error_calibration():

    # set up TxtInOut directory path
    txtinout_dir = os.path.join(os.path.dirname(__file__), 'TxtInOut')

    # initialize TxtinoutReader class
    txtinout_reader = pySWATPlus.TxtinoutReader(
        tio_dir=txtinout_dir
    )

    # Calibration parameters
    parameters = [
        {
            'name': 'perco',
            'change_type': 'absval',
            'lower_bound': 0,
            'upper_bound': 1
        }
    ]
    # Extract data configuration
    extract_data = {
        'channel_sd_mon.txt': {
            'has_units': True,
            'ref_day': 1,
            'apply_filter': {'name': ['cha771']}
        }
    }

    # Observe data configuration
    observe_data = {
        'channel_sd_mon.txt': {
            'obs_file': os.path.join(txtinout_dir, 'a_observe_discharge_monthly.csv'),
            'date_format': '%Y-%m-%d'
        }
    }

    # Objective configuration
    objective_config = {
        'channel_sd_mon.txt': {
            'sim_col': 'flo_out',
            'obs_col': 'mean',
            'indicator': 'RMSE'
        }
    }

    with tempfile.TemporaryDirectory() as tmp1_dir:
        # Copy required files to a simulation directory
        txtinout_reader.copy_required_files(
            sim_dir=tmp1_dir
        )

        with tempfile.TemporaryDirectory() as tmp2_dir:

            # Error: mismatch of top-level key names
            with pytest.raises(Exception) as exc_info:
                pySWATPlus.Calibration(
                    parameters=parameters,
                    calsim_dir=tmp2_dir,
                    txtinout_dir=tmp1_dir,
                    extract_data=extract_data,
                    observe_data=observe_data,
                    objective_config={
                        'channel_sd_monn.txt': {
                            'sim_col': 'flo_out',
                            'obs_col': 'mean',
                            'indicator': 'RMSE'
                        }
                    },
                    algorithm='NSGA2',
                    n_gen=2,
                    pop_size=5
                )
            assert 'Top-level keys mismatch' in exc_info.value.args[0]

            # Error: PBIAS is not allowed as an indicator name
            with pytest.raises(Exception) as exc_info:
                pySWATPlus.Calibration(
                    parameters=parameters,
                    calsim_dir=tmp2_dir,
                    txtinout_dir=tmp1_dir,
                    extract_data=extract_data,
                    observe_data=observe_data,
                    objective_config={
                        'channel_sd_mon.txt': {
                            'sim_col': 'flo_out',
                            'obs_col': 'mean',
                            'indicator': 'PBIAS'
                        }
                    },
                    algorithm='NSGA2',
                    n_gen=2,
                    pop_size=5
                )
            assert exc_info.value.args[0] == 'Indicator "PBIAS" is invalid in objective_config; it lacks a defined optimization direction'

            # Error: invalid value type of top-key in observe_data
            with pytest.raises(Exception) as exc_info:
                pySWATPlus.Calibration(
                    parameters=parameters,
                    calsim_dir=tmp2_dir,
                    txtinout_dir=tmp1_dir,
                    extract_data=extract_data,
                    observe_data={
                        'channel_sd_mon.txt': []
                    },
                    objective_config=objective_config,
                    algorithm='NSGA2',
                    n_gen=2,
                    pop_size=5
                )
            assert 'Expected "channel_sd_mon.txt" in observe_data must be a dictionary' in exc_info.value.args[0]

            # Error: invalid length of sub-dictionary in observe_data
            with pytest.raises(Exception) as exc_info:
                pySWATPlus.Calibration(
                    parameters=parameters,
                    calsim_dir=tmp2_dir,
                    txtinout_dir=tmp1_dir,
                    extract_data=extract_data,
                    observe_data={
                        'channel_sd_mon.txt': {
                            'date_format': '%Y-%m-%d'
                        }
                    },
                    objective_config=objective_config,
                    algorithm='NSGA2',
                    n_gen=2,
                    pop_size=5
                )
            assert 'Length of "channel_sd_mon.txt" sub-dictionary in observe_data must be 2' in exc_info.value.args[0]

            # Error: invalid sub-key in observe_data
            with pytest.raises(Exception) as exc_info:
                pySWATPlus.Calibration(
                    parameters=parameters,
                    calsim_dir=tmp2_dir,
                    txtinout_dir=tmp1_dir,
                    extract_data=extract_data,
                    observe_data={
                        'channel_sd_mon.txt': {
                            'obs_file': os.path.join(txtinout_dir, 'a_observe_discharge_monthly.csv'),
                            'date_formatt': '%Y-%m-%d'
                        }
                    },
                    objective_config=objective_config,
                    algorithm='NSGA2',
                    n_gen=2,
                    pop_size=5
                )
            assert 'Invalid sub-key "date_formatt" for "channel_sd_mon.txt" in observe_data' in exc_info.value.args[0]

            # Error: invalid value type of top-key in objectives
            with pytest.raises(Exception) as exc_info:
                pySWATPlus.Calibration(
                    parameters=parameters,
                    calsim_dir=tmp2_dir,
                    txtinout_dir=tmp1_dir,
                    extract_data=extract_data,
                    observe_data=observe_data,
                    objective_config={
                        'channel_sd_mon.txt': []
                    },
                    algorithm='NSGA2',
                    n_gen=2,
                    pop_size=5
                )
            assert 'Expected "channel_sd_mon.txt" in objective_config must be a dictionary' in exc_info.value.args[0]

            # Error: invalid length of sub-dictionary in objectives
            with pytest.raises(Exception) as exc_info:
                pySWATPlus.Calibration(
                    parameters=parameters,
                    calsim_dir=tmp2_dir,
                    txtinout_dir=tmp1_dir,
                    extract_data=extract_data,
                    observe_data=observe_data,
                    objective_config={
                        'channel_sd_mon.txt': {
                            'sim_col': 'flo_out',
                            'obs_col': 'mean'
                        }
                    },
                    algorithm='NSGA2',
                    n_gen=2,
                    pop_size=5
                )
            assert 'Length of "channel_sd_mon.txt" sub-dictionary in objective_config must be 3' in exc_info.value.args[0]

            # Error: invalid sub-key in objectives
            with pytest.raises(Exception) as exc_info:
                pySWATPlus.Calibration(
                    parameters=parameters,
                    calsim_dir=tmp2_dir,
                    txtinout_dir=tmp1_dir,
                    extract_data=extract_data,
                    observe_data=observe_data,
                    objective_config={
                        'channel_sd_mon.txt': {
                            'sim_col': 'flo_out',
                            'obs_col': 'mean',
                            'indicatorr': 'RMSE'
                        }
                    },
                    algorithm='NSGA2',
                    n_gen=2,
                    pop_size=5
                )
            assert 'Invalid sub-key "indicatorr" for "channel_sd_mon.txt" in objective_config' in exc_info.value.args[0]

            # Error: invalid indicator in objectives
            with pytest.raises(Exception) as exc_info:
                pySWATPlus.Calibration(
                    parameters=parameters,
                    calsim_dir=tmp2_dir,
                    txtinout_dir=tmp1_dir,
                    extract_data=extract_data,
                    observe_data=observe_data,
                    objective_config={
                        'channel_sd_mon.txt': {
                            'sim_col': 'flo_out',
                            'obs_col': 'mean',
                            'indicator': 'RMSEE'
                        }
                    },
                    algorithm='NSGA2',
                    n_gen=2,
                    pop_size=5
                )
            assert 'Invalid "indicator" value "RMSEE" for "channel_sd_mon.txt" in objective_config' in exc_info.value.args[0]

            # Error: invalid algorithm name
            with pytest.raises(Exception) as exc_info:
                pySWATPlus.Calibration(
                    parameters=parameters,
                    calsim_dir=tmp2_dir,
                    txtinout_dir=tmp1_dir,
                    extract_data=extract_data,
                    observe_data=observe_data,
                    objective_config=objective_config,
                    algorithm='NSGA',
                    n_gen=2,
                    pop_size=5
                ).parameter_optimization()
            assert 'Invalid algorithm "NSGA"' in exc_info.value.args[0]

            # Error: invalid algorithm for multiple objectives
            with pytest.raises(Exception) as exc_info:
                pySWATPlus.Calibration(
                    parameters=parameters,
                    calsim_dir=tmp2_dir,
                    txtinout_dir=tmp1_dir,
                    extract_data={
                        'channel_sd_day.txt': {
                            'has_units': True,
                            'apply_filter': {'name': ['cha771']}
                        },
                        'channel_sd_mon.txt': {
                            'has_units': True,
                            'ref_day': 1,
                            'apply_filter': {'name': ['cha771']}
                        }
                    },
                    observe_data={
                        'channel_sd_day.txt': {
                            'obs_file': os.path.join(txtinout_dir, 'a_observe_discharge_monthly.csv'),
                            'date_format': '%Y-%m-%d'
                        },
                        'channel_sd_mon.txt': {
                            'obs_file': os.path.join(txtinout_dir, 'a_observe_discharge_monthly.csv'),
                            'date_format': '%Y-%m-%d'
                        }
                    },
                    objective_config={
                        'channel_sd_day.txt': {
                            'sim_col': 'flo_out',
                            'obs_col': 'mean',
                            'indicator': 'NSE'
                        },
                        'channel_sd_mon.txt': {
                            'sim_col': 'flo_out',
                            'obs_col': 'mean',
                            'indicator': 'RMSE'
                        }
                    },
                    algorithm='DE',
                    n_gen=2,
                    pop_size=5
                ).parameter_optimization()
            assert 'Algorithm "DE" cannot handle multiple objectives' in exc_info.value.args[0]
