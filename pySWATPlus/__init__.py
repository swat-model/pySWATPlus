from .txtinout_reader import TxtinoutReader
from .data_manager import DataManager
from .sensitivity_analyzer import SensitivityAnalyzer
from .performance_metrics import PerformanceMetrics
from .calibration import Calibration
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    # If package is not installed yet (e.g., during dev)
    __version__ = "0.0.0"


__all__ = [
    'TxtinoutReader',
    'DataManager',
    'SensitivityAnalyzer',
    'PerformanceMetrics',
    'Calibration',
    '__version__'
]
