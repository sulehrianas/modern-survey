import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math

# Try to import folium for maps
try:
    import folium
    from streamlit_folium import st_folium
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False

# --- Import Core Logic ---
try:
    from core.calculations import dms_to_dd, dd_to_dms, calculate_lat_dep, calculate_coordinates
    from core.adjustments import adjust_traverse_bowditch
    from core.coordinate_converter import convert_to_global, convert_coords
    from core.trigonometric_leveling import calculate_trig_levels
    from core.triangulation import calculate_simple_triangulation
except ImportError as e:
    st.error(f"Could not import core modules: {e}")
    st.info("Please ensure 'streamlit_app.py' is in the root directory of your project.")
    st.stop()

st.set_page_config(page_title="Modern Survey", layout="wide", page_icon="📐")
st.title("📐 Modern Survey System (Web)")

# --- Tabs ---
tabs = st.tabs([
    "Compass Traverse", 
    "Theodolite Survey", 
    "Diff. Leveling", 
    "Trig. Leveling", 
    "Triangulation", 
    "GPS / Conversion"
])

# ==========================================
# TAB 1: COMPASS TRAVERSING
# ==========================================
with tabs[0]:
    st.header("Compass Traversing")
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("Setup")
        comp_start_n = st.number_input("Start Northing", value=1000.0, key="comp_n")
        comp_start_e = st.number_input("Start Easting", value=5000.0, key="comp_e")
        comp_fmt = st.selectbox("Angle Format", ["Azimuth (DD.MMSS)", "Azimuth (Decimal)"], key="comp_fmt")
        comp_epsg = st.number_input("EPSG Code (Map)", value=32632, step=1, key="comp_epsg")
    
    with c2:
        if "compass_data" not in st.session_state:
            st.session_state.compass_data = pd.DataFrame(
                [{"Line": "1-2", "Azimuth": "45.0000", "Distance": 100.0}],
                columns=["Line", "Azimuth", "Distance"]
            )
        comp_df = st.data_editor(st.session_state.compass_data, num_rows="dynamic", use_container_width=True)

    if st.button("Calculate Compass Traverse"):
        try:
            lines = comp_df["Line"].tolist()
            raw_az = comp_df["Azimuth"].astype(str).tolist()
            dists = comp_df["Distance"].astype(float).values
            
            if len(dists) > 0:
                # Convert Angles
                if "DD.MMSS" in comp_fmt:
                    bearings = np.array([dms_to_dd(b) for b in raw_az])
                else:
                    bearings = np.array([float(b) for b in raw_az])
                
                # Calculate
                lats, deps = calculate_lat_dep(bearings, dists)
                adj_lat, adj_dep, _, _ = adjust_traverse_bowditch(dists, lats, deps)
                coords = calculate_coordinates(comp_start_n, comp_start_e, adj_lat, adj_dep)
                
                # Results
                res_data = []
                for i in range(len(lines)):
                    res_data.append({
                        "Line": lines[i], "Lat": lats[i], "Dep": deps[i],
                        "Adj N": coords[i+1][1], "Adj E": coords[i+1][0]
                    })
                st.dataframe(pd.DataFrame(res_data).style.format("{:.4f}"))
                
                # Plot
                fig, ax = plt.subplots()
                es, ns = zip(*coords)
                ax.plot(es, ns, 'b-o')
                for i, (e, n) in enumerate(coords):
                    ax.text(e, n, f" P{i}")
                ax.set_aspect('equal')
                ax.grid(True)
                st.pyplot(fig)
        except Exception as e:
            st.error(f"Error: {e}")

