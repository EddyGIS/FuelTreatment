#-------------------------------------------------------------------------------
# Name:
# Purpose:
#
# Author:      Edward Graham
#
# Created:     27/06/2025
# Copyright:   (c) Edward Graham 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import os
import datetime
import pandas as pd
import piexif

# 1. Paths - New users will need to update paths accoringly
input_csv = r"C:\Users\Edward Graham\Desktop\Database_import_EXIF.csv"
images_root = r"C:\GIS\Fuels_Photo_Database\Pictures"

# 2. Read the original CSV (preserve all columns)
df = pd.read_csv(input_csv)

# 3. Ensure X_coord / Y_coord exist
for coord in ("X_coord", "Y_coord"):
    if coord not in df.columns:
        df[coord] = pd.NA

# 4. Build filename → full path lookup (normalize to lowercase)
name_to_path = {}
for root, _, files in os.walk(images_root):
    for file in files:
        lower = file.lower()
        if lower.endswith(('.jpg', '.jpeg')):
            name_to_path[lower] = os.path.join(root, file)

# 5. EXIF extraction helper using piexif
def get_exif_data(img_path):
    try:
        exif_dict = piexif.load(img_path)
        gps_ifd = exif_dict.get("GPS", {})

        lat_tag = piexif.GPSIFD.GPSLatitude
        lon_tag = piexif.GPSIFD.GPSLongitude
        lat_ref_tag = piexif.GPSIFD.GPSLatitudeRef
        lon_ref_tag = piexif.GPSIFD.GPSLongitudeRef

        if lat_tag in gps_ifd and lon_tag in gps_ifd:
            def to_deg(rational, ref):
                d, m, s = rational
                deg = d[0]/d[1] + (m[0]/m[1])/60 + (s[0]/s[1])/3600
                return -deg if ref in (b'S', b'W') else deg

            lat = to_deg(gps_ifd[lat_tag], gps_ifd.get(lat_ref_tag, b'N'))
            lon = to_deg(gps_ifd[lon_tag], gps_ifd.get(lon_ref_tag, b'E'))
            return lat, lon
    except Exception:
        pass
    return None, None

# 6. Fill missing coords in the original DataFrame
for idx, row in df.iterrows():
    if pd.notna(row["X_coord"]) and pd.notna(row["Y_coord"]):
        continue
    img_file = str(row["Original_File_Name"]).lower()
    img_path = name_to_path.get(img_file)
    if not img_path:
        continue
    lat, lon = get_exif_data(img_path)
    if lat is not None:
        df.at[idx, "X_coord"] = lon
        df.at[idx, "Y_coord"] = lat

# 7. Identify images *not* in the CSV
existing_names = set(name.lower() for name in df["Original_File_Name"])
missing_names = set(name_to_path.keys()) - existing_names

# 8. Build “Consider_Include” DataFrame with same columns as df
rows = []
for fname in missing_names:
    full_path = name_to_path[fname]
    rel_folder = os.path.relpath(os.path.dirname(full_path), images_root)
    lat, lon = get_exif_data(full_path)
    row = {col: pd.NA for col in df.columns}
    row["Unique_ID"] = pd.NA
    row["Origin"] = rel_folder
    row["Original_File_Name"] = fname
    row["X_coord"] = lon
    row["Y_coord"] = lat
    rows.append(row)
consider_df = pd.DataFrame(rows, columns=df.columns)

# 9. Write out both CSVs to Desktop\Analysis with timestamps - New users will need to create an output location
ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
out_base = r"C:\Users\Edward Graham\Desktop\Analysis"
os.makedirs(out_base, exist_ok=True)

main_csv = os.path.join(out_base, f"Database_import_EXIF_completed_{ts}.csv")
consider_csv = os.path.join(out_base, f"Consider_Include_{ts}.csv")

df.to_csv(main_csv, index=False)
consider_df.to_csv(consider_csv, index=False)

print(f"Main CSV written to: {main_csv}")
print(f"Consider_Include CSV written to: {consider_csv}")
