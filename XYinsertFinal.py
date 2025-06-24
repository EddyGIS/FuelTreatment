import os
import shutil
import pandas as pd
import piexif
from datetime import datetime
import csv
import math

# Define the working directory where renamed/copies will be placed
directory_path = r"C:\Users\Edward Graham\Desktop\TestImages"
os.makedirs(directory_path, exist_ok=True)

# Load the photo metadata CSV
csv_path = os.path.join(directory_path, "Test_Photo_Database_Log.csv")
data = pd.read_csv(csv_path, encoding="latin1")  # adjust encoding if needed

# Create a unique logger filename with timestamp
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_filename = f"logger_{timestamp}.csv"
log_file_path = os.path.join(directory_path, log_filename)

# Helper: Convert decimal degrees to EXIF DMS rational format
def deg_to_dms_rational(deg_float):
    deg_abs = abs(deg_float)
    degrees = int(deg_abs)
    minutes_float = (deg_abs - degrees) * 60
    minutes = int(minutes_float)
    seconds_float = (minutes_float - minutes) * 60
    sec_num = int(round(seconds_float * 100))
    sec_den = 100
    return ((degrees, 1), (minutes, 1), (sec_num, sec_den))

with open(log_file_path, mode='w', newline='', encoding='utf-8') as log_file:
    logger = csv.writer(log_file)
    logger.writerow(["timestamp", "original_name", "new_name", "success", "message"])

    for idx, row in data.iterrows():
        orig_name    = str(row["Original_File_Name"])
        origin_folder= str(row["Origin"])
        source_path  = os.path.join(origin_folder, orig_name)

        # Build target filename
        new_raw      = str(row["New_File_Name"])
        new_name     = new_raw if new_raw.lower().endswith(".jpg") else new_raw + ".jpg"
        target_path  = os.path.join(directory_path, new_name)

        # Check source exists
        if not os.path.isfile(source_path):
            msg = f"Source missing: {source_path}"
            print(f"[!] {msg}")
            logger.writerow([datetime.now().isoformat(), orig_name, "", False, msg])
            continue

        # Copy source → working folder
        try:
            shutil.copy2(source_path, target_path)
            print(f"[OK] Copied: {orig_name} → {new_name}")
            logger.writerow([datetime.now().isoformat(), orig_name, new_name, True, "Copied"])
        except Exception as e:
            msg = f"Copy failed: {e}"
            print(f"[ERROR] {msg}")
            logger.writerow([datetime.now().isoformat(), orig_name, "", False, msg])
            continue

        # Parse lat/lon
        lat = row.get("Y_coord", None)
        lon = row.get("X_coord", None)
        try:
            lat = float(lat)
            lon = float(lon)
        except Exception:
            lat = lon = float('nan')

        # If either coordinate is missing (NaN), skip GPS insertion
        if math.isnan(lat) or math.isnan(lon):
            msg = "Skipped GPS (missing coordinates)"
            print(f"[OK] {msg}: {new_name}")
            logger.writerow([datetime.now().isoformat(), orig_name, new_name, True, msg])
            continue

        # Load or init EXIF on the copy
        try:
            exif = piexif.load(target_path)
        except Exception:
            exif = {"0th":{}, "Exif":{}, "GPS":{}, "1st":{}, "thumbnail":None}

        gps_ifd = exif.get("GPS", {})

        # Prepare GPS tags
        lat_ref = "N" if lat >= 0 else "S"
        lon_ref = "E" if lon >= 0 else "W"
        lat_dms = deg_to_dms_rational(lat)
        lon_dms = deg_to_dms_rational(lon)

        # Insert if missing
        try:
            if gps_ifd.get(piexif.GPSIFD.GPSLatitude) is None:
                gps_ifd[piexif.GPSIFD.GPSLatitudeRef]  = lat_ref.encode()
                gps_ifd[piexif.GPSIFD.GPSLatitude]     = lat_dms
                gps_ifd[piexif.GPSIFD.GPSLongitudeRef] = lon_ref.encode()
                gps_ifd[piexif.GPSIFD.GPSLongitude]    = lon_dms
                exif["GPS"] = gps_ifd
                piexif.insert(piexif.dump(exif), target_path)
                msg = "GPS inserted"
            else:
                msg = "GPS already present, skipped"
            print(f"[OK] {msg}: {new_name}")
            logger.writerow([datetime.now().isoformat(), orig_name, new_name, True, msg])
        except Exception as e:
            msg = f"GPS write error: {e}"
            print(f"[ERROR] {msg}")
            logger.writerow([datetime.now().isoformat(), orig_name, new_name, False, msg])
