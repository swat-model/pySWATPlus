import os
import shutil
import pySWATPlus
import tempfile


def test_filereader():

    # set up TxtInOut folder path
    txtinout_folder = os.path.join(os.path.dirname(__file__), 'TxtInOut')

    # initializing FileReader class instance
    file_reader = pySWATPlus.FileReader(
        path=os.path.join(txtinout_folder, 'hydrology.hyd'),
        has_units=False,
    )

    # pass test for DataFrame attribute
    df = file_reader.df
    assert df.shape[0] == 561

    # change varibale value
    variable = 'epco'
    value = 0.75
    df[variable] = value

    # rewrite the file
    file_reader.overwrite_file()

    # read the new DataFrame
    df = file_reader.df
    assert df[variable].unique()[0] == value

    with tempfile.TemporaryDirectory() as tmp_dir:
        # pass test for rewriting empty DataFrame in a TXT file
        file_name = 'hru_soilc_stat.txt'
        shutil.copy2(
            src=os.path.join(txtinout_folder, file_name),
            dst=os.path.join(tmp_dir, file_name)
        )
        file_reader = pySWATPlus.FileReader(
            path=os.path.join(tmp_dir, file_name),
            has_units=True
        )
        df = file_reader.df
        assert len(df) == 0
        file_reader.overwrite_file()

        # pass test for rewriting DataFrame with 'has_units' key in a TXT file
        file_name = 'basin_carbon_all.txt'
        shutil.copy2(
            src=os.path.join(txtinout_folder, file_name),
            dst=os.path.join(tmp_dir, file_name)
        )
        file_reader = pySWATPlus.FileReader(
            path=os.path.join(tmp_dir, file_name),
            has_units=True
        )
        df = file_reader.df
        assert len(df) == 0
        file_reader.overwrite_file()


def test_github():

    # GitHub test function tigger when no code is changed
    assert str(2) == '2'
