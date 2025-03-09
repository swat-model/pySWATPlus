import pandas as pd
import warnings
import dask.dataframe as dd
from pathlib import Path
from typing import Union, List, Dict, Literal, Optional
import os

def read_csv(
        path: Union[str, Path], 
        skip_rows: List[int],
        usecols: List[str],
        filter_by:  Dict[str, List[str]],
        separator: str,
        encoding: str, 
        engine: Literal['c', 'python'],
        mode: Literal['dask', 'pandas'] = 'dask' )-> Union[pd.DataFrame, dd.DataFrame]:

    '''
    Read a CSV file using either Dask or Pandas and filter the data based on criteria.

        Parameters:
        path (Union[str, Path]): The path to the CSV file.
        skip_rows (List[int]): List of specific row numbers to skip.
        usecols (List[str]): A list of column names to read
        filter_by (Dict[str, List[str]): A dictionary of column names and values (list of str) to filter by.
        separator (str): The delimiter used in the CSV file.
        encoding (str): The character encoding to use when reading the file.
        engine (Literal['c', 'python']): The CSV parsing engine to use (e.g., 'c' for C engine, 'python' for Python engine).
        mode (Literal['dask', 'pandas']): The mode to use for reading ('dask' or 'pandas').

        Returns:
        Union[pd.DataFrame, dd.DataFrame]: A DataFrame containing the filtered data. The type depends on the chosen mode.

        Note:
        - When `mode` is 'dask', a Dask DataFrame is returned.
        - When `mode` is 'pandas', a Pandas DataFrame is returned.

        Example:
        read_csv('plants.plt', skip_rows=[0], usecols=['name', 'plnt_typ', 'gro_trig'], filter_by={'plnt_typ': 'perennial'}, separator=r"[ ]{2,}", encoding="utf-8", engine='python', mode='dask')
    '''
    
    if mode == 'dask':
        df = dd.read_csv(
            path,
            sep=separator,
            skiprows=skip_rows,
            assume_missing=True,
            usecols=usecols,
            encoding=encoding,
            engine=engine
        )
        
        for column, keys in filter_by.items():
            #check if keys is a list or a str
            if isinstance(keys, list):
                df = df.loc[df[column].isin(keys)]
            else:
                df = df.loc[df[column] == keys]
        

        return df.compute()
    
    elif mode == 'pandas':
        df = pd.read_csv(
            path,
            sep=separator,
            skiprows=skip_rows,
            usecols=usecols,
            encoding=encoding,
            engine=engine
        )

        for column, keys in filter_by.items():
            #check if keys is a list or a str
            if isinstance(keys, list):
                df = df.loc[df[column].isin(keys)]
            else:
                df = df.loc[df[column] == keys]

        return df


