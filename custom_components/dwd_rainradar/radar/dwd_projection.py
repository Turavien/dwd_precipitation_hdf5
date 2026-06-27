"""DWD ODIM-H5 stereographic projection."""

import math


_RS_A = 6378137.0
_RS_B = 6356752.3142451802
_RS_E2 = 1 - (_RS_B / _RS_A) ** 2
_RS_E = math.sqrt(_RS_E2)

_RS_LAT_TS = math.radians(60.0)
_RS_LON_0 = 10.0

_sin_lat_ts = math.sin(_RS_LAT_TS)
_cos_lat_ts = math.cos(_RS_LAT_TS)

_RS_M_C = (
    _cos_lat_ts
    / math.sqrt(
        1 - _RS_E2 * _sin_lat_ts ** 2
    )
)

_RS_T_C = (
    math.tan(
        math.pi / 4 - _RS_LAT_TS / 2
    )
    /
    (
        (
            1 - _RS_E * _sin_lat_ts
        )
        /
        (
            1 + _RS_E * _sin_lat_ts
        )
    ) ** (_RS_E / 2)
)

_PROJ_X0 = 543196.83521776402
_PROJ_Y0 = 3622588.8619310022

_LL_LON = 3.5669946350078914
_LL_LAT = 45.696425377390064

_GRID_ROWS = 1200
_GRID_COLS = 1100

_GRID_SIZE = 1000.0


def _lonlat_to_xy(lon, lat):
    """Convert WGS84 coordinates to DWD stereographic."""

    phi = math.radians(lat)
    lam = math.radians(lon - _RS_LON_0)

    sin_phi = math.sin(phi)

    t = (
        math.tan(
            math.pi / 4 - phi / 2
        )
        /
        (
            (
                1 - _RS_E * sin_phi
            )
            /
            (
                1 + _RS_E * sin_phi
            )
        ) ** (_RS_E / 2)
    )

    rho = (
        _RS_A
        * _RS_M_C
        * t
        / _RS_T_C
    )

    return (
        rho * math.sin(lam) + _PROJ_X0,
        -rho * math.cos(lam) + _PROJ_Y0
    )


def get_dwd_grid_index(lat, lon):
    """Return DWD ODIM-H5 grid index."""

    x_ll, y_ll = _lonlat_to_xy(
        _LL_LON,
        _LL_LAT
    )

    x_pt, y_pt = _lonlat_to_xy(
        lon,
        lat
    )

    col = int(
        round(
            (x_pt - x_ll)
            / _GRID_SIZE
        )
    )

    row = int(
        _GRID_ROWS
        - 1
        - round(
            (y_pt - y_ll)
            / _GRID_SIZE
        )
    )

    if (
        row < 0
        or row >= _GRID_ROWS
        or col < 0
        or col >= _GRID_COLS
    ):
        raise ValueError(
            f"Coordinates outside DWD grid: "
            f"lat={lat}, lon={lon}"
        )

    return row, col
