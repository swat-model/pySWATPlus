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
            'apply_filter': {'name': ['cha561']}
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
    objectives = {
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
                objectives=objectives,
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
            'apply_filter': {'name': ['cha561']}
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
    objectives = {
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
                    objectives={
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
            assert exc_info.value.args[0] == 'Mismatch of key names. Ensure extract_data, observe_data, and objectives have identical top-level keys.'

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
                    objectives=objectives,
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
                    objectives=objectives,
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
                    objectives=objectives,
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
                    objectives={
                        'channel_sd_mon.txt': []
                    },
                    algorithm='NSGA2',
                    n_gen=2,
                    pop_size=5
                )
            assert 'Expected "channel_sd_mon.txt" in "objectives" must be a dictionary' in exc_info.value.args[0]

            # Error: invalid length of sub-dictionary in objectives
            with pytest.raises(Exception) as exc_info:
                pySWATPlus.Calibration(
                    parameters=parameters,
                    calsim_dir=tmp2_dir,
                    txtinout_dir=tmp1_dir,
                    extract_data=extract_data,
                    observe_data=observe_data,
                    objectives={
                        'channel_sd_mon.txt': {
                            'sim_col': 'flo_out',
                            'obs_col': 'mean'
                        }
                    },
                    algorithm='NSGA2',
                    n_gen=2,
                    pop_size=5
                )
            assert 'Length of "channel_sd_mon.txt" sub-dictionary in "objectives" must be 3' in exc_info.value.args[0]

            # Error: invalid sub-key in objectives
            with pytest.raises(Exception) as exc_info:
                pySWATPlus.Calibration(
                    parameters=parameters,
                    calsim_dir=tmp2_dir,
                    txtinout_dir=tmp1_dir,
                    extract_data=extract_data,
                    observe_data=observe_data,
                    objectives={
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
            assert 'Invalid sub-key "indicatorr" for "channel_sd_mon.txt" in "objectives"' in exc_info.value.args[0]

            # Error: invalid indicator in objectives
            with pytest.raises(Exception) as exc_info:
                pySWATPlus.Calibration(
                    parameters=parameters,
                    calsim_dir=tmp2_dir,
                    txtinout_dir=tmp1_dir,
                    extract_data=extract_data,
                    observe_data=observe_data,
                    objectives={
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
            assert 'Invalid "indicator" value "RMSEE" for "channel_sd_mon.txt" in "objectives"' in exc_info.value.args[0]

            # Error: invalid algorithm name
            with pytest.raises(Exception) as exc_info:
                pySWATPlus.Calibration(
                    parameters=parameters,
                    calsim_dir=tmp2_dir,
                    txtinout_dir=tmp1_dir,
                    extract_data=extract_data,
                    observe_data=observe_data,
                    objectives=objectives,
                    algorithm='NSGA',
                    n_gen=2,
                    pop_size=5
                ).parameter_optimization()
            assert 'Invalid algorithm "NSGA"' in exc_info.value.args[0]
