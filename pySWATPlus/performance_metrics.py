class PerformanceMetrics:
    '''
    WARNING:
        This class is currently under development and not recommended for use.

    Provide functionality to compute error and efficiency metrics for the SWAT+ model.
    '''

    @property
    def error_options(
        self
    ) -> dict[str, str]:
        '''
        Return a dictionary of available error options. Keys are the commonly used abbreviations,
        and values are the corresponding full error metric names.
        '''

        error_names = {
            'NSE': 'Nash-Sutcliffe Efficiency',
            'KGE': 'Kling-Gupta Efficiency',
            'MSE': 'Mean Squared Error',
            'RMSE': 'Root Mean Squared Error',
            'PBIAS': 'Percent Bias',
            'MARE': 'Mean Absolute Relative Error'
        }

        return error_names
