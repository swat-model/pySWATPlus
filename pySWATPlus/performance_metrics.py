import pandas
import pathlib
import typing
from .data_manager import DataManager
from . import utils
from . import validators


class PerformanceMetrics:
    '''
    Provide functionality to evaluate model perfromance between simulated and ovserved values.
    '''

    @property
    def indicator_names(
        self
    ) -> dict[str, str]:
        '''
        Returns a dictionary of available performance indicators. The keys are
        commonly used abbreviations, and the values are the corresponding full
        indicator names. The computed indicator values are treated as performance
        metrics of the model. Available abbreviations:

        - `NSE`: Nash–Sutcliffe Efficiency
        - `KGE`: Kling–Gupta Efficiency
        - `MSE`: Mean Squared Error
        - `RMSE`: Root Mean Squared Error
        - `PBIAS`: Percent Bias
        - `MARE`: Mean Absolute Relative Error
        '''

        abbr_name = {
            'NSE': 'Nash-Sutcliffe Efficiency',
            'KGE': 'Kling-Gupta Efficiency',
            'MSE': 'Mean Squared Error',
            'RMSE': 'Root Mean Squared Error',
            'PBIAS': 'Percent Bias',
            'MARE': 'Mean Absolute Relative Error'
        }

        return abbr_name

    def compute_nse(
        self,
        df: pandas.DataFrame,
        sim_col: str,
        obs_col: str
    ) -> float:
        '''
        Calculate the [`Nash-Sutcliffe Efficiency`](https://doi.org/10.1016/0022-1694(70)90255-6)
        metric between simulated and observed values

        Args:
            df (pandas.DataFrame): DataFrame containing at least two columns with simulated and observed values.

            sim_col (str): Name of the column containing simulated values.

            obs_col (str): Name of the column containing observed values.

        Returns:
            Computed value of the `Nash-Sutcliffe Efficiency` metric.
        '''

        # Check input variables type
        validators._variable_origin_static_type(
            vars_types=typing.get_type_hints(
                obj=self.compute_nse
            ),
            vars_values=locals()
        )

        # Simulation values
        sim_arr = df[sim_col].astype(float)

        # Observed values
        obs_arr = df[obs_col].astype(float)

        # Output
        numerator = ((sim_arr - obs_arr).pow(2)).sum()
        denominator = ((obs_arr - obs_arr.mean()).pow(2)).sum()
        output = float(1 - numerator / denominator)

        return output

    def compute_kge(
        self,
        df: pandas.DataFrame,
        sim_col: str,
        obs_col: str
    ) -> float:
        '''
        Calculate the [`Kling-Gupta Efficiency`](https://doi.org/10.1016/j.jhydrol.2009.08.003)
        metric between simulated and observed values

        Args:
            df (pandas.DataFrame): DataFrame containing at least two columns with simulated and observed values.

            sim_col (str): Name of the column containing simulated values.

            obs_col (str): Name of the column containing observed values.

        Returns:
            Computed value of the `Kling-Gupta Efficiency` metric.
        '''

        # Check input variables type
        validators._variable_origin_static_type(
            vars_types=typing.get_type_hints(
                obj=self.compute_kge
            ),
            vars_values=locals()
        )

        # Simulation values
        sim_arr = df[sim_col].astype(float)

        # Observed values
        obs_arr = df[obs_col].astype(float)

        # Pearson correlation coefficient (r)
        r = sim_arr.corr(obs_arr)

        # Variability of prediction errors
        alpha = sim_arr.std() / obs_arr.std()

        # Bias
        beta = sim_arr.mean() / obs_arr.mean()

        # Output
        output = float(1 - pow(pow(r - 1, 2) + pow(alpha - 1, 2) + pow(beta - 1, 2), 0.5))

        return output

    def compute_mse(
        self,
        df: pandas.DataFrame,
        sim_col: str,
        obs_col: str
    ) -> float:
        '''
        Calculate the `Mean Squared Error` metric between simulated and observed values

        Args:
            df (pandas.DataFrame): DataFrame containing at least two columns with simulated and observed values.

            sim_col (str): Name of the column containing simulated values.

            obs_col (str): Name of the column containing observed values.

        Returns:
            Computed value of the `Mean Squared Error` metric.
        '''

        # Check input variables type
        validators._variable_origin_static_type(
            vars_types=typing.get_type_hints(
                obj=self.compute_mse
            ),
            vars_values=locals()
        )

        # Simulation values
        sim_arr = df[sim_col].astype(float)

        # Observed values
        obs_arr = df[obs_col].astype(float)

        # Output
        output = float(((sim_arr - obs_arr).pow(2)).mean())

        return output

    def compute_rmse(
        self,
        df: pandas.DataFrame,
        sim_col: str,
        obs_col: str
    ) -> float:
        '''
        Calculate the `Root Mean Squared Error` metric between simulated and observed values.

        Args:
            df (pandas.DataFrame): DataFrame containing at least two columns with simulated and observed values.

            sim_col (str): Name of the column containing simulated values.

            obs_col (str): Name of the column containing observed values.

        Returns:
            Computed value of the `Root Mean Squared Error` metric.
        '''

        # Check input variables type
        validators._variable_origin_static_type(
            vars_types=typing.get_type_hints(
                obj=self.compute_rmse
            ),
            vars_values=locals()
        )

        # computer MSE error
        mse_value = self.compute_mse(
            df=df,
            sim_col=sim_col,
            obs_col=obs_col
        )

        # Output
        output = float(pow(mse_value, 0.5))

        return output

    def compute_pbias(
        self,
        df: pandas.DataFrame,
        sim_col: str,
        obs_col: str
    ) -> float:
        '''
        Calculate the `Percent Bias` metric between simulated and observed values.

        Args:
            df (pandas.DataFrame): DataFrame containing at least two columns with simulated and observed values.

            sim_col (str): Name of the column containing simulated values.

            obs_col (str): Name of the column containing observed values.

        Returns:
            Computed value of the `Percent Bias` metric.
        '''

        # Check input variables type
        validators._variable_origin_static_type(
            vars_types=typing.get_type_hints(
                obj=self.compute_pbias
            ),
            vars_values=locals()
        )

        # Simulation values
        sim_arr = df[sim_col].astype(float)

        # Observed values
        obs_arr = df[obs_col].astype(float)

        # Output
        output = float(100 * (sim_arr - obs_arr).sum() / obs_arr.sum())

        return output

    def compute_mare(
        self,
        df: pandas.DataFrame,
        sim_col: str,
        obs_col: str
    ) -> float:
        '''
        Calculate the `Mean Absolute Relative Error` metric between simulated and observed values

        Args:
            df (pandas.DataFrame): DataFrame containing at least two columns with simulated and observed values.

            sim_col (str): Name of the column containing simulated values.

            obs_col (str): Name of the column containing observed values.

        Returns:
            Computed value of the `Mean Absolute Relative Error` metric.
        '''

        # Check input variables type
        validators._variable_origin_static_type(
            vars_types=typing.get_type_hints(
                obj=self.compute_mare
            ),
            vars_values=locals()
        )

        # Simulation values
        sim_arr = df[sim_col].astype(float)

        # Observed values
        obs_arr = df[obs_col].astype(float)

        # Output
        output = float(((obs_arr - sim_arr) / obs_arr).abs().mean())

        return output

    def _validate_indicator_abbr(
        self,
        indicators: list[str]
    ) -> None:
        '''
        Validate each indicator abbreviation in the provided list.
        '''

        abbr_indicator = self.indicator_names
        for ind in indicators:
            if ind not in abbr_indicator:
                raise ValueError(
                    f'Invalid indicator "{ind}"; expected names are {list(abbr_indicator.keys())}'
                )

        return None

    def compute_from_abbr(
        self,
        df: pandas.DataFrame,
        sim_col: str,
        obs_col: str,
        indicator: str
    ) -> float:
        '''
        Compute the performance metric between simulated and observed values based on the provided indicator abbreviation.

        Args:
            df (pandas.DataFrame): DataFrame containing at least two columns with simulated and observed values.

            sim_col (str): Name of the column containing simulated values.

            obs_col (str): Name of the column containing observed values.

            indicator (str): Abbreviation of the indicator, selected from the available options in the property
                [`indicator_names`](https://swatmodel.github.io/pySWATPlus/api/performance_metrics/#pySWATPlus.PerformanceMetrics.indicator_names).

        Returns:
            Computed metric value corresponding to the specified indicator.
        '''

        # Check input variables type
        validators._variable_origin_static_type(
            vars_types=typing.get_type_hints(
                obj=self.compute_from_abbr
            ),
            vars_values=locals()
        )

        # Validate abbreviation of indicators
        self._validate_indicator_abbr(
            indicators=[indicator]
        )

        # Method from indicator abbreviation
        indicator_method = getattr(
            self,
            f'compute_{indicator.lower()}'
        )

        # Indicator value
        indicator_value = indicator_method(
            df=df,
            sim_col=sim_col,
            obs_col=obs_col
        )

        return float(indicator_value)

    def scenario_indicators(
        self,
        sensim_file: str | pathlib.Path,
        df_name: str,
        sim_col: str,
        obs_file: str | pathlib.Path,
        date_format: str,
        obs_col: str,
        indicators: list[str],
        json_file: typing.Optional[str | pathlib.Path] = None
    ) -> dict[str, typing.Any]:
        '''
        Compute performance metrics for sample scenarios obtained using the method
        [`simulation_by_sample_parameters`](https://swat-model.github.io/pySWATPlus/api/sensitivity_analyzer/#pySWATPlus.SensitivityAnalyzer.simulation_by_sample_parameters).

        Before computing the metrics, simulated and observed values are normalized using the formula `(v - min_o) / (max_o - min_o)`,
        where `min_o` and `max_o` represent the minimum and maximum of observed values, respectively.

        The method returns a dictionary with two keys:

        - `problem`: The definition dictionary passed to sampling.
        - `indicator`: A `DataFrame` containing the `Scenario` column and one column per indicator,
          with scenario indices and corresponding indicator values.

        Before computing the indicators, both simulated and observed values are normalized using the formula
        `(v - min_o) / (max_o - min_o)`, where `min_o` and `max_o` represent the minimum and maximum of observed values, respectively.
        All negative and `None` observed values are removed before computing `min_o` and `max_o` to prevent errors during normalization.

        Args:
            sensim_file (str | pathlib.Path): Path to the `sensitivity_simulation.json` file produced by `simulation_by_sobol_sample`.

            df_name (str): Name of the `DataFrame` within `sensitivity_simulation.json` from which to compute scenario indicators.

            sim_col (str): Name of the column in `df_name` containing simulated values.

            obs_file (str | pathlib.Path): Path to the CSV file containing observed data. The file must include a
                `date` column (used to merge simulated and observed data) and use a comma as the separator.

            date_format (str): Date format of the `date` column in `obs_file`, used to parse `datetime.date` objects from date strings.

            obs_col (str): Name of the column in `obs_file` containing observed data.

            indicators (list[str]): List of indicator abbreviations selected from the available options in the property
                [`indicator_names`](https://swatmodel.github.io/pySWATPlus/api/performance_metrics/#pySWATPlus.PerformanceMetrics.indicator_names).

            json_file (str | pathlib.Path, optional): Path to a JSON file for saving the output `DataFrame` containing indicator values.
                If `None` (default), the `DataFrame` is not saved.

        Returns:
            Dictionary with two keys, `problem` and `indicator`, and their corresponding values.
        '''

        # Check input variables type
        validators._variable_origin_static_type(
            vars_types=typing.get_type_hints(
                obj=self.scenario_indicators
            ),
            vars_values=locals()
        )

        # Validate abbreviation of indicators
        self._validate_indicator_abbr(
            indicators=indicators
        )

        # Observed DataFrame
        obs_df = utils._df_observe(
            obs_file=pathlib.Path(obs_file).resolve(),
            date_format=date_format,
            obs_col=obs_col
        )
        obs_df.columns = ['date', 'obs']

        # Retrieve sensitivity output
        sensitivity_sim = utils._sensitivity_output_retrieval(
            sensim_file=pathlib.Path(sensim_file).resolve(),
            df_name=df_name,
            add_problem=True,
            add_sample=False
        )

        # Empty DataFrame to store scenario indicators
        ind_df = pandas.DataFrame(
            columns=indicators
        )

        # Iterate scenarios
        for key, df in sensitivity_sim['scenario'].items():
            df = df[['date', sim_col]]
            df.columns = ['date', 'sim']
            # Merge scenario DataFrame with observed DataFrame
            merge_df = df.merge(
                right=obs_df.copy(),
                how='inner',
                on='date'
            )
            # Normalized DataFrame
            norm_df = utils._df_normalize(
                df=merge_df[['sim', 'obs']],
                norm_col='obs'
            )
            # Iterate indicators
            for indicator in indicators:
                # Store indicator value in DataFrame
                ind_val = PerformanceMetrics().compute_from_abbr(
                    df=norm_df,
                    sim_col='sim',
                    obs_col='obs',
                    indicator=indicator
                )
                ind_df.loc[key, indicator] = ind_val

        # Reset index to scenario column
        scnro_col = 'Scenario'
        ind_df = ind_df.reset_index(
            names=[scnro_col]
        )
        ind_df[scnro_col] = ind_df[scnro_col].astype(int)

        # Save DataFrame
        if json_file is not None:
            json_file = pathlib.Path(json_file).resolve()
            # Raise error for invalid JSON file extension
            validators._json_extension(
                json_file=json_file
            )
            # Write DataFrame to the JSON file
            ind_df.to_json(
                path_or_buf=json_file,
                orient='records',
                indent=4
            )

        # Output dictionary
        output = {
            'problem': sensitivity_sim['problem'],
            'indicator': ind_df
        }

        return output

    def indicator_from_file(
        self,
        sim_file: str | pathlib.Path,
        sim_col: str,
        extract_sim: dict[str, typing.Any],
        obs_file: str | pathlib.Path,
        date_format: str,
        obs_col: str,
        indicators: list[str]
    ) -> dict[str, float]:

        '''
        Compute performance metrics for simulated values obtained using the method
        [`run_swat`](https://swat-model.github.io/pySWATPlus/api/txtinout_reader/#pySWATPlus.TxtinoutReader.run_swat).

        Before computing the indicators, simulated and observed values are normalized using the formula `(v - min_o) / (max_o - min_o)`,
        where `min_o` and `max_o` represent the minimum and maximum of observed values, respectively. All negative and `None` observed values
        are removed before computing `min_o` and `max_o` to prevent errors during normalization.

        Args:
            sim_file (str | pathlib.Path): Path to the simulation file generated using the method
                [`run_swat`](https://swat-model.github.io/pySWATPlus/api/txtinout_reader/#pySWATPlus.TxtinoutReader.run_swat).

            sim_col (str): Name of the column in `sim_file` containing simulated data.

            extract_sim (dict[str, typing.Any]): Dictionary specifying input variable configurations for
                [`simulated_timeseries_df`](https://swat-model.github.io/pySWATPlus/api/data_manager/#pySWATPlus.DataManager.simulated_timeseries_df)
                to extract data from `sim_file`. Each key corresponds to an input variable name, and its value is the parameter supplied to the method.

                - *Required key:* `has_units`.
                - *Optional key:* `begin_date`, `end_date`, `ref_day`, `ref_month`, and `apply_filter`.

                !!! note
                    The optional key `usecols` should **not** be included in `extract_sim`. Although no error will be raised,
                    it will be ignored because the `sim_col` argument is internally used to define the `usecols` list.

            obs_file (str | pathlib.Path): Path to the CSV file containing observed data. The file must include a
                `date` column (used to merge simulated and observed data) and use a comma as the separator.

            date_format (str): Date format of the `date` column in `obs_file`, used to parse `datetime.date` objects from date strings.

            obs_col (str): Name of the column in `obs_file` containing observed data.

            indicators (list[str]): List of indicator abbreviations selected from the available options in the property
                [`indicator_names`](https://swatmodel.github.io/pySWATPlus/api/performance_metrics/#pySWATPlus.PerformanceMetrics.indicator_names).

        Returns:
            Dictionary where each key is an indicator abbreviation, and value is the corresponding performance metric.
        '''

        # Check input variables type
        validators._variable_origin_static_type(
            vars_types=typing.get_type_hints(
                obj=self.indicator_from_file
            ),
            vars_values=locals()
        )

        # Validate abbreviation of indicators
        self._validate_indicator_abbr(
            indicators=indicators
        )

        # Simulated DataFrame
        extract_sim['usecols'] = [sim_col]
        sim_df = DataManager().simulated_timeseries_df(
            sim_file=pathlib.Path(sim_file).resolve(),
            **extract_sim
        )
        sim_df.columns = ['date', 'sim']

        # Observed DataFrame
        obs_df = utils._df_observe(
            obs_file=pathlib.Path(obs_file).resolve(),
            date_format=date_format,
            obs_col=obs_col
        )
        obs_df.columns = ['date', 'obs']

        # Merge simulated and observed DataFrames
        merge_df = sim_df.merge(
            right=obs_df,
            how='inner',
            on='date'
        )

        # Normalized DataFrame
        norm_df = utils._df_normalize(
            df=merge_df[['sim', 'obs']],
            norm_col='obs'
        )

        # Empty dictionary to store indicator values
        ind_dict = {}

        # Iterate indicator
        for ind in indicators:
            # Store indicator value in dictionary
            ind_val = PerformanceMetrics().compute_from_abbr(
                df=norm_df,
                sim_col='sim',
                obs_col='obs',
                indicator=ind
            )
            ind_dict[ind] = ind_val

        return ind_dict
