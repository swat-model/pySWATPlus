import os
import pandas
import pySWATPlus
import pytest
import tempfile
from pySWATPlus.types import ParameterModel
from datetime import date


@pytest.fixture(scope='class')
def txtinout_reader():

    # set up TxtInOut folder path
    txtinout_folder = os.path.join(os.path.dirname(__file__), 'TxtInOut')

    # initialize TxtinoutReader class
    txtinout_reader = pySWATPlus.TxtinoutReader(
        path=txtinout_folder
    )

    yield txtinout_reader


def test_reader_error(
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
        # pass test for enable CSV print
        target_reader.enable_csv_print()
        printprt_file = os.path.join(str(target_reader.root_folder), 'print.prt')
        with open(printprt_file, 'r') as read_output:
            target_line = read_output.readlines()[6]
        assert target_line[0] == 'y'
        # pass test to update all objects in print.prt
        target_reader.enable_object_in_print_prt(
            obj=None,
            daily=False,
            monthly=False,
            yearly=True,
            avann=True
        )
        with open(printprt_file, 'r') as f:
            lines = f.readlines()[10:]  # skip first 10 unchanged lines
        for line in lines:
            if line.strip():
                assert line.split()[1] == 'n'
                assert line.split()[2] == 'n'
                assert line.split()[3] == 'y'
                assert line.split()[4] == 'y'
        with tempfile.TemporaryDirectory() as tmp2_dir:
            # pass test for run SWAT+ in other directory
            target_dir = target_reader.run_swat(
                target_dir=tmp2_dir,
                begin_and_end_date={
                    "begin_date": date(2010, 1, 1), "end_date": date(2012, 1, 1)
                },
                warmup=1,
                print_prt_control={'channel_sd': {'daily': False}}
            )
            assert os.path.samefile(target_dir, tmp2_dir)
            # pass test to ensure data types are parsed correctly (for example jday must be int)
            file_reader = pySWATPlus.FileReader(
                path=os.path.join(str(target_dir), 'channel_sd_yr.txt'),
                has_units=True
            )
            df = file_reader.df
            assert pandas.api.types.is_integer_dtype(df['jday'])
            # pass test to read CSV file
            csv_file_reader = pySWATPlus.FileReader(
                path=os.path.join(str(target_dir), 'channel_sd_yr.csv'),
                has_units=True
            )
            csv_df = csv_file_reader.df
            # pass test TXT and CSV file DataFrames
            assert df.shape == csv_df.shape
            assert list(df.columns) == list(csv_df.columns)
            assert all(df.dtypes == csv_df.dtypes)
            assert file_reader.units_row.equals(csv_file_reader.units_row)
            # error for overwriting output file
            with pytest.raises(Exception) as exc_info:
                file_reader = pySWATPlus.FileReader(
                    path=os.path.join(str(target_dir), 'channel_sd_yr.txt'),
                    has_units=True
                )
                file_reader.overwrite_file()
            assert exc_info.value.args[0] == 'Overwriting SWAT+ Output Files is not allowed'
            # Initialize TxtInoutReader class
            target_reader = pySWATPlus.TxtinoutReader(
                path=target_dir
            )
            # pass test for adding invalid object with flag
            target_reader.enable_object_in_print_prt(
                obj='my_custom_obj',
                daily=True,
                monthly=False,
                yearly=False,
                avann=True,
                allow_unavailable_object=True
            )
            printprt_file = os.path.join(str(target_reader.root_folder), 'print.prt')
            with open(printprt_file, 'r') as f:
                lines = f.readlines()
            assert any(line.startswith('my_custom_obj') for line in lines)
            assert ' y' in lines[-1]
            # pass test for disable CSV print
            target_reader.disable_csv_print()
            with open(printprt_file, 'r') as read_output:
                target_line = read_output.readlines()[6]
            assert target_line[0] == 'n'


def test_error_enable_object_in_print_prt(
    txtinout_reader
):

    # error test for 'obj' type
    with pytest.raises(Exception) as exc_info:
        txtinout_reader.enable_object_in_print_prt(
            obj=1,
            daily=True,
            monthly=True,
            yearly=True,
            avann=False
        )
    assert exc_info.value.args[0] == 'Input "obj" to be string type or None, got int'

    # error test for invalid bool value
    with pytest.raises(Exception) as exc_info:
        txtinout_reader.enable_object_in_print_prt(
            obj='basin_wb',
            daily=5,
            monthly=True,
            yearly=True,
            avann=False
        )
    assert exc_info.value.args[0] == 'Variable "daily" for "basin_wb" must be a bool value'

    # error test for adding invalid object without flag
    with pytest.raises(Exception) as exc_info:
        txtinout_reader.enable_object_in_print_prt(
            obj='invalid_obj',
            daily=True,
            monthly=True,
            yearly=True,
            avann=False,
            allow_unavailable_object=False
        )
    assert exc_info.value.args[0] == 'Object "invalid_obj" not found in print.prt file. Use allow_unavailable_object=True to proceed.'


def test_error_txtinoutreader_class():

    # error test for .exe file
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.TxtinoutReader(
            path=1
        )
    assert "Argument must be a string or Path object" in exc_info.value.args[0]

    # error test for .exe file
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.TxtinoutReader(
            path='nonexist_folder'
        )
    assert exc_info.value.args[0] == 'Folder does not exist'

    # error test for .exe file
    with tempfile.TemporaryDirectory() as tmp_dir:
        with pytest.raises(Exception) as exc_info:
            pySWATPlus.TxtinoutReader(
                path=tmp_dir
            )
        assert exc_info.value.args[0] == 'Expected exactly one .exe file in the parent folder, but found none or multiple.'


def test_run_swat_dir_in_same_dir(
    txtinout_reader
):
    with pytest.raises(Exception) as exc_info:
        txtinout_reader.run_swat(
            target_dir=txtinout_reader.root_folder
        )

    assert "`target_dir` parameter must be different from the existing TxtInOut path!" == exc_info.value.args[0]


def test_error_set_begin_and_end_date(txtinout_reader):
    # --- error: begin_date is not a date object ---
    with pytest.raises(TypeError) as exc_info:
        txtinout_reader.set_begin_and_end_date(
            begin_date="2012-01-01",  # string instead of date
            end_date=date(2016, 1, 1)
        )
    assert exc_info.value.args[0] == "begin_date and end_date must be datetime.date objects"

    # --- error: end_date is not a date object ---
    with pytest.raises(TypeError) as exc_info:
        txtinout_reader.set_begin_and_end_date(
            begin_date=date(2012, 1, 1),
            end_date="2016-01-01"  # string instead of date
        )
    assert exc_info.value.args[0] == "begin_date and end_date must be datetime.date objects"

    # --- error: begin_date >= end_date ---
    with pytest.raises(ValueError) as exc_info:
        txtinout_reader.set_begin_and_end_date(
            begin_date=date(2016, 1, 1),
            end_date=date(2012, 1, 1)
        )
    assert exc_info.value.args[0] == "begin_date must be earlier than end_date"

    # --- error: step is not an integer ---
    with pytest.raises(TypeError) as exc_info:
        txtinout_reader.set_begin_and_end_date(
            begin_date=date(2012, 1, 1),
            end_date=date(2016, 1, 1),
            step="daily"  # string instead of int
        )
    assert exc_info.value.args[0] == "step must be an integer"

    # --- error: step is invalid ---
    with pytest.raises(ValueError) as exc_info:
        txtinout_reader.set_begin_and_end_date(
            begin_date=date(2012, 1, 1),
            end_date=date(2016, 1, 1),
            step=7  # not in {0,1,24,96,1440}
        )
    assert exc_info.value.args[0] == "Invalid step: 7. Must be one of [0, 1, 24, 96, 1440]"


def test_set_begin_and_end_date_updates_time_sim(txtinout_reader):
    """
    Test that set_begin_and_end_date correctly updates line 3 in time.sim
    with proper year and Julian day values, formatted correctly.
    """

    with tempfile.TemporaryDirectory() as tmp_dir:

        target_dir = txtinout_reader.copy_required_files(tmp_dir)
        target_reader = pySWATPlus.TxtinoutReader(target_dir)

        # Call the function
        begin_date = date(2010, 3, 15)  # March 15, 2010
        end_date = date(2012, 10, 20)   # Oct 20, 2012
        step = 0

        target_reader.set_begin_and_end_date(
            begin_date=begin_date,
            end_date=end_date,
            step=step
        )

        # Calculate expected values
        begin_day = begin_date.timetuple().tm_yday
        begin_year = begin_date.year
        end_day = end_date.timetuple().tm_yday
        end_year = end_date.year

        expected_elements = [str(begin_day), str(begin_year), str(end_day), str(end_year), str(step)]
        expected_line = '{: >8} {: >10} {: >10} {: >10} {: >10} \n'.format(*expected_elements)

        # Read the file again
        with open(target_dir / 'time.sim', 'r') as f:
            lines = f.readlines()

        # Check line 3
        assert lines[2] == expected_line, f"Expected:\n{expected_line}\nGot:\n{lines[2]}"


def test_error_run_swat(
    txtinout_reader
):

    # error test for invalid folder path
    with pytest.raises(Exception) as exc_info:
        txtinout_reader.run_swat(
            target_dir=1
        )
    assert "Argument must be a string or Path object" in exc_info.value.args[0]

    # error test for invalid begin and end year values type
    with tempfile.TemporaryDirectory() as tmp_dir:

        with pytest.raises(Exception) as exc_info:
            txtinout_reader.run_swat(
                target_dir=tmp_dir,
                begin_and_end_date=[]
            )
        assert exc_info.value.args[0] == "begin_and_end_date must be a dictionary"

    # error test for invalid begin and end years tuple length
    with tempfile.TemporaryDirectory() as tmp_dir:
        with pytest.raises(Exception) as exc_info:
            txtinout_reader.run_swat(
                target_dir=tmp_dir,
                begin_and_end_date={"begin_date": date(2010, 1, 1)}  # missing end_date
            )

        assert "missing 1 required positional argument" in exc_info.value.args[0]
    # error test for invalid print_prt_control type
    with tempfile.TemporaryDirectory() as tmp_dir:
        with pytest.raises(Exception) as exc_info:
            txtinout_reader.run_swat(
                target_dir=tmp_dir,
                print_prt_control=[]
            )
        assert exc_info.value.args[0] == 'print_prt_control must be a dictionary'

    # error test for empty print_prt_control dictionary
    with tempfile.TemporaryDirectory() as tmp_dir:
        with pytest.raises(Exception) as exc_info:
            txtinout_reader.run_swat(
                target_dir=tmp_dir,
                print_prt_control={}
            )
        assert exc_info.value.args[0] == 'print_prt_control cannot be an empty dictionary'

    # error test for invalid sub key value type of print_prt_control
    with tempfile.TemporaryDirectory() as tmp_dir:
        with pytest.raises(Exception) as exc_info:
            txtinout_reader.run_swat(
                target_dir=tmp_dir,
                print_prt_control={'basin_wb': []}
            )
        assert exc_info.value.args[0] == 'Value of key "basin_wb" must be a dictionary'

    # error test for empty dictionary of sub key of print_prt_control
    with tempfile.TemporaryDirectory() as tmp_dir:
        with pytest.raises(Exception) as exc_info:
            txtinout_reader.run_swat(
                target_dir=tmp_dir,
                print_prt_control={'basin_wb': {}}
            )
        assert exc_info.value.args[0] == 'Value of key "basin_wb" cannot be an empty dictionary'

    # error test for invalid time fequency
    with tempfile.TemporaryDirectory() as tmp_dir:
        with pytest.raises(Exception) as exc_info:
            txtinout_reader.run_swat(
                target_dir=tmp_dir,
                print_prt_control={'basin_wb': {'dailyy': False}}
            )
        assert exc_info.value.args[0] == 'Sub-key "dailyy" for key "basin_wb" is not valid'

    """
    # error test for subprocess.CalledProcessError
    with tempfile.TemporaryDirectory() as tmp_dir:
        with pytest.raises(Exception) as exc_info:
            txtinout_reader.run_swat(
                target_dir=tmp_dir,
                parameters={
                    'plants.plt': {
                        'has_units': False,
                        'bm_e': {'value': 200, 'filter_by': 'name == "agrl"'}
                    },
                }
            )
        assert exc_info.value.args[0] == 65
        """


def test_error_print_prt_does_not_exist(
    txtinout_reader
):
    # check that exception is raised if print.prt file does not exist
    with tempfile.TemporaryDirectory() as tmp1_dir:
        target_dir = txtinout_reader.copy_required_files(
            target_dir=tmp1_dir
        )
        target_reader = pySWATPlus.TxtinoutReader(
            path=target_dir
        )

        # delete print.prt file in tmp1_dir
        print_prt_path = target_dir / 'print.prt'
        if print_prt_path.exists():
            print_prt_path.unlink()

        with pytest.raises(Exception) as exc_info:
            target_reader.enable_object_in_print_prt(
                obj='basin_wb',
                daily=False,
                monthly=True,
                yearly=True,
                avann=False
            )
        assert exc_info.value.args[0] == 'print.prt file does not exist'

        with pytest.raises(Exception) as exc_info:
            target_reader.set_warmup_year(3)
        assert exc_info.value.args[0] == 'print.prt file does not exist'

        with pytest.raises(Exception) as exc_info:
            target_reader.enable_csv_print()
        assert exc_info.value.args[0] == 'print.prt file does not exist'

        with pytest.raises(Exception) as exc_info:
            target_reader.disable_csv_print()
        assert exc_info.value.args[0] == 'print.prt file does not exist'


def test_error_time_sim_does_not_exist(
    txtinout_reader
):
    # check that exception is raised if time.sim file does not exist
    with tempfile.TemporaryDirectory() as tmp1_dir:
        target_dir = txtinout_reader.copy_required_files(
            target_dir=tmp1_dir
        )
        target_reader = pySWATPlus.TxtinoutReader(
            path=target_dir
        )

        # delete time.sim file in tmp1_dir
        time_sim_path = target_dir / 'time.sim'
        if time_sim_path.exists():
            time_sim_path.unlink()

        with pytest.raises(Exception) as exc_info:
            target_reader.set_begin_and_end_date(
                begin_date=date(2000, 1, 1),
                end_date=date(2020, 12, 31),
                step=0  # optional, defaults to daily
            )

        assert exc_info.value.args[0] == 'time.sim file does not exist'


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

        par_change = [
            ParameterModel(name="cn2", change_type="pctchg", value=50),
            ParameterModel(name="cn3_swf", change_type="absval", value=0.5),
            ParameterModel(name="ovn", change_type="pctchg", value=50),
            ParameterModel(name="lat_ttime", change_type="absval", value=100),
            ParameterModel(name="latq_co", change_type="absval", value=0.5),
            ParameterModel(name="lat_len", change_type="pctchg", value=50),
            ParameterModel(name="canmx", change_type="absval", value=50),
            ParameterModel(name="esco", change_type="absval", value=0.5),
            ParameterModel(name="epco", change_type="absval", value=0.5),

            ParameterModel(name="perco", change_type="absval", value=0.5, conditions={"hsg": ["A"]}),
            ParameterModel(name="perco", change_type="absval", value=0.5, conditions={"hsg": ["B"]}),
            ParameterModel(name="perco", change_type="absval", value=0.5, conditions={"hsg": ["C"]}),
            ParameterModel(name="perco", change_type="absval", value=0.5, conditions={"hsg": ["D"]}),

            ParameterModel(name="z", change_type="pctchg", value=20),
            ParameterModel(name="bd", change_type="pctchg", value=50),
            ParameterModel(name="awc", change_type="pctchg", value=100),
            ParameterModel(name="k", change_type="pctchg", value=100),

            ParameterModel(name="surlag", change_type="absval", value=10),
            ParameterModel(name="evrch", change_type="absval", value=0.8),
            ParameterModel(name="evlai", change_type="absval", value=5),
            ParameterModel(name="ffcb", change_type="absval", value=0.5),

            ParameterModel(name="chn", change_type="absval", value=0.05),
            ParameterModel(name="chk", change_type="absval", value=100),

            ParameterModel(name="alpha", change_type="absval", value=0.3, units=list(range(1, 143))),
            ParameterModel(name="bf_max", change_type="absval", value=0.3, units=list(range(1, 143))),
            ParameterModel(name="deep_seep", change_type="absval", value=0.1, units=list(range(1, 143))),
            ParameterModel(name="sp_yld", change_type="absval", value=0.2, units=list(range(1, 143))),
            ParameterModel(name="flo_min", change_type="absval", value=10, units=list(range(1, 143))),
            ParameterModel(name="revap_co", change_type="absval", value=0.1, units=list(range(1, 143))),
            ParameterModel(name="revap_min", change_type="absval", value=5, units=list(range(1, 143))),
        ]

        # Run the method
        target_reader._write_calibration_file(par_change)

        # Expected output
        expected_content = (
            "Number of parameters:\n"
            "30\n"
            "NAME        CHG_TYPE             VAL           CONDS    LYR1    LYR2   YEAR1   YEAR2    DAY1    DAY2 OBJ_TOT\n"
            "cn2           pctchg            50.0               0       0       0       0       0       0       0       0\n"
            "cn3_swf       absval             0.5               0       0       0       0       0       0       0       0\n"
            "ovn           pctchg            50.0               0       0       0       0       0       0       0       0\n"
            "lat_ttime     absval           100.0               0       0       0       0       0       0       0       0\n"
            "latq_co       absval             0.5               0       0       0       0       0       0       0       0\n"
            "lat_len       pctchg            50.0               0       0       0       0       0       0       0       0\n"
            "canmx         absval            50.0               0       0       0       0       0       0       0       0\n"
            "esco          absval             0.5               0       0       0       0       0       0       0       0\n"
            "epco          absval             0.5               0       0       0       0       0       0       0       0\n"
            "perco         absval             0.5               1       0       0       0       0       0       0       0\n"
            "hsg                =               0               A\n"
            "perco         absval             0.5               1       0       0       0       0       0       0       0\n"
            "hsg                =               0               B\n"
            "perco         absval             0.5               1       0       0       0       0       0       0       0\n"
            "hsg                =               0               C\n"
            "perco         absval             0.5               1       0       0       0       0       0       0       0\n"
            "hsg                =               0               D\n"
            "z             pctchg            20.0               0       0       0       0       0       0       0       0\n"
            "bd            pctchg            50.0               0       0       0       0       0       0       0       0\n"
            "awc           pctchg           100.0               0       0       0       0       0       0       0       0\n"
            "k             pctchg           100.0               0       0       0       0       0       0       0       0\n"
            "surlag        absval            10.0               0       0       0       0       0       0       0       0\n"
            "evrch         absval             0.8               0       0       0       0       0       0       0       0\n"
            "evlai         absval             5.0               0       0       0       0       0       0       0       0\n"
            "ffcb          absval             0.5               0       0       0       0       0       0       0       0\n"
            "chn           absval            0.05               0       0       0       0       0       0       0       0\n"
            "chk           absval           100.0               0       0       0       0       0       0       0       0\n"
            "alpha         absval             0.3               0       0       0       0       0       0       0       2       1    -142\n"
            "bf_max        absval             0.3               0       0       0       0       0       0       0       2       1    -142\n"
            "deep_seep     absval             0.1               0       0       0       0       0       0       0       2       1    -142\n"
            "sp_yld        absval             0.2               0       0       0       0       0       0       0       2       1    -142\n"
            "flo_min       absval            10.0               0       0       0       0       0       0       0       2       1    -142\n"
            "revap_co      absval             0.1               0       0       0       0       0       0       0       2       1    -142\n"
            "revap_min     absval             5.0               0       0       0       0       0       0       0       2       1    -142\n"
        )

        # Compare file content
        cal_file = target_reader.root_folder / "calibration.cal"
        content = cal_file.read_text()

        assert content == expected_content