class FileReader:

    def __init__(self, 
                 path: str, 
                 has_units: bool = False, 
                 index: Optional[str] = None, 
                 usecols: List[str] = None, 
                 filter_by:  Dict[str, List[str]] = {}):
        
        '''
        Initialize a FileReader instance to read data from a file.

        Parameters:
        path (str, os.PathLike): The path to the file.
        has_units (bool): Indicates if the file has units (default is False).
        index (str, optional): The name of the index column (default is None).
        usecols (List[str], optional): A list of column names to read (default is None).
        filter_by (Dict[str, List[str]]): A dictionary of column names and values (list of str) to filter by (default is an empty dictionary).

        Raises:
        FileNotFoundError: If the specified file does not exist.
        TypeError: If there's an issue reading the file or if the resulting DataFrame is not of type pandas.DataFrame.

        Attributes:
        df (pd.DataFrame): a dataframe containing the data from the file.


        Note:
        - When has_units is True, the file is expected to have units information, and the units_file attribute will be set.
        - The read_csv method is called with different parameters to attempt reading the file with various delimiters and encodings.
        - If an index column is specified, it will be used as the index in the DataFrame.

        Example:
        FileReader('plants.plt', has_units = False, index = 'name', usecols=['name', 'plnt_typ', 'gro_trig'], filter_by={'plnt_typ': 'perennial'})

        '''
        if not isinstance(path, (str, os.PathLike)):
            raise TypeError("path must be a string or os.PathLike object")
        
        path = Path(path).resolve()

        if not path.is_file():
            raise FileNotFoundError("file does not exist")

        df = None
        
        #skips the header
        skip_rows = [0]
        if has_units:
            skip_rows.append(2) #skips the units
        
        #if file is txt
        if path.suffix == '.csv':
            raise TypeError("Not implemented yet")

        else:
            #read only first line of file    
            with open(path, 'r', encoding='latin-1') as file:
                # Read the first line
                self.header_file = file.readline()
                        
            if has_units:
                #read only third line of file
                with open(path, 'r', encoding='latin-1') as file:
                    # Use a for loop to iterate through the file, reading lines
                    for line_number, line in enumerate(file, start=1):
                        if line_number == 3:
                            self.units_file = line
                            break



            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("error")

                #first try with dask. if it fails, try with pandas
                try:
                    df = read_csv(path, skip_rows, usecols, filter_by, '\s+', 'utf-8', 'c', 'dask')
                except:
                    try:
                        df = read_csv(path, skip_rows, usecols, filter_by, '\s+', 'latin-1', 'c', 'dask')
                    except:
                        try:
                            df = read_csv(path, skip_rows, usecols, filter_by, r"[ ]{2,}", 'utf-8', 'python', 'dask')
                        except:
                            try:
                                df = read_csv(path, skip_rows, usecols, filter_by, r"[ ]{2,}", 'latin-1', 'python', 'dask')
                            except:    
                                try:
                                    df = read_csv(path, skip_rows, usecols, filter_by, '\s+', 'utf-8', 'c', 'pandas')
                                except:
                                    try:
                                        df = read_csv(path, skip_rows, usecols, filter_by, '\s+', 'latin-1', 'c', 'pandas')
                                    except:
                                        try:
                                            df = read_csv(path, skip_rows, usecols, filter_by, r"[ ]{2,}", 'utf-8', 'python', 'pandas')
                                        except:
                                            try:
                                                df = read_csv(path, skip_rows, usecols, filter_by, r"[ ]{2,}", 'latin-1', 'python', 'pandas')

                                            except Exception as e:
                                                raise e

                

        #check if df is a pandas dataframe
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Something went wrong!")
        
        df.columns = df.columns.str.replace(' ', '')

        if index is not None:
            aux_index_name = 'aux_index'

            # Add the copied 'name' column back to the DataFrame
            df[aux_index_name] = df[index]

            # Set the 'name' column as the index
            df.set_index(aux_index_name, inplace=True)

            # Change the index name to a default name, such as 'index'
            df.rename_axis('', inplace=True)

        self.df = df
        self.path = path


    def _store_text(self) -> None:
        '''
        Store the DataFrame as a formatted text file.

        This method converts the DataFrame to a formatted string with adjusted column widths and writes it to a .txt file.
        The text file will contain the header and the formatted data.

        TODO: This function still does not write the corresponding units, in case the original file had it.

        Returns:
        None
        '''
        data_str = self.df.to_string(index=False, justify='left', col_space=15)

        # Find the length of the longest string in each column
        max_lengths = self.df.apply(lambda x: x.astype(str).str.len()).max()

        # Define the column widths based on the longest string length
        column_widths = {column: max_length + 3 for column, max_length in max_lengths.items()}

        # Convert the DataFrame to a formatted string with adjusted column widths
        data_str = self.df.to_string(index=False, justify='right', col_space=column_widths)

        # Write the string to a .txt file
        with open(self.path, 'w') as file:
            file.write(self.header_file)
            file.write(data_str)
        
    
    def _store_csv(self) -> None:
        '''
        Store the DataFrame as a CSV file.

        This method raises a TypeError to indicate that storing as a CSV file is not implemented yet.

        Returns:
        None
        '''
        raise TypeError("Not implemented yet")

    def overwrite_file(self) -> None:
        '''
        Overwrite the original file with the DataFrame.

        This method checks the file extension and calls the appropriate storage method (_store_csv or _store_text).

        Returns:
        None
        '''
        if self.path.suffix == '.csv':
            self._store_csv()
        else:
            self._store_text()        
    


        
        

    


