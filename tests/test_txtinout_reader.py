import os
import pySWATPlus
import pytest
import tempfile
import pathlib


@pytest.fixture(scope='class')
def txtinout_reader():

    # set up TxtInOut directory path
    tio_dir = os.path.join(os.path.dirname(__file__), 'TxtInOut')

    # initialize TxtinoutReader class
    output = pySWATPlus.TxtinoutReader(
        tio_dir=tio_dir
    )

    yield output


def test_run_swat(
    txtinout_reader
):

    with tempfile.TemporaryDirectory() as tmp1_dir:

        # Intialize TxtinOutReader class by simulation direcotry
        sim_dir = txtinout_reader.copy_required_files(
            sim_dir=tmp1_dir
        )
        sim_reader = pySWATPlus.TxtinoutReader(
            tio_dir=sim_dir
        )

        # Error: run SWAT+ in same directory
        with pytest.raises(Exception) as exc_info:
            sim_reader.run_swat(
                sim_dir=sim_dir
            )
        assert 'expected an empty directory' in exc_info.value.args[0]

        # Pass: enable CSV print
        sim_reader.enable_csv_print()
        printprt_file = os.path.join(str(sim_reader.root_dir), 'print.prt')
        with open(printprt_file, 'r') as read_output:
            target_line = read_output.readlines()[6]
        assert target_line[0] == 'y'

        # Pass: update all objects in print.prt
        sim_reader.enable_object_in_print_prt(
            obj=None,
            daily=False,
            monthly=False,
            yearly=True,
            avann=True
        )
        with open(printprt_file, 'r') as f:
            # skip first 10 unchanged lines
            lines = f.readlines()[10:]
        for line in lines:
            if line.strip():
                assert line.split()[1] == 'n'
                assert line.split()[2] == 'n'
                assert line.split()[3] == 'y'
                assert line.split()[4] == 'y'

        with tempfile.TemporaryDirectory() as tmp2_dir:

            # Pass: run SWAT+ in other directory
            sim2_dir = sim_reader.run_swat(
                sim_dir=tmp2_dir,
                begin_date='01-Jan-2010',
                end_date='01-Jan-2012',
                simulation_timestep=0,
                warmup=1,
                print_prt_control={
                    'channel_sd': {},
                    'basin_wb': {'daily': False}
                },
                print_begin_date='01-Feb-2011',
                print_end_date='31-Dec-2011',
                print_interval=1
            )
            assert os.path.samefile(sim2_dir, tmp2_dir)

            # Pass: data types are parsed correctly (for example jday must be int)
            df = pySWATPlus.utils._df_extract(
                input_file=sim2_dir / 'channel_sd_yr.txt',
                skiprows=[0, 2],
            )

            # Pass: read CSV file
            csv_df = pySWATPlus.utils._df_extract(
                input_file=sim2_dir / 'channel_sd_yr.csv',
                skiprows=[0, 2],
            )

            # Pass: TXT and CSV file DataFrames. They cannot be compared directly due to rounding differences.
            assert df.shape == csv_df.shape
            assert list(df.columns) == list(csv_df.columns)
            assert all(df.dtypes == csv_df.dtypes)

            # Pass: computing indicator from file
            output = pySWATPlus.PerformanceMetrics().indicator_from_file(
                sim_file=sim2_dir / 'channel_sd_day.txt',
                sim_col='flo_out',
                extract_sim={
                    'has_units': True,
                    'apply_filter': {'name': ['cha771']}
                },
                obs_file=txtinout_reader.root_dir / 'a_observe_discharge_daily.csv',
                date_format='%Y-%m-%d',
                obs_col='discharge',
                indicators=['NSE', 'KGE', 'RMSE']
            )
            assert isinstance(output, dict)
            assert len(output) == 3

            # Pass: monthly and yearly summary statistics from daily time series
            stats_dict = pySWATPlus.DataManager().hru_stats_from_daily_simulation(
                sim_file=sim2_dir / 'channel_sd_day.txt',
                has_units=True,
                gis_id=771,
                sim_col='flo_out',
                output_dir=sim2_dir
            )
            assert isinstance(stats_dict, dict)
            assert len(stats_dict) == 2

            # Error: reading TXT file
            with pytest.raises(Exception) as exc_info:
                pySWATPlus.DataManager().simulated_timeseries_df(
                    sim_file=sim2_dir / 'channel_sd_day',
                    has_units=True
                )
            assert 'Error reading the file' in exc_info.value.args[0]

            # Pass: adding invalid object with flag
            sim2_reader = pySWATPlus.TxtinoutReader(
                tio_dir=sim2_dir
            )
            sim2_reader.enable_object_in_print_prt(
                obj='my_custom_obj',
                daily=True,
                monthly=False,
                yearly=False,
                avann=True,
                allow_unavailable_object=True
            )
            printprt_file = os.path.join(str(sim2_reader.root_dir), 'print.prt')
            with open(printprt_file, 'r') as f:
                lines = f.readlines()
            assert any(line.startswith('my_custom_obj') for line in lines)
            assert ' y' in lines[-1]

            # Pass: disable CSV print
            sim2_reader.disable_csv_print()
            with open(printprt_file, 'r') as read_output:
                target_line = read_output.readlines()[6]
            assert target_line[0] == 'n'


