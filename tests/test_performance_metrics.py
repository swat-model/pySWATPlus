import pySWATPlus
import pytest


@pytest.fixture(scope='class')
def performance_metrics():

    # initialize TxtinoutReader class
    performance_metrics = pySWATPlus.PerformanceMetrics()

    yield performance_metrics


def test_error_options(
    performance_metrics
):

    error_options = performance_metrics.error_options

    assert isinstance(error_options, dict)
    assert len(error_options) == 6
