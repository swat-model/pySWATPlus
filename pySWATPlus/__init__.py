from .txtinoutreader import TxtinoutReader
from .filereader import FileReader
from .calsensitivityanalyzer import CalSensitivityAnalyzer
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
    'CalSensitivityAnalyzer',
    'PerformanceMetrics',
    '__version__'
]