# ==========================================
# TAB 2: THEODOLITE SURVEYING
# ==========================================
with tabs[1]:
    st.header("Theodolite Surveying")
    t1, t2 = st.columns([1, 2])
    with t1:
        theo_start_n = st.number_input("Start N", value=1000.0, key="theo_n")
        theo_start_e = st.number_input("Start E", value=5000.0, key="theo_e")
        theo_init_az = st.text_input("Initial Azimuth (DD.MMSS)", value="0.0000")
        theo_k = st.number_input("Stadia Constant (k)", value=100.0)
        theo_angle_type = st.selectbox("Angle Type", ["Interior (Right)", "Exterior"], key="theo_type")

    with t2:
        if "theo_data" not in st.session_state:
            st.session_state.theo_data = pd.DataFrame(
                [{"Line": "1-2", "Angle": "90.0000", "Upper": 1.5, "Lower": 0.5, "V.Angle": "0.0"}],
                columns=["Line", "Angle", "Upper", "Lower", "V.Angle"]
            )
        theo_df = st.data_editor(st.session_state.theo_data, num_rows="dynamic", use_container_width=True)

    if st.button("Calculate Theodolite"):
        try:
            # Parse Data
            rows = theo_df.to_dict('records')
            if not rows: st.stop()
            
            # Initial Azimuth
            curr_az = dms_to_dd(theo_init_az)
            
            results = []
            coords = [(theo_start_e, theo_start_n)]
            
            for row in rows:
                # 1. Distance from Stadia
                u, l = float(row['Upper']), float(row['Lower'])
                va_dms = str(row['V.Angle'])
                va = dms_to_dd(va_dms)
                dist = theo_k * (u - l) * (math.cos(math.radians(va))**2)
                
                # 2. Azimuth
                angle_dms = str(row['Angle'])
                angle = dms_to_dd(angle_dms)
                
                back_az = (curr_az + 180) % 360
                if "Interior" in theo_angle_type:
                    next_az = (back_az + angle) % 360
                else:
                    next_az = (back_az - angle) % 360
                
                curr_az = next_az
                
                # 3. Coords
                lat = dist * math.cos(math.radians(curr_az))
                dep = dist * math.sin(math.radians(curr_az))
                
                prev_e, prev_n = coords[-1]
                new_e = prev_e + dep
                new_n = prev_n + lat
                coords.append((new_e, new_n))
                
                results.append({
                    "Line": row['Line'], "Dist": dist, "Azimuth": dd_to_dms(curr_az),
                    "Lat": lat, "Dep": dep, "N": new_n, "E": new_e
                })
            
            st.dataframe(pd.DataFrame(results).style.format({"Dist": "{:.3f}", "Lat": "{:.3f}", "Dep": "{:.3f}", "N": "{:.3f}", "E": "{:.3f}"}))
            
            # Plot
            fig, ax = plt.subplots()
            es, ns = zip(*coords)
            ax.plot(es, ns, 'r-^')
            for i, (e, n) in enumerate(coords):
                ax.text(e, n, f" ST{i}")
            ax.set_aspect('equal')
            ax.grid(True)
            st.pyplot(fig)
            
        except Exception as e:
            st.error(f"Calculation Error: {e}")

# ==========================================
# TAB 3: DIFFERENTIAL LEVELING
# ==========================================
with tabs[2]:
    st.header("Differential Leveling")
    start_bm = st.number_input("Start BM Elevation", value=100.0)
    
    if "level_data" not in st.session_state:
        st.session_state.level_data = pd.DataFrame(
            [{"Station": "BM1", "BS": 1.5, "FS": 0.0}, {"Station": "TP1", "BS": 0.0, "FS": 1.2}],
            columns=["Station", "BS", "FS"]
        )
    lev_df = st.data_editor(st.session_state.level_data, num_rows="dynamic", use_container_width=True)
    
    if st.button("Calculate Levels"):
        try:
            rows = lev_df.to_dict('records')
            if rows:
                rows[0]['Elevation'] = start_bm
                rows[0]['HI'] = 0.0
                
                curr_hi = 0.0
                total_bs, total_fs = 0.0, 0.0
                
                for i, row in enumerate(rows):
                    bs = float(row.get('BS', 0) or 0)
                    fs = float(row.get('FS', 0) or 0)
                    
                    if 'Elevation' in row:
                        if bs > 0:
                            curr_hi = row['Elevation'] + bs
                            row['HI'] = curr_hi
                            total_bs += bs
                    
                    if fs > 0 and i + 1 < len(rows):
                        if row.get('HI', 0) == 0 and i > 0:
                            curr_hi = rows[i-1]['HI']
                            row['HI'] = curr_hi
                        
                        next_elev = curr_hi - fs
                        rows[i+1]['Elevation'] = next_elev
                        total_fs += fs
                
                res_df = pd.DataFrame(rows)
                st.dataframe(res_df[["Station", "BS", "HI", "FS", "Elevation"]].style.format("{:.4f}"))
                
                check = start_bm + total_bs - total_fs
                end_elev = rows[-1].get('Elevation', 0)
                st.success(f"Check: {check:.4f} | End Elev: {end_elev:.4f} | Misclosure: {check - end_elev:.4f}")
        except Exception as e:
            st.error(f"Error: {e}")

