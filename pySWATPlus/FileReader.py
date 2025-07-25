import pandas
import pathlib
import typing


class FileReader:

    def __init__(
        self,
        path: str | pathlib.Path,
        has_units: bool = False,
        usecols: typing.Optional[list[str]] = None,
        filter_by: typing.Optional[str] = None
    ):
        '''
        Initialize a FileReader instance to read data from a file.

        Parameters:
            path (str, Path): The path to the file.
            has_units (bool): Indicates if the file has units (default is False).
            usecols (list[str], optional): A list of column names to read (default is None).
            filter_by (str, optional): Pandas query string to select applicable rows (default is None).

        Raises:
            FileNotFoundError: If the specified file does not exist.
            TypeError: If there's an issue reading the file or if the resulting DataFrame is not of type pandas.DataFrame.

        Attributes:
            df (pandas.DataFrame): a dataframe containing the data from the file.

        Example:
            ```python
            reader = FileReader(
                'plants.plt',
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
        if path.suffix == '.csv':
            raise TypeError("Not implemented yet")

        # read only first line of file
        with open(path, 'r', encoding='latin-1') as file:
            self.header_file = file.readline()

        self.df = pandas.read_fwf(
            path,
            skiprows=skip_rows,
            usecols=usecols
        )

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
        Overwrites the TXT file after converting the content DataFrame
        to a formatted string with adjusted column widths.

        Returns:
            None
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
