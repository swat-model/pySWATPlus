import pySWATPlus
import pytest


def test_validate_params():

    # pass test for None input
    output = pySWATPlus.utils._validate_params(
        params=None
    )
    assert output is None

    # error test for input other than dictionary
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.utils._validate_params(
            params=[]
        )
    assert exc_info.value.args[0] == "'params' must be a dictionary mapping filenames to parameter specs."

    # error test for dictionary input but key's value other than dictionary
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.utils._validate_params(
            params={
                'plants.plt': []
            }
        )
    assert exc_info.value.args[0] == "Expected a dictionary for file 'plants.plt', got list"

    # error test for has_units key
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.utils._validate_params(
            params={
                'plants.plt': {'has_units': []}
            }
        )
    assert exc_info.value.args[0] == "'has_units' for file 'plants.plt' must be a boolean."

    with pytest.raises(Exception) as exc_info:
        pySWATPlus.utils._validate_params(
            params={
                'plants.plt': {
                    'bm_e': {'value': 2}
                }
            }
        )
    assert exc_info.value.args[0] == "'has_units' key is missing for file 'plants.plt'."

    # error test for other keys
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.utils._validate_params(
            params={
                'plants.plt': {
                    'has_units': False,
                    'bm_e': ()
                }
            }
        )
    assert exc_info.value.args[0] == "'bm_e' for file 'plants.plt' must be either a dictinary or a list of dictionaries, got tuple"

    # error test for missing 'value' key in the parameter
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.utils._validate_params(
            params={
                'plants.plt': {
                    'has_units': False,
                    'bm_e': {'val': 2}
                }
            }
        )
    assert exc_info.value.args[0] == "Missing 'value' key for 'bm_e' in file 'plants.plt'."

    # error test for other than integer or float type for 'value' key
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.utils._validate_params(
            params={
                'plants.plt': {
                    'has_units': False,
                    'bm_e': {'value': 'hi'}
                }
            }
        )
    assert exc_info.value.args[0] == "'value' for 'bm_e' in file 'plants.plt' must be numeric."

    # error test for invalid 'change_type' key
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.utils._validate_params(
            params={
                'plants.plt': {
                    'has_units': False,
                    'bm_e': {'value': 100, 'change_type': 'abs'}
                }
            }
        )
    assert exc_info.value.args[0] == "Invalid 'change_type' value 'abs' for 'bm_e' in file 'plants.plt'. Expected one of: absval, abschg, pctchg."

    # error test for invalid 'filter_by' key
    with pytest.raises(Exception) as exc_info:
        pySWATPlus.utils._validate_params(
            params={
                'plants.plt': {
                    'has_units': False,
                    'bm_e': {'value': 100, 'change_type': 'absval', 'filter_by': 5}
                }
            }
        )
    assert exc_info.value.args[0] == "'filter_by' for 'bm_e' in file 'plants.plt' must be a string."
