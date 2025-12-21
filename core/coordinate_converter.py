# Logic for coordinate transformation
def transform_coordinates(coords):
    pass
from pyproj import Transformer, CRS
import math

def convert_to_global(local_points, local_epsg):
    """
    Converts a list of local Cartesian coordinates to global WGS84 (lon, lat).

    Args:
        local_points (list of tuples): A list of (easting, northing) coordinates.
        local_epsg (int): The EPSG code of the local coordinate system (e.g., a UTM zone).

    Returns:
        list of tuples: A list of converted (longitude, latitude) coordinates.
    """
    if not local_points:
        return []

    local_crs = CRS(f"EPSG:{local_epsg}")
    global_crs = CRS("EPSG:4326") # WGS84

    # always_xy=True ensures the output is (longitude, latitude)
    transformer = Transformer.from_crs(local_crs, global_crs, always_xy=True)
    global_points = [transformer.transform(p[0], p[1]) for p in local_points]
    return global_points

def convert_coords(points, from_epsg, to_epsg):
    """
    Converts a list of coordinates from a source EPSG to a target EPSG.

    Args:
        points (list of tuples): A list of (x, y, z) coordinates.
        from_epsg (int): The EPSG code of the source coordinate system.
        to_epsg (int): The EPSG code of the target coordinate system.

    Returns:
        list of tuples: A list of converted (x, y, z) coordinates.
    """
    if not points:
        return []

    from_crs = CRS(f"EPSG:{from_epsg}")
    to_crs = CRS(f"EPSG:{to_epsg}")

    # always_xy=True ensures (lon, lat) or (easting, northing) order
    transformer = Transformer.from_crs(from_crs, to_crs, always_xy=True)

    # Unzip points for transformation
    x_coords, y_coords, z_coords = zip(*points)

    # Perform the transformation
    x_out, y_out, z_out = transformer.transform(x_coords, y_coords, z_coords)

    # Zip them back into a list of tuples
    return list(zip(x_out, y_out, z_out))

def get_utm_epsg_code(longitude):
    """
    Calculates the WGS84 UTM Zone EPSG code for a given longitude.

    Args:
        longitude (float): The longitude in decimal degrees.

    Returns:
        int: The corresponding EPSG code for the WGS84 UTM zone.
    """
    zone_number = math.floor((longitude + 180) / 6) + 1
    # WGS84 UTM zones in the northern hemisphere start from 32601
    return 32600 + zone_number
