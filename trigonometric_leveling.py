import math
from .calculations import dms_to_dd

def calculate_trig_levels(station_elev, hi, observations):
    """
    Calculates elevations based on trigonometric leveling.
    
    Args:
        station_elev (float): Elevation of the instrument station.
        hi (float): Height of Instrument.
        observations (list): List of dicts {'target', 'hd', 'va', 'th', 'type'}
    
    Returns:
        list: Processed observations with calculated 'elevation'.
    """
    results = []

    for obs in observations:
        hd = float(obs['hd'])
        va_val = dms_to_dd(obs['va'])
        th = float(obs['th'])
        
        # Assume Zenith Angle (0 is Up, 90 is Horizon)
        # Alpha (angle from horizon) = 90 - Zenith
        alpha_rad = math.radians(90 - va_val)
        
        # Vertical component V = HD * tan(alpha)
        v_component = hd * math.tan(alpha_rad)
        
        # Curvature and Refraction Correction (approx 0.0675 * k^2)
        k = hd / 1000.0
        cr = 0.0675 * (k**2)
        
        final_elev = station_elev + v_component + hi - th + cr
        
        results.append({**obs, 'elevation': final_elev, 'cr': cr})
        
    return results