def test_error_txtinoutreader_class():

    # Error: invalid input path type
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.TxtinoutReader(
            tio_dir=1
        )
    valid_type = ['str', 'Path']
    assert exc_info.value.args[0] == f'Expected "tio_dir" to be one of {valid_type}, but got type "int"'

    # Error: invalid TxtInOut directory
    invalid_dir = 'nonexist_folder'
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.TxtinoutReader(
            tio_dir=invalid_dir
        )
    assert exc_info.value.args[0] == f'Invalid directory path: {str(pathlib.Path(invalid_dir).resolve())}'

    # Error: no EXE file
    with tempfile.TemporaryDirectory() as tmp_dir:
        with pytest.raises(Exception) as exc_info:
            pySWATPlus.TxtinoutReader(
                tio_dir=tmp_dir
            )
        assert exc_info.value.args[0] == 'Expected exactly one executable file in the parent folder, but found none or multiple'


def test_error_enable_object_in_print_prt(
    txtinout_reader
):

    # Error: invalid bool type for time frequency
    with pytest.raises(Exception) as exc_info:
        txtinout_reader.enable_object_in_print_prt(
            obj='basin_wb',
            daily=5,
            monthly=True,
            yearly=True,
            avann=False
        )
    assert exc_info.value.args[0] == 'Expected "daily" to be "bool", but got type "int"'

    # Error: adding invalid object without flag
    with pytest.raises(Exception) as exc_info:
        txtinout_reader.enable_object_in_print_prt(
            obj='invalid_obj',
            daily=True,
            monthly=True,
            yearly=True,
            avann=False,
            allow_unavailable_object=False
        )
    assert exc_info.value.args[0] == 'Object "invalid_obj" not found in print.prt file; use "allow_unavailable_object=True" to proceed'


def test_set_simulation_period(
    txtinout_reader
):

    # Pass: modify begin and end date in time.sim
    with tempfile.TemporaryDirectory() as tmp_dir:

        sim_dir = txtinout_reader.copy_required_files(tmp_dir)

        # Read original time.sim
        with open(sim_dir / 'time.sim', 'r') as f:
            original_lines = f.readlines()

        # Replace begin and end date in read line
        parts = original_lines[2].split()
        parts[0] = str(74)
        parts[1] = str(2010)
        parts[2] = str(294)
        parts[3] = str(2012)
        expected_line = '{: >8} {: >10} {: >10} {: >10} {: >10} \n'.format(*parts)

        sim_reader = pySWATPlus.TxtinoutReader(
            tio_dir=sim_dir
        )

        sim_reader.set_simulation_period(
            begin_date='15-Mar-2010',
            end_date='20-Oct-2012'
        )

        # Read the line in time.sim again
        with open(sim_dir / 'time.sim', 'r') as f:
            lines = f.readlines()
        assert lines[2] == expected_line, f'Expected:\n{expected_line}\nGot:\n{lines[2]}'

    # Error: begin date earlier than end date
    with pytest.raises(ValueError) as exc_info:
        txtinout_reader.set_simulation_period(
            begin_date='01-Jan-2016',
            end_date='01-Jan-2012'
        )
    assert exc_info.value.args[0] == 'begin_date 01-Jan-2016 must be earlier than end_date 01-Jan-2012'


