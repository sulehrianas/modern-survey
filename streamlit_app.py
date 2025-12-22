import streamlit as st
import pandas as pd
import sys
import os
import math
import numpy as np

# Ensure we can import from the core folder
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from core.trigonometric_leveling import calculate_trig_levels
from core.triangulation import calculate_simple_triangulation
from core.calculations import dms_to_dd, dd_to_dms, calculate_lat_dep, calculate_coordinates
from core.adjustments import adjust_traverse_bowditch
from core.coordinate_converter import convert_coords, get_utm_epsg_code

# --- Page Config ---
st.set_page_config(page_title="Modern Survey Web", layout="wide")

st.title("Modern Survey - Web Edition")
st.markdown("Perform survey calculations directly in your browser.")

# --- Tabs ---
tab_compass, tab_level, tab_trig, tab_tri, tab_conv = st.tabs([
    "Compass Traversing", 
    "Differential Leveling", 
    "Trigonometric Leveling", 
    "Triangulation", 
    "Coordinate Conversion"
])

# ==========================================
# 1. COMPASS TRAVERSING TAB
# ==========================================
with tab_compass:
    st.header("Compass Traversing")
    
    c_col1, c_col2 = st.columns(2)
    with c_col1:
        start_e = st.number_input("Start Easting", value=5000.0, format="%.3f")
    with c_col2:
        start_n = st.number_input("Start Northing", value=1000.0, format="%.3f")

    st.subheader("Traverse Data")
    
    # Initial Data
    trav_data = {
        "Station": ["A", "B", "C", "D"],
        "Distance (m)": [100.0, 150.0, 120.0, 130.0],
        "Azimuth (DD.MMSS)": ["45.0000", "135.0000", "225.0000", "315.0000"]
    }
    trav_df = st.data_editor(pd.DataFrame(trav_data), num_rows="dynamic", use_container_width=True, key="trav_editor")

    if st.button("Calculate Traverse"):
        try:
            dists = trav_df["Distance (m)"].astype(float).tolist()
            az_strs = trav_df["Azimuth (DD.MMSS)"].astype(str).tolist()
            
            # 1. Calculate Lat/Dep
            lats, deps = calculate_lat_dep(az_strs, dists, angle_format='dms')
            
            # 2. Adjust (Bowditch)
            adj_lats, adj_deps, corr_lat, corr_dep = adjust_traverse_bowditch(dists, lats, deps)
            
            # 3. Calculate Coordinates
            coords = calculate_coordinates(start_n, start_e, adj_lats, adj_deps)
            
            # Display Results
            res_data = []
            for i, (e, n) in enumerate(coords):
                stn = trav_df.iloc[i]["Station"] if i < len(trav_df) else f"End"
                # For the start point, we just show it. For subsequent points, they correspond to leg i-1
                res_data.append({"Station": stn, "Easting": e, "Northing": n})
            
            # Handle the final point which is the result of the last leg
            if len(coords) > len(trav_df):
                 res_data[-1]["Station"] = "End/Close"

            st.success("Traverse Calculated Successfully")
            st.dataframe(pd.DataFrame(res_data), use_container_width=True)
            
            # Misclosure Info
            mis_lat = sum(lats)
            mis_dep = sum(deps)
            mis_closure = math.sqrt(mis_lat**2 + mis_dep**2)
            st.info(f"Linear Misclosure: {mis_closure:.4f} m")

        except Exception as e:
            st.error(f"Error: {e}")

# ==========================================
# 2. DIFFERENTIAL LEVELING TAB
# ==========================================
with tab_level:
    st.header("Differential Leveling")
    
    start_bm = st.number_input("Starting Benchmark Elevation (m)", value=100.0, format="%.4f")
    
    level_data = {
        "Station": ["BM1", "TP1", "TP2", "BM2"],
        "Backsight (BS)": [1.500, 1.200, 1.100, 0.0],
        "Foresight (FS)": [0.0, 1.400, 1.300, 1.600]
    }
    level_df = st.data_editor(pd.DataFrame(level_data), num_rows="dynamic", use_container_width=True, key="level_editor")

    if st.button("Calculate Levels"):
        results = []
        current_elev = start_bm
        current_hi = 0.0
        
        # Logic adapted from ui/leveling_tab.py
        # We iterate through the dataframe rows
        for idx, row in level_df.iterrows():
            bs = float(row["Backsight (BS)"])
            fs = float(row["Foresight (FS)"])
            stn = str(row["Station"])
            
            # If it's the first row or a row with BS, we calculate HI based on current elevation
            # Note: In standard leveling table, HI is on the line of the BS.
            # Elevation is established by Previous HI - Current FS.
            
            # 1. Establish Elevation of this point
            if idx == 0:
                this_elev = start_bm
            else:
                # Elevation = Previous HI - This FS
                # We need the HI from the *previous* row logic
                this_elev = current_hi - fs
            
            # 2. Establish HI for this setup (if there is a BS)
            if bs != 0:
                current_hi = this_elev + bs
                hi_display = f"{current_hi:.4f}"
            else:
                hi_display = "-" # End of run usually
            
            results.append({
                "Station": stn,
                "Backsight": bs,
                "Foresight": fs,
                "HI": hi_display,
                "Elevation": this_elev
            })
            
            # Update current_elev for next iteration logic if needed, 
            # though we used current_hi which persists.
            current_elev = this_elev

        st.dataframe(pd.DataFrame(results).style.format({"Elevation": "{:.4f}", "Backsight": "{:.3f}", "Foresight": "{:.3f}"}), use_container_width=True)