# ==========================================
# TAB 4: TRIGONOMETRIC LEVELING
# ==========================================
with tabs[3]:
    st.header("Trigonometric Leveling")
    c1, c2 = st.columns(2)
    with c1:
        trig_stn_elev = st.number_input("Station Elev", value=100.0)
        trig_hi = st.number_input("Instrument Height (HI)", value=1.5)
    
    if "trig_data" not in st.session_state:
        st.session_state.trig_data = pd.DataFrame(
            [{"Target": "T1", "HD": 50.0, "VA (DD.MMSS)": "0.0000", "TH": 1.5}],
            columns=["Target", "HD", "VA (DD.MMSS)", "TH"]
        )
    trig_df = st.data_editor(st.session_state.trig_data, num_rows="dynamic", use_container_width=True)
    
    if st.button("Calculate Trig Levels"):
        try:
            obs_list = []
            for _, row in trig_df.iterrows():
                obs_list.append({
                    'target': row['Target'],
                    'hd': row['HD'],
                    'va': row['VA (DD.MMSS)'],
                    'th': row['TH']
                })
            
            results = calculate_trig_levels(trig_stn_elev, trig_hi, obs_list)
            
            res_data = [{"Target": r['target'], "Elevation": r['elevation'], "Correction": r['cr']} for r in results]
            st.dataframe(pd.DataFrame(res_data).style.format("{:.4f}"))
        except Exception as e:
            st.error(f"Error: {e}")