def test_set_simulation_timestep(
    txtinout_reader
):

    # Pass: modify step in time.sim
    with tempfile.TemporaryDirectory() as tmp_dir:

        sim_dir = txtinout_reader.copy_required_files(tmp_dir)
        simulation_timestep = 1

        # Read original time.sim
        with open(sim_dir / 'time.sim', 'r') as f:
            original_lines = f.readlines()

        # Replace simulation timestep in read line
        parts = original_lines[2].split()
        parts[4] = str(simulation_timestep)  # new timestep value
        expected_line = '{: >8} {: >10} {: >10} {: >10} {: >10} \n'.format(*parts)

        sim_reader = pySWATPlus.TxtinoutReader(
            tio_dir=sim_dir
        )
        sim_reader.set_simulation_timestep(
            step=simulation_timestep
        )

        # Read the line in time.sim again
        with open(sim_dir / 'time.sim', 'r') as f:
            lines = f.readlines()

        # Now just compare
        assert lines[2] == expected_line, f"Expected:\n{expected_line}\nGot:\n{lines[2]}"

    # Error: step is invalid
    with pytest.raises(ValueError) as exc_info:
        txtinout_reader.set_simulation_timestep(
            step=7
        )
    assert 'Received invalid step: 7' in exc_info.value.args[0]


def test_set_print_period(
    txtinout_reader
):

    # Pass: modify begin date in print.prt
    with tempfile.TemporaryDirectory() as tmp_dir:

        sim_dir = txtinout_reader.copy_required_files(tmp_dir)

        # Read original print.prt
        with open(sim_dir / 'print.prt', 'r') as f:
            original_lines = f.readlines()

        # Replace start date in read line
        parts = original_lines[2].split()
        parts[1] = str(74)
        parts[2] = str(2010)
        parts[3] = str(365)
        parts[4] = str(2021)

        expected_line = f"{parts[0]:<12}{parts[1]:<11}{parts[2]:<11}{parts[3]:<10}{parts[4]:<10}{parts[5]}\n"

        sim_reader = pySWATPlus.TxtinoutReader(
            tio_dir=sim_dir
        )

        sim_reader.set_print_period(
            begin_date='15-Mar-2010',
            end_date='31-Dec-2021'
        )

        # Read the line in print.prt again
        with open(sim_dir / 'print.prt', 'r') as f:
            lines = f.readlines()
        assert lines[2] == expected_line, f'Expected:\n{expected_line}\nGot:\n{lines[2]}'

        # Error: begin date earlier than end date
        with pytest.raises(ValueError) as exc_info:
            sim_reader.set_print_period(
                begin_date='01-Jan-2016',
                end_date='01-Jan-2012'
            )
        assert exc_info.value.args[0] == 'begin_date 01-Jan-2016 must be earlier than end_date 01-Jan-2012'


def test_set_print_interval(
    txtinout_reader
):

    # Pass: modify interval in print.prt
    with tempfile.TemporaryDirectory() as tmp_dir:

        sim_dir = txtinout_reader.copy_required_files(tmp_dir)
        print_interval = 2

        # Read original print.prt
        with open(sim_dir / 'print.prt', 'r') as f:
            original_lines = f.readlines()

        # Replace start date in read line
        parts = original_lines[2].split()
        parts[5] = str(print_interval)
        expected_line = f"{parts[0]:<12}{parts[1]:<11}{parts[2]:<11}{parts[3]:<10}{parts[4]:<10}{parts[5]}\n"

        sim_reader = pySWATPlus.TxtinoutReader(
            tio_dir=sim_dir
        )

        sim_reader.set_print_interval(
            interval=print_interval
        )

        # Read the line in print.prt again
        with open(sim_dir / 'print.prt', 'r') as f:
            lines = f.readlines()
        assert lines[2] == expected_line, f'Expected:\n{expected_line}\nGot:\n{lines[2]}'


