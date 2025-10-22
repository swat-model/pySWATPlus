import numpy
import shutil
import typing
import pathlib
from .txtinout_reader import TxtinoutReader
from .data_manager import DataManager
from . import newtype


def _simulation_output(
    track_sim: int,
    var_array: numpy.typing.NDArray[numpy.float64],
    num_sim: int,
    var_names: list[str],
    sim_dir: pathlib.Path,
    tio_dir: pathlib.Path,
    params_bounds: list[newtype.BoundDict],
    extract_data: dict[str, dict[str, typing.Any]],
    clean_setup: bool
) -> dict[str, typing.Any]:
    '''
    Run parallel simulations for sensitivity analysis and calibration, assigning each process
    to a dedicated logical CPU for optimized performance.
    '''

    # Dictionary mapping for sensitivity simulation name and variable
    var_dict = {
        var_names[i]: float(var_array[i]) for i in range(len(var_names))
    }

    # Create ParameterType dictionary to write calibration.cal file
    params_sim = []
    for i, param in enumerate(params_bounds):
        params_sim.append(
            {
                'name': param.name,
                'change_type': param.change_type,
                'value': var_dict[var_names[i]],
                'units': param.units,
                'conditions': param.conditions
            }
        )

    # Display start of current simulation for tracking
    print(
        f'Started simulation: {track_sim}/{num_sim}',
        flush=True
    )

    # Create simulation directory
    cpu_dir = f'sim_{track_sim}'
    cpu_path = sim_dir / cpu_dir
    cpu_path.mkdir()

    # Output simulation dictionary
    cpu_output = {
        'dir': cpu_dir,
        'array': var_array
    }

    # Initialize TxtinoutReader class
    tio_reader = TxtinoutReader(
        tio_dir=tio_dir
    )

    # Run SWAT+ model in CPU directory
    tio_reader.run_swat(
        sim_dir=cpu_path,
        parameters=params_sim
    )

    # Extract simulated data
    for sim_fname, sim_fdict in extract_data.items():
        sim_file = cpu_path / sim_fname
        df = DataManager().simulated_timeseries_df(
            sim_file=sim_file,
            **sim_fdict
        )
        cpu_output[f'{sim_file.stem}_df'] = df

    # Remove simulation directory
    if clean_setup:
        shutil.rmtree(cpu_path, ignore_errors=True)

    return cpu_output
