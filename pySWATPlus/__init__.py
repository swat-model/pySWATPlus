from .txtinout_reader import TxtinoutReader
from .filereader import FileReader
from .cal_sensitivity_analyzer import SensitivityAnalyzer
from .performance_metrics import PerformanceMetrics
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    # If package is not installed yet (e.g., during dev)
    __version__ = "0.0.0"


__all__ = [
    'TxtinoutReader',
    'FileReader',
    'SensitivityAnalyzer',
    'PerformanceMetrics',
    '__version__'
]
