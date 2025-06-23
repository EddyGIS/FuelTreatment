import os
import pandas as pd
import piexif
from PIL import Image
from datetime import datetime
import csv

# Define the working directory containing images and CSV
directory_path = r"C:\Users\Edward Graham\Desktop\TestImages"
os.chdir(directory_path)

# Load the photo metadata CSV
csv_path = os.path.join(directory_path, "Test_Photo_Database_Log.csv")
data = pd.read_csv(csv_path, encoding="latin1")  # adjust encoding if needed

# Create a unique logger filename with timestamp
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_filename = f"logger_{timestamp}.csv"
log_file_path = os.path.join(directory_path, log_filename)

# Helper function: Convert decimal degrees to EXIF DMS rational format (tuples required)
def deg_to_dms_rational(deg_float):
    deg_abs = abs(deg_float)
    degrees = int(deg_abs)
    minutes_float = (deg_abs - degrees) * 60
    minutes = int(minutes_float)
    seconds_float = (minutes_float - minutes) * 60
    sec_num = int(round(seconds_float * 100))
    sec_den = 100
    return ((degrees, 1), (minutes, 1), (sec_num, sec_den))


# Use `with` block to safely open and auto-close logger
with open(log_file_path, mode='w', newline='', encoding='utf-8') as log_file:
    logger = csv.writer(log_file)
    logger.writerow(["timestamp", "original_name", "new_name", "success", "message"])  # header row

    # Iterate through each row of the CSV
    for idx, row in data.iterrows():
        image_filename = row["Original_File_Name"]
        new_filename_raw = str(row["New_File_Name"])
        latitude = row["Y_coord"]
        longitude = row["X_coord"]
        image_path = os.path.join(directory_path, image_filename)

        # Ensure the new filename has a .jpg extension
        if not new_filename_raw.lower().endswith(".jpg"):
            new_filename = new_filename_raw + ".jpg"
        else:
            new_filename = new_filename_raw

        new_path = os.path.join(directory_path, new_filename)

        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except Exception:
            msg = f"Invalid lat/lon values: lat='{latitude}', lon='{longitude}'"
            print(f"[!] Row {idx}: {msg}")
            logger.writerow([datetime.now().isoformat(), image_filename, "", False, msg])
            continue

        if not os.path.isfile(image_path):
            msg = f"File not found: {image_filename}"
            print(f"[!] {msg}")
            logger.writerow([datetime.now().isoformat(), image_filename, "", False, msg])
            continue

        try:
            exif_dict = piexif.load(image_path)
        except Exception:
            exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}

        gps_ifd = exif_dict.get("GPS", {})
        already_has_gps = gps_ifd.get(piexif.GPSIFD.GPSLatitude) is not None

        # Convert decimal coordinates to EXIF-compatible format
        lat_ref = "N" if latitude >= 0 else "S"
        lon_ref = "E" if longitude >= 0 else "W"
        lat_dms = deg_to_dms_rational(latitude)
        lon_dms = deg_to_dms_rational(longitude)

        try:
            # Insert GPS only if not already present
            if not already_has_gps:
                gps_ifd[piexif.GPSIFD.GPSLatitudeRef] = lat_ref.encode()
                gps_ifd[piexif.GPSIFD.GPSLatitude] = lat_dms
                gps_ifd[piexif.GPSIFD.GPSLongitudeRef] = lon_ref.encode()
                gps_ifd[piexif.GPSIFD.GPSLongitude] = lon_dms
                exif_dict["GPS"] = gps_ifd
                exif_bytes = piexif.dump(exif_dict)
                piexif.insert(exif_bytes, image_path)

            # Always rename the file
            os.rename(image_path, new_path)

            # Status message
            status_msg = (
                "Renamed only (GPS already existed)"
                if already_has_gps else
                "Inserted GPS and renamed"
            )
            print(f"[OK] {status_msg}: {image_filename} → {new_filename}")
            logger.writerow([datetime.now().isoformat(), image_filename, new_filename, True, status_msg])
            log_file.flush()  # optional: ensure write

        except Exception as e:
            msg = f"Failed during insert/rename: {e}"
            print(f"[ERROR] {msg}")
            logger.writerow([datetime.now().isoformat(), image_filename, "", False, msg])
            log_file.flush()