def test_error_run_swat(
    txtinout_reader
):

    # Error: begin_date set but no end_date
    with pytest.raises(ValueError) as exc_info:
        txtinout_reader.run_swat(
            begin_date='01-Jan-2010'
        )
    assert "must be provided together" in exc_info.value.args[0]

    # Error: end_date set but no begin_date
    with pytest.raises(ValueError) as exc_info:
        txtinout_reader.run_swat(
            end_date='31-Dec-2013'
        )
    assert "must be provided together" in exc_info.value.args[0]

    # Error: print_begin_date set but no print_end_date
    with pytest.raises(ValueError) as exc_info:
        txtinout_reader.run_swat(
            print_begin_date='01-Jan-2010'
        )
    assert "must be provided together" in exc_info.value.args[0]

    # Error: print_end_date set but no print_begin_date
    with pytest.raises(ValueError) as exc_info:
        txtinout_reader.run_swat(
            print_end_date='31-Dec-2013'
        )
    assert "must be provided together" in exc_info.value.args[0]

    # Error: print_begin_date and print_end_date set without begin_date and end_date
    with pytest.raises(ValueError) as exc_info:
        txtinout_reader.run_swat(
            print_begin_date='01-Jan-2010',
            print_end_date='01-Jan-2011'
        )
    assert 'print_begin_date or print_end_date cannot be set unless begin_date and end_date are also provided' == exc_info.value.args[0]

    # Error: print_begin_date out of range
    with pytest.raises(ValueError) as exc_info:
        txtinout_reader.run_swat(
            begin_date='01-Jan-2010',
            end_date='31-Dec-2010',
            print_begin_date='31-Dec-2011',
            print_end_date='31-Dec-2012'
        )
    assert "must be between" in exc_info.value.args[0]

    # Error: print_end_date out of range
    with pytest.raises(ValueError) as exc_info:
        txtinout_reader.run_swat(
            begin_date='01-Jan-2010',
            end_date='31-Dec-2010',
            print_begin_date='15-Jan-2010',
            print_end_date='31-Dec-2012'
        )
    assert 'must be between' in exc_info.value.args[0]

    # Error: invalid warm-up years
    with pytest.raises(Exception) as exc_info:
        txtinout_reader.run_swat(
            warmup=0
        )
    assert exc_info.value.args[0] == 'Expected warmup >= 1, but received warmup = 0'

    # Error: 'obj' is set as None in print_prt_control
    with pytest.raises(Exception) as exc_info:
        txtinout_reader.run_swat(
            print_prt_control={None: {}}
        )
    assert exc_info.value.args[0] == 'Use enable_object_in_print_prt method instead of None as a key in print_prt_control'

    # Error: invalid sub key value type of print_prt_control
    with pytest.raises(Exception) as exc_info:
        txtinout_reader.run_swat(
            sim_dir=None,
            print_prt_control={'basin_wb': []}
        )
    assert exc_info.value.args[0] == 'Expected a dictionary for key "basin_wb" in print_prt_control, but got type "list"'

    # Error: invalid postional argument in print_prt_control
    with pytest.raises(Exception) as exc_info:
        txtinout_reader.run_swat(
            print_prt_control={'basin_wb': {'dailyy': False}}
        )
    assert 'Invalids sub-key "dailyy" for key "basin_wb" in print_prt_control' in exc_info.value.args[0]

    # Error: duplicate dictionary in list of parameters to be modified
    with pytest.raises(Exception) as exc_info:
        txtinout_reader.run_swat(
            parameters=[
                {
                    'name': 'epco',
                    'change_type': 'absval',
                    'value': 0.5
                },
                {
                    'name': 'epco',
                    'change_type': 'absval',
                    'value': 0.5
                }
            ]
        )
    assert exc_info.value.args[0] == 'Duplicate dictionary found in "parameters" list'


