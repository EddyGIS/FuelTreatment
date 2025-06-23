# standalone_photopoints.py

import sys
import os
import arcpy
from datetime import datetime

#— PARAMETERS FROM TOOLBOX DIALOG —#
in_folders_text = arcpy.GetParameterAsText(0)  # multivalue: “C:\A;C:\B;C:\C”
out_fc          = arcpy.GetParameterAsText(1)
bad_table       = arcpy.GetParameterAsText(2)
include_option  = arcpy.GetParameterAsText(3)
attach_option   = arcpy.GetParameterAsText(4)

# Split the multivalue folder string into a Python list
in_folders = [f for f in in_folders_text.split(';') if f.strip()]

# Log inputs
arcpy.AddMessage("Running GeoTaggedPhotosPlus with:")
arcpy.AddMessage(f"  Folders               = {in_folders}")
arcpy.AddMessage(f"  Output Feature Class  = {out_fc}")
arcpy.AddMessage(f"  Invalid Photos Table  = {bad_table}")
arcpy.AddMessage(f"  Include Option        = {include_option}")
arcpy.AddMessage(f"  Attach Option         = {attach_option}")

# Prepare a list to hold intermediate in-memory feature classes
temp_fcs = []

for folder in in_folders:
    folder_name = os.path.basename(os.path.normpath(folder))
    arcpy.AddMessage(f"Processing folder: {folder_name}")

    # Create a temporary in-memory feature class
    temp_fc = arcpy.CreateUniqueName(f"temp_pts_{folder_name}", "in_memory")

    # Run the core GeoTaggedPhotosToPoints tool
    arcpy.management.GeoTaggedPhotosToPoints(
        folder,
        temp_fc,
        bad_table,
        include_option,
        attach_option
    )

    # Add a TEXT field for the folder name
    arcpy.management.AddField(
        in_table=temp_fc,
        field_name="FolderID",
        field_type="TEXT",
        field_length=50,
        field_alias="Folder Name"
    )

    # Populate FolderID with the folder name
    expr = f"r'{folder_name}'"
    arcpy.management.CalculateField(
        in_table=temp_fc,
        field="FolderID",
        expression=expr,
        expression_type="PYTHON3"
    )

    temp_fcs.append(temp_fc)

# Merge all per-folder feature classes into the final output
arcpy.AddMessage(f"Merging {len(temp_fcs)} feature classes into {out_fc}")

if temp_fcs:
    arcpy.management.Merge(
        inputs=temp_fcs,
        output=out_fc
    )
    arcpy.AddMessage("Merge completed.")
else:
    arcpy.AddWarning("No feature classes to merge — check your input folders.")

arcpy.AddMessage("GeoTaggedPhotosPlus completed successfully.")


#   CUSTOM LOGIC IDEAS—#
#
#   select multiple folders, not just one. Create an attibute column that will be populated with a unique identifier for each folder.
#   date filtering
#   reprojection
#   writing a custom log file
