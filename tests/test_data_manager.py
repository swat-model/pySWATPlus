import os
import pySWATPlus
import pytest
import tempfile


@pytest.fixture(scope='class')
def data_manager():

    # initialize DataManager class
    output = pySWATPlus.DataManager()

    yield output


def test_simulated_timeseries_df(
    data_manager
):

    # set up TxtInOut directory path
    txtinout_dir = os.path.join(os.path.dirname(__file__), 'TxtInOut')

    # Pass: time series DataFrame and save output
    with tempfile.TemporaryDirectory() as tmp_dir:
        df = data_manager.simulated_timeseries_df(
            sim_file=os.path.join(txtinout_dir, 'zrecall_yr.txt'),
            ref_day=15,
            ref_month=6,
            has_units=True,
            json_file=os.path.join(tmp_dir, 'zrecall_yr.json')
        )
        assert df.shape == (1, 66)

    # Error: missing time series columns
    missing_cols = ['mon', 'day']
    with pytest.raises(Exception) as exc_info:
        data_manager.simulated_timeseries_df(
            sim_file=os.path.join(txtinout_dir, 'basin_carbon_all.txt'),
            has_units=True
        )
    assert exc_info.value.args[0] == f'Missing required time series columns "{missing_cols}" in file "basin_carbon_all.txt"'

    # Error: invalid begin_date format
    with pytest.raises(Exception) as exc_info:
        data_manager.simulated_timeseries_df(
            sim_file=os.path.join(txtinout_dir, 'zrecall_yr.txt'),
            has_units=True,
            begin_date='2025-01-01'
        )
    assert exc_info.value.args[0] == 'Invalid date format: "2025-01-01"; expected format is DD-Mon-YYYY (e.g., 15-Mar-2010)'

    # Error: empty DataFrame extracted by date range
    with pytest.raises(Exception) as exc_info:
        data_manager.simulated_timeseries_df(
            sim_file=os.path.join(txtinout_dir, 'zrecall_yr.txt'),
            has_units=True,
            begin_date='01-Jan-1900',
            end_date='31-Dec-1900'
        )
    assert exc_info.value.args[0] == 'No data found between "01-Jan-1900" and "31-Dec-1900" in file "zrecall_yr.txt"'

    # Error: invalid file for reference day
    with pytest.raises(Exception) as exc_info:
        data_manager.simulated_timeseries_df(
            sim_file=os.path.join(txtinout_dir, 'zrecall_day.txt'),
            has_units=True,
            ref_day=6
        )
    assert 'Parameter "ref_day" is not applicable for daily or sub-daily time series in file "zrecall_day.txt"' in exc_info.value.args[0]

    # Error: invalid file for reference month
    with pytest.raises(Exception) as exc_info:
        data_manager.simulated_timeseries_df(
            sim_file=os.path.join(txtinout_dir, 'zrecall_mon.txt'),
            has_units=True,
            ref_month=6
        )
    assert 'Parameter "ref_month" is not applicable for monthly time series in file "zrecall_mon.txt"' in exc_info.value.args[0]

    # Error: invalid column name to filter rows
    with pytest.raises(Exception) as exc_info:
        data_manager.simulated_timeseries_df(
            sim_file=os.path.join(txtinout_dir, 'zrecall_yr.txt'),
            has_units=True,
            apply_filter={'unavailable': 1}
        )
    assert exc_info.value.args[0] == 'Column "unavailable" in apply_filter was not found in file "zrecall_yr.txt"'

    # Error: invalid column value type
    with pytest.raises(Exception) as exc_info:
        data_manager.simulated_timeseries_df(
            sim_file=os.path.join(txtinout_dir, 'zrecall_yr.txt'),
            has_units=True,
            apply_filter={'name': 1}
        )
    assert 'Column "name" in apply_filter for file "zrecall_yr.txt" must be a list' in exc_info.value.args[0]

    # Error: empty DataFrame extracted by apply_filter
    val = ['hru007']
    with pytest.raises(Exception) as exc_info:
        data_manager.simulated_timeseries_df(
            sim_file=os.path.join(txtinout_dir, 'zrecall_yr.txt'),
            has_units=True,
            apply_filter={'name': val}
        )
    assert exc_info.value.args[0] == f'Filtering by column "name" with values "{val}" returned no rows in "zrecall_yr.txt"'

    # Error: invalid column name in usecols
    with pytest.raises(Exception) as exc_info:
        data_manager.simulated_timeseries_df(
            sim_file=os.path.join(txtinout_dir, 'zrecall_yr.txt'),
            has_units=True,
            usecols=['unavailable_col']
        )
    assert exc_info.value.args[0] == 'Column "unavailable_col" specified in "usecols" was not found in file "zrecall_yr.txt"'

    # Error: invalid JSON file extension to save the DataFrame
    with pytest.raises(Exception) as exc_info:
        data_manager.simulated_timeseries_df(
            sim_file=os.path.join(txtinout_dir, 'zrecall_yr.txt'),
            has_units=True,
            json_file='ext_invalid.txt'
        )
    assert exc_info.value.args[0] == 'Expected ".json" extension for "json_file", but got ".txt"'


def test_error_hru_stats_from_daily_simulation(
    data_manager
):

    # Error: invalid JSON file extension to save the DataFrame
    with pytest.raises(Exception) as exc_info:
        data_manager.hru_stats_from_daily_simulation(
            sim_file='channel_sd_mon.txt',
            has_units=True,
            gis_id=771,
            sim_col='flo_out'
        )
    assert exc_info.value.args[0] == 'Statistical summary applies only to daily time series files ending with "_day"; received file name "channel_sd_mon"'
