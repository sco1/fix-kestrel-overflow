import math
import typing as t
from enum import StrEnum, auto
from pathlib import Path

import typer

N_HEADER_LINES = 5
CORRECTED_FILE_SUFFIX = "altitude_corrected"


kestrel_cli = typer.Typer(add_completion=False, no_args_is_help=True)


class FixType(StrEnum):  # noqa: D101
    WET_AIR = auto()
    DRY_AIR = auto()
    OFFSET = auto()


def calc_density_altitude_dry_air(temp_f: float, press_inhg: float) -> float:
    """
    Calculate density altitude from the provided station parameters, assuming dry air.

    See: https://en.wikipedia.org/wiki/Density_altitude#Calculation for more information
    """
    LAPSE = 0.0065  # K/m
    T_SL = 288.15  # K
    P_SL = 29.92  # inHg
    G = 9.80665  # m/s^2x
    M = 0.028964  # kg/mol
    R = 8.3144598  # J/mol·K

    press_ratio = press_inhg / P_SL

    temp_k = (temp_f - 32) * (5 / 9) + 273.15
    temp_ratio = temp_k / T_SL

    k = 1 / ((G * M) / (LAPSE * R) - 1)

    density_alt_dry_air = ((T_SL / LAPSE) * (1 - math.pow((press_ratio / temp_ratio), k))) * 3.28084
    return density_alt_dry_air


def calc_density_altitude_wet_air(temp_f: float, press_inhg: float, dew_point_f: float) -> float:
    """
    Calculate density altitude from the provided station parameters, assuming moistness.

    See: https://www.weather.gov/media/epz/wxcalc/densityAltitude.pdf for more information
    """
    dew_point_c = (dew_point_f - 32) * (5 / 9)
    vapor_press = 6.11 * 10 ** ((7.5 * dew_point_c) / (237.7 + dew_point_c))

    press_mb = press_inhg * 33.8639
    temp_k = (temp_f - 32) * (5 / 9) + 273.15  # F to K
    virtual_temp = temp_k / (1 - (vapor_press / press_mb) * (1 - 0.622))
    virtual_temp *= 1.8  # K to Rankine

    density_alt_wet_air = 145_366 * (1 - math.pow(((17.326 * press_inhg) / virtual_temp), 0.235))
    return density_alt_wet_air


def offset_wrapped_density_altitude(log_data: t.Iterable[str]) -> list[str]:
    """
    Identify location(s) in the provided log data where the density altitude overflows.

    The Kestrel's calculated values appear to overflow and wrap around at approximately 10,600 feet.
    Segment(s) where this wrapping occurs are unwrapped so they return to being more or less
    continuous.

    NOTE: High altitude situations (e.g. above ~21k feet) are assumed to encounter a second overflow
    but are currently not handled by this function.
    """
    raise NotImplementedError


def calculate_log_density_altitudes(log_data: t.Iterable[str], fix_type: FixType) -> list[str]:
    """
    Calculate density altitude from the provided log file data using the specified `fix_type`.

    Log lines are assumed to lead with columns for: timestamp, temperature (F), relative humidity,
    pressure (inHg), heat index, dew point (F) and density altitude. Besides temperature, pressure,
    and dew point all other columns are ignored but output in the same order they are encountered.

    Two density altitude calculation types are provided:
        * `FixType.DRY_AIR`: Calculated assuming dry air & standard atmosphere lapse rates
        * `FixType.WET_AIR`: Calculated including the recorded relative humidity

    NOTE: From the current (relatively limited) experience with the Kestrel's logs, the wet air
    calculation appears to most closely match the Kestrel's internal density altitude calculation.
    Deltas between the two values have been on the order of 10-20 feet, where the delta for dry air
    values are on the order of 100-150 feet.
    """
    out_data = []
    for line in log_data:
        dt, t_f_s, rh, p_inhg_s, hi, dp_f_s, _, *rest = line.split(",")
        temp_f, press_inhg, dew_point_f = (float(n) for n in (t_f_s, p_inhg_s, dp_f_s))

        if fix_type is FixType.DRY_AIR:
            new_density_alt = calc_density_altitude_dry_air(temp_f, press_inhg)
        elif fix_type is FixType.WET_AIR:
            new_density_alt = calc_density_altitude_wet_air(temp_f, press_inhg, dew_point_f)
        else:
            raise ValueError(f"Unknown fix type specified: '{fix_type}'")

        out_data.append(
            ",".join((dt, t_f_s, rh, p_inhg_s, hi, dp_f_s, str(new_density_alt), *rest))
        )

    return out_data


def process_log_file(log_filepath: Path, fix_type: FixType) -> None:
    """
    Correct the density altitude in the provided Kestrel log file using the specified `fix_type`.

    The corrected file is output to a new file with an `"altitude_corrected"` suffix; only the
    density altitude is changed, all other fields are left as-is. Any existing corrected file with
    the same name will be overwritten.
    """
    print(f"Processing: {log_filepath.name} ... ", end="")
    full_log = log_filepath.read_text().splitlines()
    header = full_log[:N_HEADER_LINES]
    log_data = full_log[N_HEADER_LINES:]

    if fix_type is FixType.OFFSET:
        corrected_data = offset_wrapped_density_altitude(log_data)
    elif fix_type in {FixType.WET_AIR, FixType.DRY_AIR}:
        corrected_data = calculate_log_density_altitudes(log_data, fix_type)
    else:
        raise ValueError(f"Unknown fix type specified: '{fix_type}'")

    out_filepath = log_filepath.with_stem(f"{log_filepath.stem}_{CORRECTED_FILE_SUFFIX}")
    header.extend(corrected_data)
    out_filepath.write_text("\n".join(header))
    print("Done!")


@kestrel_cli.command()
def single(
    log_filepath: Path = typer.Option(None, exists=True, dir_okay=False, file_okay=True),
    fix_type: FixType = FixType.WET_AIR,
) -> None:
    """
    Correct the provided Kestrel log file (CSV) using the specified fixing method.

    The corrected file is output to a new file with an `"altitude_corrected"` suffix; only the
    density altitude is changed, all other fields are left as-is. Any existing corrected file with
    the same name will be overwritten.
    """
    process_log_file(log_filepath, fix_type)


@kestrel_cli.command()
def batch(
    log_directory: Path = typer.Option(None, exists=True, dir_okay=True, file_okay=False),
    log_pattern: str = "*.csv",
    fix_type: FixType = FixType.WET_AIR,
) -> None:
    """
    Correct a directory of Kestrel log file(s) (CSV) using the specified fixing method.

    Log file pattern can be optionally specified, note that case sensitivity is deferred to the host
    operating system. Previously corrected files with the default suffix are ignored.

    The corrected file is output to a new file with an `"altitude_corrected"` suffix; only the
    density altitude is changed, all other fields are left as-is. Any existing corrected file with
    the same name will be overwritten.
    """
    for file in log_directory.glob(log_pattern):
        if file.stem.endswith(CORRECTED_FILE_SUFFIX):
            print(f"Skipping: {file.name}")
            continue

        process_log_file(file, fix_type)


if __name__ == "__main__":
    kestrel_cli()
