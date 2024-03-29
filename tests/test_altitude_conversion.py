from textwrap import dedent

import pytest

from fix_kestrel_overflow.main import calc_density_altitude_dry_air, calc_density_altitude_wet_air

DENSITY_ALTITUDE_DRY_CASES = (
    (59, 29.92, 0),
    (70, 29.92, 715.4),
)


@pytest.mark.parametrize(("temp_f", "press_inhg", "truth_altitude"), DENSITY_ALTITUDE_DRY_CASES)
def test_calc_density_altitude_dry(temp_f: float, press_inhg: float, truth_altitude: float) -> None:
    calculated_density_altitude = calc_density_altitude_dry_air(temp_f, press_inhg)
    assert calculated_density_altitude == pytest.approx(truth_altitude, abs=1e-1)


DENSITY_ALTITUDE_WET_CASES = (
    (70, 29.92, 40, 839.8),
    (69.8, 28.16, 39.1, 2874.3),
)


@pytest.mark.parametrize(
    ("temp_f", "press_inhg", "dew_point_f", "truth_altitude"),
    DENSITY_ALTITUDE_WET_CASES,
)
def test_calc_density_altitude_wet(
    temp_f: float, press_inhg: float, dew_point_f: float, truth_altitude: float
) -> None:
    calculated_density_altitude = calc_density_altitude_wet_air(temp_f, press_inhg, dew_point_f)
    assert calculated_density_altitude == pytest.approx(truth_altitude, abs=1e-1)


SAMPLE_LOG = dedent(
    """\
    Device Name,D3 - 2918153
    Device Model,Kestrel DROP 3
    Serial Number,2918153
    FORMATTED DATE_TIME,Temperature,Relative Humidity,Station Pressure,Heat Index,Dew Point,Density Altitude,Data Type,Record name,Start time,Duration (H:M:S),Location description,Location address,Location coordinates,Notes
    yyyy-MM-dd hh:mm:ss a,°F,%,inHg,°F,°F,ft
    2024-04-29 13:37:52,69.8,32.6,28.16,67.3,39.1,2863,point
    2024-04-29 13:37:54,69.9,32.7,28.16,67.3,39.3,2863,point
    2024-04-29 13:37:56,69.9,32.9,28.16,67.3,39.4,2863,point
    2024-04-29 13:37:58,69.8,33.0,28.16,67.3,39.5,2860,point
    2024-04-29 13:38:00,69.8,33.2,28.16,67.1,39.5,2860,point
    """
)

SAMPLE_LOG_LINE = "2024-04-29 13:37:52,69.8,32.6,28.16,67.3,39.1,2863,point"
