import pathlib
import pandas
import typing
from . import utils
from . import validators


class FileReader:
    '''
    Provide functionality to read, filter, and write data
    from a TXT file located in the `TxtInOut` folder.
    '''

    def __init__(
        self,
        path: str | pathlib.Path,
        has_units: bool
    ):
        '''
        Initialize a FileReader instance to read data from a TXT file.

        Args:
            path (str or Path): Path to the TXT file to be read.
            has_units (bool): If `True`, the second row of the file contains units.

        Example:
            ```python
            reader = FileReader(
                path='C:\\users\\username\\project\\Scenarios\\Default\\TxtInOut\\plants.plt',
                has_units=False
            )
            ```
        '''

        # Check input variables type
        validators._variable_origin_static_type(
            vars_types=typing.get_type_hints(
                obj=self.__class__.__init__
            ),
            vars_values=locals()
        )

        # Absolute path
        path = pathlib.Path(path).resolve()

        self.has_units = has_units

        # if output ends with _day, _mon, _yr, _aa, _subday (removing the suffix), it means is an output file from SWAT.
        # if file is a csv is output file
        self.is_output_file = path.stem.endswith(('_day', '_mon', '_yr', '_aa', '_subday')) or path.suffix == '.csv'

        # skips the header
        skip_rows = [0, 2] if self.has_units else [0]

        # read only first line of file
        with open(path, 'r', encoding='latin-1') as file:
            self.header_file = file.readline()

        self.df = utils._load_file(path, skip_rows=skip_rows)

        # if file is a csv is output file
        if path.suffix == '.csv' and self.has_units:
            _df = pandas.read_csv(path, skiprows=[0], nrows=2, header=None, skipinitialspace=True)
            self.units_row = utils._clean(_df).iloc[1].copy()

        elif self.has_units:  # TXT file with a units row
            # The units row may contain empty values, making it unreliable to parse with read_csv.
            # Instead, we use read_fwf to handle fixed-width formatting and infer column boundaries
            # based on the first data row.
            # In some cases, file formatting may be inconsistent (e.g., misaligned spacing between
            # the header and units row). If such inconsistencies are detected, a warning will be
            # issued when overwriting the file, though compatibility with SWAT+ is still preserved.

            # Attempt parsing using the first data row as a reference for alignment.
            _df = pandas.read_fwf(path, skiprows=[0, 1], nrows=2, header=None)
            self.units_row = utils._clean(_df).iloc[0].copy()

            # If only one row is returned (the df is empty), fall back to using the header row as reference.
            # This approach is less reliable and more prone to alignment issues.
            if len(_df) == 1:
                _df = pandas.read_fwf(path, skiprows=[0], nrows=2, header=None)
                self.units_row = utils._clean(_df).iloc[1].copy()

        else:
            self.units_row = None

        self.path = path
