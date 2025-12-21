# Logic to generate KML files
def export_to_kml(data, output_path):
    pass
import simplekml

def export_to_kml(output_filename, points):
    """
    Exports a list of coordinates to a KML file.

    Args:
        output_filename (str): Path to save the KML file.
        points (list of tuples): List of (name, longitude, latitude) tuples.
    """
    kml = simplekml.Kml()
    for name, lon, lat in points:
        kml.newpoint(name=name, coords=[(lon, lat)])

    kml.save(output_filename)

# Example Usage:
# # NOTE: KML uses (longitude, latitude) order!
# global_points_for_kml = [
#     ("Point 1", 9.99, 53.55),
#     ("Point 2", 10.0, 53.56)
# ]
# export_to_kml("survey_points.kml", global_points_for_kml)
