#-------------------------------------------------------------------------------
# Name:        Panarama_Split
# Purpose:
#
# Author:      Edward Graham
#
# Created:     14/07/2025
# Copyright:   (c) Edward Graham 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import os
from PIL import Image
import numpy as np
import py360convert
import piexif

def main():
    # Root directory containing your panoramas (including subfolders)
    root_dir = r"C:\Users\Edward Graham\Desktop\Eagle_W_XY"

    # Define suffixes and corresponding yaw angles (degrees)
    suffixes = {
        "_a": 0,
        "_b": 90,
        "_c": 180,
        "_d": 270,
    }

    # Walk through folders, excluding any with "raw" in the name
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if "raw" in os.path.basename(dirpath).lower():
            continue

        # Find all JPEG/JPG files
        pano_files = [f for f in filenames if f.lower().endswith((".jpg", ".jpeg"))]
        if not pano_files:
            continue

        # Create an output subfolder named "<original_folder>_split"
        parent_folder_name = os.path.basename(dirpath)
        split_folder = os.path.join(dirpath, f"{parent_folder_name}_split")
        os.makedirs(split_folder, exist_ok=True)

        # Process each panorama
        for fname in pano_files:
            input_path = os.path.join(dirpath, fname)

            # Load original EXIF metadata
            try:
                exif_dict = piexif.load(input_path)
                exif_bytes = piexif.dump(exif_dict)
            except Exception:
                exif_bytes = None

            # Load image and convert to array
            img = Image.open(input_path)
            arr = np.array(img)
            height, width, _ = arr.shape

            base, ext = os.path.splitext(fname)
            for suffix, yaw in suffixes.items():
                # e2p signature: e2p(e_img, fov_deg, u_deg, v_deg, out_hw, in_rot_deg=0, mode="bilinear")
                persp = py360convert.e2p(
                    arr,
                    90,               # fov_deg: horizontal & vertical FOV if single value
                    yaw,              # u_deg: yaw (horizontal viewing angle)
                    0,                # v_deg: pitch (vertical viewing angle)
                    (height, height)  # out_hw: (output_height, output_width)
                )
                out_fname = f"{base}{suffix}{ext}"
                out_path = os.path.join(split_folder, out_fname)

                # Save with original EXIF if available
                out_img = Image.fromarray(persp)
                if exif_bytes:
                    out_img.save(out_path, exif=exif_bytes)
                else:
                    out_img.save(out_path)

                print(f"Saved: {out_path}")

if __name__ == '__main__':
    main()

# Note: Ensure you have 'py360convert' installed via:
# pip install py360convert
