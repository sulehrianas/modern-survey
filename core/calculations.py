"""Core surveying calculation functions"""
import numpy as np

def dms_to_dd(dms_str):
    """
    Converts an angle string in DD.MMSS format to decimal degrees.
    Example: "123.4530" -> 123 degrees, 45 minutes, 30 seconds.
    """
    try:
        dms_str = str(dms_str)
        # If it doesn't contain a '.', it's likely already decimal or a simple integer.
        if '.' not in dms_str:
            return float(dms_str)
            
        parts = dms_str.split('.')
        degrees = float(parts[0])
        fractional_part = parts[1]

        # Ensure fractional part is padded to handle M or S correctly if needed
        if len(fractional_part) >= 4: # Indicates at least MMSS format
            minutes = float(fractional_part[:2])
            seconds = float(fractional_part[2:4]) # Only take the first two for seconds
            return degrees + (minutes / 60.0) + (seconds / 3600.0)
        return float(dms_str) # It's already a decimal
    except (ValueError, IndexError, TypeError):
        return None

def dd_to_dms(dd):
    """
    Converts decimal degrees to a DD.MMSS string.

    Args:
        dd (float): The angle in decimal degrees.

    Returns:
        str: The angle in DD.MMSS format.
    """
    is_negative = dd < 0
    dd = abs(dd)
    degrees = int(dd)
    minutes_float = (dd - degrees) * 60
    minutes = int(minutes_float)
    seconds = round((minutes_float - minutes) * 60)

    # Handle cases where seconds round up to 60
    if seconds == 60:
        minutes += 1
        seconds = 0
    if minutes == 60:
        degrees += 1
        minutes = 0

    sign = "-" if is_negative else ""
    return f"{sign}{degrees:02d}.{minutes:02d}{seconds:02d}"

def calculate_lat_dep(azimuths, distances, angle_format='dd'):
    """
    Calculates the latitude and departure for each traverse leg.

    Args:
        azimuths (list): A list of azimuths.
        distances (list): A list of distances.
        angle_format (str): The format of the input azimuths ('dd' for decimal
                            degrees or 'dms' for DD.MMSS string format).

    Returns:
        tuple: A tuple containing (list of latitudes, list of departures).
    """
    azimuths_dd = azimuths
    if angle_format == 'dms':
        azimuths_dd = [dms_to_dd(az) for az in azimuths]

    # Convert azimuths from decimal degrees to radians for numpy trigonometric functions
    azimuths_rad = np.deg2rad(azimuths_dd)

    # Ensure distances is a numpy array for element-wise multiplication
    distances = np.array(distances)

    # Latitude = Distance * cos(Azimuth)
    latitudes = distances * np.cos(azimuths_rad)

    # Departure = Distance * sin(Azimuth)
    departures = distances * np.sin(azimuths_rad)

    return latitudes.tolist(), departures.tolist()

def calculate_coordinates(start_northing, start_easting, adj_latitudes, adj_departures):
    """Calculates final coordinates from adjusted latitudes and departures."""
    coords = [(start_easting, start_northing)]
    for i in range(len(adj_latitudes)):
        next_easting = coords[-1][0] + adj_departures[i]
        next_northing = coords[-1][1] + adj_latitudes[i]
        coords.append((next_easting, next_northing))
    return coords