# ==========================================
# TAB 5: TRIANGULATION
# ==========================================
with tabs[4]:
    st.header("Simple Triangulation")
    c1, c2 = st.columns(2)
    with c1:
        tri_start_e = st.number_input("Start E", value=1000.0, key="tri_e")
        tri_start_n = st.number_input("Start N", value=1000.0, key="tri_n")
    with c2:
        tri_base_dist = st.number_input("Base Dist", value=100.0)
        tri_base_az = st.text_input("Base Azimuth (DD.MMSS)", value="90.0000")
    
    if "tri_data" not in st.session_state:
        st.session_state.tri_data = pd.DataFrame(
            [{"P1": "A", "P2": "B", "P3": "C", "A1": "60.0000", "A2": "60.0000", "A3": "60.0000", "Dir": "Left"}],
            columns=["P1", "P2", "P3", "A1", "A2", "A3", "Dir"]
        )
    
    tri_df = st.data_editor(
        st.session_state.tri_data, 
        num_rows="dynamic", 
        use_container_width=True,
        column_config={
            "Dir": st.column_config.SelectboxColumn("Dir", options=["Left", "Right"])
        }
    )
    
    if st.button("Calculate Network"):
        try:
            triangles = []
            for _, row in tri_df.iterrows():
                triangles.append({
                    'p1': row['P1'], 'p2': row['P2'], 'p3': row['P3'],
                    'a1': str(row['A1']), 'a2': str(row['A2']), 'a3': str(row['A3']),
                    'dir': row['Dir']
                })
            
            stations, results = calculate_simple_triangulation(tri_start_e, tri_start_n, tri_base_dist, tri_base_az, triangles)
            
            st.subheader("Station Coordinates")
            st_data = [{"Station": k, "Easting": v[0], "Northing": v[1]} for k, v in stations.items()]
            st.dataframe(pd.DataFrame(st_data).style.format("{:.3f}"))
            
            st.subheader("Triangle Closures")
            res_data = [{"Triangle": r['triangle'], "Error (sec)": r['error'], "Base": r['dist_base']} for r in results]
            st.dataframe(pd.DataFrame(res_data))
            
            # Plot
            fig, ax = plt.subplots()
            for k, v in stations.items():
                ax.plot(v[0], v[1], 'ro')
                ax.text(v[0], v[1], f" {k}")
            
            # Draw lines (simplified)
            pts = list(stations.values())
            if len(pts) > 1:
                # Draw base
                ax.plot([pts[0][0], pts[1][0]], [pts[0][1], pts[1][1]], 'k-')
                # Draw others roughly
                for tri in triangles:
                    if tri['p1'] in stations and tri['p3'] in stations:
                        p1, p3 = stations[tri['p1']], stations[tri['p3']]
                        ax.plot([p1[0], p3[0]], [p1[1], p3[1]], 'b--')
                    if tri['p2'] in stations and tri['p3'] in stations:
                        p2, p3 = stations[tri['p2']], stations[tri['p3']]
                        ax.plot([p2[0], p3[0]], [p2[1], p3[1]], 'b--')

            ax.set_aspect('equal')
            ax.grid(True)
            st.pyplot(fig)
            
        except Exception as e:
            st.error(f"Error: {e}")

# ==========================================
# TAB 6: GPS / CONVERSION
# ==========================================
with tabs[5]:
    st.header("Coordinate Conversion")
    c1, c2 = st.columns(2)
    with c1:
        from_epsg = st.number_input("From EPSG", value=4326, step=1)
    with c2:
        to_epsg = st.number_input("To EPSG", value=32632, step=1)
        
    if "gps_data" not in st.session_state:
        st.session_state.gps_data = pd.DataFrame(
            [{"Name": "P1", "X/Lon": 12.4924, "Y/Lat": 41.8902, "Z": 50.0}],
            columns=["Name", "X/Lon", "Y/Lat", "Z"]
        )
        
    gps_df = st.data_editor(st.session_state.gps_data, num_rows="dynamic")
    
    if st.button("Convert Coords"):
        try:
            points = []
            for _, row in gps_df.iterrows():
                points.append((float(row["X/Lon"]), float(row["Y/Lat"]), float(row["Z"])))
            
            converted = convert_coords(points, from_epsg, to_epsg)
            
            res_df = gps_df.copy()
            res_df["Out X"] = [c[0] for c in converted]
            res_df["Out Y"] = [c[1] for c in converted]
            res_df["Out Z"] = [c[2] for c in converted]
            
            st.dataframe(res_df)
            
            # Map Preview (if converting to WGS84 or if input is WGS84)
            map_points = []
            if from_epsg == 4326:
                map_points = [(p[1], p[0]) for p in points] # Lat, Lon
            elif to_epsg == 4326:
                map_points = [(c[1], c[0]) for c in converted]
            
            if map_points and FOLIUM_AVAILABLE:
                st.subheader("Map Preview")
                avg_lat = sum(p[0] for p in map_points)/len(map_points)
                avg_lon = sum(p[1] for p in map_points)/len(map_points)
                m = folium.Map(location=[avg_lat, avg_lon], zoom_start=15)
                for i, mp in enumerate(map_points):
                    folium.Marker(mp, popup=f"P{i}").add_to(m)
                st_folium(m, height=400, use_container_width=True)
                
        except Exception as e:
            st.error(f"Conversion Error: {e}")