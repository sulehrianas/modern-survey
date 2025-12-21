"""Functions to import/export CSV data using pandas."""
import pandas as pd

def import_csv_to_dataframe(file_path):
    """
    Imports data from a CSV file into a pandas DataFrame.

    Args:
        file_path (str): The path to the CSV file.

    Returns:
        pd.DataFrame or None: A DataFrame with the data, or None if an error occurs.
    """
    try:
        return pd.read_csv(file_path)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return None

def export_dataframe_to_csv(df, file_path):
    """
    Exports a pandas DataFrame to a CSV file.

    Args:
        df (pd.DataFrame): The DataFrame to export.
        file_path (str): The path to save the CSV file.
    """
    try:
        df.to_csv(file_path, index=False)
        return True
    except Exception as e:
        print(f"Error exporting to CSV: {e}")
        return False