def test_calibration_cal_in_file_cio(
    txtinout_reader
):

    with tempfile.TemporaryDirectory() as tmp1_dir:
        sim_dir = txtinout_reader.copy_required_files(
            sim_dir=tmp1_dir
        )
        sim_reader = pySWATPlus.TxtinoutReader(
            tio_dir=sim_dir
        )

        file_path = sim_reader.root_dir / 'file.cio'

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

        # Pass: adding calibration line
        sim_reader._calibration_cal_in_file_cio(
            add=True
        )
        lines = file_path.read_text().splitlines()
        expected_line = fmt.format(
            'chg', 'cal_parms.cal', 'calibration.cal', *['null'] * 9
        )
        assert lines[21] == expected_line

        # Pass: removing calibration line
        sim_reader._calibration_cal_in_file_cio(
            add=False
        )
        lines = file_path.read_text().splitlines()

        expected_line = fmt.format(
            'chg', 'null', 'calibration.cal', *['null'] * 9
        )
        assert lines[21] == expected_line


def test_write_calibration_file(
    txtinout_reader
):
    with tempfile.TemporaryDirectory() as tmp1_dir:
        # Initialize TxtinOutReader class by target directory
        sim_dir = txtinout_reader.copy_required_files(
            sim_dir=tmp1_dir
        )
        sim_reader = pySWATPlus.TxtinoutReader(
            tio_dir=sim_dir
        )

        par_change = [
            pySWATPlus.newtype.ModifyDict(name='cn2', change_type='pctchg', value=50),
            pySWATPlus.newtype.ModifyDict(name='cn3_swf', change_type='absval', value=0.5),
            pySWATPlus.newtype.ModifyDict(name='ovn', change_type='pctchg', value=50),
            pySWATPlus.newtype.ModifyDict(name='lat_ttime', change_type='absval', value=100),
            pySWATPlus.newtype.ModifyDict(name='latq_co', change_type='absval', value=0.5),
            pySWATPlus.newtype.ModifyDict(name='lat_len', change_type='pctchg', value=50),
            pySWATPlus.newtype.ModifyDict(name='canmx', change_type='absval', value=50),
            pySWATPlus.newtype.ModifyDict(name='esco', change_type='absval', value=0.5),
            pySWATPlus.newtype.ModifyDict(name='epco', change_type='absval', value=0.5),

            pySWATPlus.newtype.ModifyDict(name='perco', change_type='absval', value=0.5, conditions={'hsg': ['A']}),
            pySWATPlus.newtype.ModifyDict(name='perco', change_type='absval', value=0.5, conditions={'hsg': ['B']}),
            pySWATPlus.newtype.ModifyDict(name='perco', change_type='absval', value=0.5, conditions={'hsg': ['C']}),
            pySWATPlus.newtype.ModifyDict(name='perco', change_type='absval', value=0.5, conditions={'hsg': ['D']}),

            pySWATPlus.newtype.ModifyDict(name='z', change_type='pctchg', value=20),
            pySWATPlus.newtype.ModifyDict(name='bd', change_type='pctchg', value=50),
            pySWATPlus.newtype.ModifyDict(name='awc', change_type='pctchg', value=100),
            pySWATPlus.newtype.ModifyDict(name='k', change_type='pctchg', value=100),

            pySWATPlus.newtype.ModifyDict(name='surlag', change_type='absval', value=10),
            pySWATPlus.newtype.ModifyDict(name='evrch', change_type='absval', value=0.8),
            pySWATPlus.newtype.ModifyDict(name='evlai', change_type='absval', value=5),
            pySWATPlus.newtype.ModifyDict(name='ffcb', change_type='absval', value=0.5),

            pySWATPlus.newtype.ModifyDict(name='chn', change_type='absval', value=0.05),
            pySWATPlus.newtype.ModifyDict(name='chk', change_type='absval', value=100),

            pySWATPlus.newtype.ModifyDict(name='alpha', change_type='absval', value=0.3, units=list(range(1, 143))),
            pySWATPlus.newtype.ModifyDict(name='bf_max', change_type='absval', value=0.3, units=list(range(1, 143))),
            pySWATPlus.newtype.ModifyDict(name='deep_seep', change_type='absval', value=0.1, units=list(range(1, 143))),
            pySWATPlus.newtype.ModifyDict(name='sp_yld', change_type='absval', value=0.2, units=list(range(1, 143))),
            pySWATPlus.newtype.ModifyDict(name='flo_min', change_type='absval', value=10, units=list(range(1, 143))),
            pySWATPlus.newtype.ModifyDict(name='revap_co', change_type='absval', value=0.1, units=list(range(1, 143))),
            pySWATPlus.newtype.ModifyDict(name='revap_min', change_type='absval', value=5, units=list(range(1, 143))),
        ]

        # Run the method
        sim_reader._write_calibration_file(par_change)

        # Expected output
        expected_content = (
            'Number of parameters:\n'
            '30\n'
            'NAME        CHG_TYPE             VAL           CONDS    LYR1    LYR2   YEAR1   YEAR2    DAY1    DAY2 OBJ_TOT\n'
            'cn2           pctchg            50.0               0       0       0       0       0       0       0       0\n'
            'cn3_swf       absval             0.5               0       0       0       0       0       0       0       0\n'
            'ovn           pctchg            50.0               0       0       0       0       0       0       0       0\n'
            'lat_ttime     absval           100.0               0       0       0       0       0       0       0       0\n'
            'latq_co       absval             0.5               0       0       0       0       0       0       0       0\n'
            'lat_len       pctchg            50.0               0       0       0       0       0       0       0       0\n'
            'canmx         absval            50.0               0       0       0       0       0       0       0       0\n'
            'esco          absval             0.5               0       0       0       0       0       0       0       0\n'
            'epco          absval             0.5               0       0       0       0       0       0       0       0\n'
            'perco         absval             0.5               1       0       0       0       0       0       0       0\n'
            'hsg                =               0               A\n'
            'perco         absval             0.5               1       0       0       0       0       0       0       0\n'
            'hsg                =               0               B\n'
            'perco         absval             0.5               1       0       0       0       0       0       0       0\n'
            'hsg                =               0               C\n'
            'perco         absval             0.5               1       0       0       0       0       0       0       0\n'
            'hsg                =               0               D\n'
            'z             pctchg            20.0               0       0       0       0       0       0       0       0\n'
            'bd            pctchg            50.0               0       0       0       0       0       0       0       0\n'
            'awc           pctchg           100.0               0       0       0       0       0       0       0       0\n'
            'k             pctchg           100.0               0       0       0       0       0       0       0       0\n'
            'surlag        absval            10.0               0       0       0       0       0       0       0       0\n'
            'evrch         absval             0.8               0       0       0       0       0       0       0       0\n'
            'evlai         absval             5.0               0       0       0       0       0       0       0       0\n'
            'ffcb          absval             0.5               0       0       0       0       0       0       0       0\n'
            'chn           absval            0.05               0       0       0       0       0       0       0       0\n'
            'chk           absval           100.0               0       0       0       0       0       0       0       0\n'
            'alpha         absval             0.3               0       0       0       0       0       0       0       2       1    -142\n'
            'bf_max        absval             0.3               0       0       0       0       0       0       0       2       1    -142\n'
            'deep_seep     absval             0.1               0       0       0       0       0       0       0       2       1    -142\n'
            'sp_yld        absval             0.2               0       0       0       0       0       0       0       2       1    -142\n'
            'flo_min       absval            10.0               0       0       0       0       0       0       0       2       1    -142\n'
            'revap_co      absval             0.1               0       0       0       0       0       0       0       2       1    -142\n'
            'revap_min     absval             5.0               0       0       0       0       0       0       0       2       1    -142\n'
        )

        # Compare file content
        cal_file = sim_reader.root_dir / 'calibration.cal'
        content = cal_file.read_text()

        assert content == expected_content
