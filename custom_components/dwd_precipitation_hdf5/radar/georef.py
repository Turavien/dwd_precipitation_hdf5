"""Minimal RADOLAN grid helper."""

import numpy as np


def get_radolan_coords(lon, lat):
    """Convert lon/lat to RADOLAN projection coordinates."""

    phi_0 = np.radians(60.0)
    phi_m = np.radians(lat)

    lam_0 = 10.0
    lam = np.radians(lon - lam_0)

    er = 6370.040

    m_phi = (
        (1.0 + np.sin(phi_0))
        / (1.0 + np.sin(phi_m))
    )

    x = (
        er
        * m_phi
        * np.cos(phi_m)
        * np.sin(lam)
    )

    y = (
        -er
        * m_phi
        * np.cos(phi_m)
        * np.cos(lam)
    )

    return x, y


def get_radolan_coordinates(
    nrows=1200,
    ncols=1100,
):
    """Return RADOLAN coordinate arrays."""

    j_0 = 470
    i_0 = 600
    res = 1

    x_0, y_0 = get_radolan_coords(
        9.0,
        51.0
    )

    x_arr = np.arange(
        x_0 - j_0,
        x_0 - j_0 + ncols * res,
        res
    )

    y_arr = np.arange(
        y_0 - i_0,
        y_0 - i_0 + nrows * res,
        res
    )

    return x_arr, y_arr


def get_radolan_grid(
    nrows=1200,
    ncols=1100,
    wgs84=True,
):
    """Return RADOLAN grid."""

    x_arr, y_arr = get_radolan_coordinates(
        nrows,
        ncols
    )

    x, y = np.meshgrid(
        x_arr,
        y_arr
    )

    if not wgs84:

        return np.dstack((x, y))

    lon0 = 10.0
    lat0 = 60.0

    sinlat0 = np.sin(
        np.radians(lat0)
    )

    fac = (
        (6370.040 ** 2.0)
        * ((1.0 + sinlat0) ** 2.0)
    )

    lon = (
        np.degrees(np.arctan(-x / y))
        + lon0
    )

    lat = np.degrees(
        np.arcsin(
            (
                fac - (x ** 2.0 + y ** 2.0)
            )
            / (
                fac + (x ** 2.0 + y ** 2.0)
            )
        )
    )

    return np.dstack((lon, lat))
