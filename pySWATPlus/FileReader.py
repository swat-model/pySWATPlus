import pandas
import pathlib
import typing
from . import utils


class FileReader:

    '''
    Provide functionality to read, filter, and write data
    from a TXT file located in the `TxtInOut` folder.
    '''

    def __init__(
        self,
        path: str | pathlib.Path,
        has_units: bool = False,
        usecols: typing.Optional[list[str]] = None,
        filter_by: typing.Optional[str] = None
    ):
        '''
        Initialize a FileReader instance to read data from a TXT file.

        Args:
            path (str or Path): Path to the TXT file to be read.
            has_units (bool): If `True`, the second row of the file contains units.
            usecols (list[str]): List of column names to read from the file.
            filter_by (str): A pandas query string to filter rows from the file.

        Raises:
            TypeError: If the input file has a `.csv` extension.

        Attributes:
            df (pandas.DataFrame): A DataFrame containing the loaded and optionally filtered data.

        Example:
            ```python
            reader = FileReader(
                path='C:\\users\\username\\project\\Scenarios\\Default\\TxtInOut\\plants.plt',
                has_units=False,
                usecols=['name', 'plnt_typ', 'gro_trig'],
                filter_by="plnt_typ == 'perennial'"
            )
            ```
        '''

        if not isinstance(path, (str, pathlib.Path)):
            raise TypeError("path must be a string or Path object")

        path = pathlib.Path(path).resolve()

        if not path.is_file():
            raise FileNotFoundError("file does not exist")

        # skips the header
        skip_rows = [0]

        # if file is txt
        if path.suffix.lower() == '.csv':
            raise TypeError("Not implemented yet")

        # read only first line of file
        with open(path, 'r', encoding='latin-1') as file:
            self.header_file = file.readline()

        self.df = utils._load_file(path, skip_rows=skip_rows, usecols=usecols)

        self.path = path

        if has_units:
            self.units_row = self.df.iloc[0].copy()
            self.df = self.df.iloc[1:].reset_index(drop=True)
        else:
            self.units_row = None

        if filter_by:
            self.df = self.df.query(filter_by)

    def overwrite_file(
        self
    ) -> None:
        '''
        Overwrite the original TXT file with the modified DataFrame content.
        If the file originally contained a unit row (below the header),
        it will be preserved and written back as part of the output.
        '''

        if self.units_row is not None:
            _df = pandas.concat([pandas.DataFrame([self.units_row]), self.df], ignore_index=True)
        else:
            _df = self.df

        # Replace NaN with empty strings to avoid printing 'NaN'
        _df = _df.fillna('')

        with open(self.path, 'w') as file:
            # Write the header file first
            file.write(self.header_file)

            if _df.empty:
                # Calculate max width for each column name (or set a minimum if you prefer)
                col_widths = [max(len(col), 1) + 3 for col in _df.columns]

                # Create format string with fixed widths, right-aligned
                fmt = ''.join([f'{{:>{w}}}' for w in col_widths])

                # Format and write the header line
                file.write(fmt.format(*_df.columns) + '\n')
                return

            max_lengths = _df.apply(lambda x: x.astype(str).str.len()).max()
            column_widths = {column: max_length + 3 for column, max_length in max_lengths.items()}
            data_str = _df.to_string(index=False, justify='right', col_space=column_widths)
            file.write(data_str)
