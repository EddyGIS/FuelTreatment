#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Edward Graham
#
# Created:     15/07/2025
# Copyright:   (c) Edward Graham 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

def main():
    pass

if __name__ == '__main__':
    main()

import os
import shutil
import pandas as pd
import piexif
from datetime import datetime
import csv
import math

# Working folder for copies
directory_path = r"C:\Users\Edward Graham\Desktop\TestImages"
os.makedirs(directory_path, exist_ok=True)

# Load your metadata CSV (must reside in TestImages)
csv_path = os.path.join(directory_path, "Test_Photo_Database_Log.csv")
data = pd.read_csv(csv_path, encoding="latin1")

# Logger setup
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_file_path = os.path.join(directory_path, f"logger_{timestamp}.csv")
with open(log_file_path, 'w', newline='', encoding='utf-8') as log_file:
    logger = csv.writer(log_file)
    logger.writerow(["timestamp","original_name","success","message"])

    def deg_to_dms_rational(deg_float):
        deg_abs = abs(deg_float)
        d = int(deg_abs)
        m_float = (deg_abs - d) * 60
        m = int(m_float)
        s_float = (m_float - m) * 60
        s_num = int(round(s_float * 100))
        return ((d,1),(m,1),(s_num,100))

    for _, row in data.iterrows():
        orig = str(row["Original_File_Name"])
        src_folder = str(row["Origin"])
        source_path = os.path.join(src_folder, orig)
        target_path = os.path.join(directory_path, orig)

        # 1) Copy
        if not os.path.isfile(source_path):
            msg = f"Source missing: {source_path}"
            print(f"[!] {msg}")
            logger.writerow([datetime.now().isoformat(), orig, False, msg])
            continue

        try:
            shutil.copy2(source_path, target_path)
        except Exception as e:
            msg = f"Copy failed: {e}"
            print(f"[ERROR] {msg}")
            logger.writerow([datetime.now().isoformat(), orig, False, msg])
            continue

        # 2) Parse coords
        try:
            lat = float(row["Y_coord"])
            lon = float(row["X_coord"])
        except Exception:
            lat = lon = float('nan')

        if math.isnan(lat) or math.isnan(lon):
            msg = "Skipped GPS (missing coords)"
            print(f"[OK] {msg}: {orig}")
            logger.writerow([datetime.now().isoformat(), orig, True, msg])
            continue

        # 3) Load existing EXIF (or init empty)
        try:
            exif = piexif.load(target_path)
        except Exception:
            exif = {"0th":{}, "Exif":{}, "GPS":{}, "1st":{}, "thumbnail":None}

        gps = exif.setdefault("GPS", {})
        lat_ref = b"N" if lat >= 0 else b"S"
        lon_ref = b"E" if lon >= 0 else b"W"
        gps[piexif.GPSIFD.GPSLatitudeRef]  = lat_ref
        gps[piexif.GPSIFD.GPSLatitude]     = deg_to_dms_rational(lat)
        gps[piexif.GPSIFD.GPSLongitudeRef] = lon_ref
        gps[piexif.GPSIFD.GPSLongitude]    = deg_to_dms_rational(lon)
        exif["GPS"] = gps

        # 4) Insert and log
        try:
            piexif.insert(piexif.dump(exif), target_path)
            msg = "GPS inserted"
            print(f"[OK] {msg}: {orig}")
            logger.writerow([datetime.now().isoformat(), orig, True, msg])
        except Exception as e:
            msg = f"GPS write error: {e}"
            print(f"[ERROR] {msg}")
            logger.writerow([datetime.now().isoformat(), orig, False, msg])
