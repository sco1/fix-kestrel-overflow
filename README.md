# fix-kestrel-overflow
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Code style: black](https://img.shields.io/badge/code%20style-black-black)](https://github.com/psf/black)

Fix overflowing density altitude for the [Kestrel DROP D3](https://kestrelinstruments.com/data-loggers/kestrel-drop-d3-wireless-temperature-humidity-pressure-data-logger)

## So What's The Issue?
![wraparound](./doc/wraparound.png)
The density altitudes calculated by the device appear to overflow & wrap around somewhere near 10,600 feet, with no apparent discrepencies in any of the other measurements this value is derived from.

## Ok, What's The Fix?
### Offset
...

### Recalculate
...

## CLI Interface
### `fixkestrel single`
Process a single Kestrel log file.
#### Input Parameters
| Parameter        | Description                    | Type         | Default    |
|------------------|--------------------------------|--------------|------------|
| `--log-filepath` | Path to Kestrel log to parse.  | `Path\|None` | GUI Prompt |
| `--fix-type`     | Log fixing method.<sup>1</sup> | `str`        | `...`      |

### `fixkestrel batch`
Process a directory of Kestrel log file(s).
#### Input Parameters
| Parameter    | Description                             | Type         | Default    |
|--------------|-----------------------------------------|--------------|------------|
| `--log-path` | Path to Kestrel log directory to parse. | `Path\|None` | GUI Prompt |
| `--fix-type` | Log fixing method.<sup>1</sup>          | `str`        | `...`      |