# ==========================================
# 3. TRIGONOMETRIC LEVELING TAB
# ==========================================
with tab_trig:
    st.header("Trigonometric Leveling")
    
    col1, col2 = st.columns(2)
    with col1:
        stn_elev = st.number_input("Station Elevation (m)", value=100.0, step=0.001, format="%.3f")
    with col2:
        hi = st.number_input("Instrument Height (HI) (m)", value=1.500, step=0.001, format="%.3f")

    st.subheader("Observations")
    st.info("Enter your observations below. VA should be in DD.MMSS format (Zenith).")

    # Create a template DataFrame for the editor
    data = {
        "target": ["T1", "T2", "T3"],
        "hd": [10.5, 20.0, 15.0],
        "va": ["90.0000", "85.3000", "92.1500"],
        "th": [1.5, 1.5, 1.5]
    }
    df = pd.DataFrame(data)

    # Editable Data Table
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)

    if st.button("Calculate Elevations", type="primary"):
        # Prepare data for the core function
        obs_list = []
        for index, row in edited_df.iterrows():
            obs_list.append({
                'target': str(row['target']),
                'hd': float(row['hd']),
                'va': str(row['va']),
                'th': float(row['th']),
                'type': 'Zenith' # Defaulting to Zenith for web simplicity
            })
        
        # Call your existing core logic
        try:
            results = calculate_trig_levels(stn_elev, hi, obs_list)
            
            # Display Results
            res_df = pd.DataFrame(results)
            # Select and rename columns for display
            display_df = res_df[['target', 'elevation', 'cr']].rename(columns={'elevation': 'Final Elevation', 'cr': 'C&R Correction'})
            st.success("Calculation Complete!")
            st.dataframe(display_df, use_container_width=True)
            
        except Exception as e:
            st.error(f"An error occurred: {e}")

# ==========================================
# 4. TRIANGULATION TAB
# ==========================================
with tab_tri:
    st.header("Triangulation (Simple Chain)")
    
    t_col1, t_col2, t_col3, t_col4 = st.columns(4)
    with t_col1: tri_start_e = st.number_input("Start E", value=1000.0)
    with t_col2: tri_start_n = st.number_input("Start N", value=1000.0)
    with t_col3: tri_base_dist = st.number_input("Base Dist", value=100.0)
    with t_col4: tri_base_az = st.text_input("Base Az (DMS)", value="90.0000")

    tri_data = {
        "P1": ["A"], "P2": ["B"], "P3": ["C"],
        "Angle 1 (DMS)": ["60.0000"], "Angle 2 (DMS)": ["60.0000"], "Angle 3 (DMS)": ["60.0000"],
        "Direction": ["Left"]
    }
    tri_df = st.data_editor(pd.DataFrame(tri_data), num_rows="dynamic", use_container_width=True, key="tri_editor")

    if st.button("Calculate Triangulation"):
        triangles = []
        for _, row in tri_df.iterrows():
            triangles.append({
                'p1': str(row['P1']), 'p2': str(row['P2']), 'p3': str(row['P3']),
                'a1': str(row['Angle 1 (DMS)']), 'a2': str(row['Angle 2 (DMS)']), 'a3': str(row['Angle 3 (DMS)']),
                'dir': str(row['Direction'])
            })
        
        try:
            stations, results = calculate_simple_triangulation(tri_start_e, tri_start_n, tri_base_dist, tri_base_az, triangles)
            
            st.subheader("Station Coordinates")
            stn_data = [{"Station": k, "Easting": v[0], "Northing": v[1]} for k, v in stations.items()]
            st.dataframe(pd.DataFrame(stn_data), use_container_width=True)
            
            st.subheader("Triangle Details")
            st.dataframe(pd.DataFrame(results), use_container_width=True)
            
        except Exception as e:
            st.error(f"Error: {e}")

# ==========================================
# 5. COORDINATE CONVERSION TAB
# ==========================================
with tab_conv:
    st.header("Coordinate Conversion")
    
    cc_col1, cc_col2 = st.columns(2)
    with cc_col1:
        from_epsg = st.number_input("Source EPSG (e.g., 4326 for WGS84)", value=4326, step=1)
    with cc_col2:
        to_epsg = st.number_input("Target EPSG (e.g., 32632 for UTM)", value=32632, step=1)
        
    st.info("Tip: Use EPSG 4326 for Lat/Lon and 326xx for UTM North (where xx is zone).")

    conv_data = {
        "X / Lon": [12.4924],
        "Y / Lat": [41.8902],
        "Z / Elev": [0.0]
    }
    conv_df = st.data_editor(pd.DataFrame(conv_data), num_rows="dynamic", use_container_width=True, key="conv_editor")

    if st.button("Convert Coordinates"):
        points = []
        for _, row in conv_df.iterrows():
            points.append((float(row["X / Lon"]), float(row["Y / Lat"]), float(row["Z / Elev"])))
        
        try:
            converted = convert_coords(points, int(from_epsg), int(to_epsg))
            res_conv = [{"X_out": c[0], "Y_out": c[1], "Z_out": c[2]} for c in converted]
            st.dataframe(pd.DataFrame(res_conv), use_container_width=True)
        except Exception as e:
            st.error(f"Conversion Error: {e}")