# Author: lundeak
# Date: 4/16/21

# Purpose: This script uses a structures feature class (such as towers or poles) to determine
# import packages. It is in initial development phases and will be restructured into a series of functions that
# run on user inputs specified in a runfile

# import sys
import os
import arcpy

# Set workspace
inWS = 'E:\\Spherical_Imagery\\Data\\03_EO'
#inWS_shp = 'E:\\Spherical_Imagery\\PGE_8k_Poles\\Data\\01_Resources\\Shapes'
arcpy.env.workspace = inWS
outWS = 'E:\\Spherical_Imagery\\Data\\01_Resources\\Shapes\\test'

# Read in spherical tour and structures feature classes

target_pts = "01_Resources\\Shapes\\Structures.shp"
spherical_pts = [{"mission": "d1", "fp": "d1_EO.txt"},
                 {"mission": "d2", "fp": "d2_EO.txt"},
                 {"mission": "d3", "fp": "d3_EO.txt"}]

user_EPSG = input("What is the EPSG code for this EO file? ")
sr = arcpy.SpatialReference(user_EPSG)

# Make event layer from EO txt files

for EO_file in spherical_pts:
    shp_list = []
    in_table = EO_File["fp"]
    mission = EO_file["mission"]

    in_x_field = "LON"
    in_y_field = "LAT"
    in_z_field = "ALT"

    out_lyr = '{}_EO_points'.format(mission)
    out_shp_name = '{}.shp'.format(out_lyr)
    out_shp = os.path.join(outWS, out_shp_name)

    try:
        arcpy.MakeXYEventLayer_management(in_table, in_x_field, in_y_field,
                                          out_lyr)
        print(arcpy.GetCount_management(out_lyr))
        arcpy.FeatureClassToShapefile_conversion(out_lyr, out_shp)

        shp_list.append({'mission': mission, 'shp': out_shp})

    except Exception:
        e = sys.exc_info()[1]
        print(e.args[0])

# convert target feature class to polyline

in_fc = target_pts
out_fc = "Structures_pline.shp"
lineField = "LINE_ID"
sortField = "STR_GEOTAG"  # tried also (default) and STR_NUM; default is also similarly imperfect but passable

if not arcpy.Exists(out_fc):
    arcpy.PointsToLine_management(in_fc, out_fc, lineField, sortField)
    target_pline = out_fc
else:
    print("Structure_pline.shp already exists")
    target_pline = out_fc

# Select and extract features by location, with 300 ft buffer

for fc in spherical_fcs:
    in_fc = fc["fp"]
    mission = fc["mission"]

    # Select by Location
    overlap_type = 'WITHIN_A_DISTANCE'
    select_features = target_pline
    search_distance = '300 Feet'
    selection_type = 'NEW_SELECTION'

    if arcpy.Exists(in_fc):
        mission_lyr = '{}_lyr'.format(mission)
        # mission_sr = arcpy.Describe(in_fc).spatialReference
        arcpy.MakeFeatureLayer_management(in_fc, mission_lyr)
        # chk = arcpy.Describe(mission_lyr).SpatialReference
        # print(chk.Name)
        arcpy.SelectLayerByLocation_management(mission_lyr,
                                               overlap_type,
                                               select_features,
                                               search_distance,
                                               selection_type
                                               )

        # Feature Layer to Feature Class
        record_ct = arcpy.GetCount_management(mission_lyr)

        try:
            arcpy.env.workspace = inWS
            new_fc_name = '{}_subset_to_structures.shp'.format(mission)
            mission_fc = os.path.join(outWS, new_fc_name)

            if not arcpy.Exists(mission_fc):
                arcpy.CopyFeatures_management(mission_lyr, mission_fc)
                # try:
                #     arcpy.DefineProjection_management(mission_fc, mission_sr)
                # except Exception:
                #     e = sys.exc_info()[1]
                #     print(e.args[0])
                chk = arcpy.Describe(mission_fc).SpatialReference
                print(chk.Name)

                print("{} records written to file {}".format(record_ct[0], new_fc_name))
            else:
                print("This subset already exists -- delete or rename if new subset desired")

            # Export CSV
            # if arcpy.Exists(mission_fc):
            delimiter = 'COMMA'
            csv_name = '{}_EO_subset_to_structures.txt'.format(mission)
            export_csv = os.path.join(outWS, csv_name)
            fields = [f.name for f in arcpy.ListFields(mission_fc)]
            fields_decoded = [field.encode("utf-8") for field in fields]
            fields_decoded.remove('Shape') # shape field was "invalid" for export

            try:
                if not arcpy.Exists(export_csv):
                    arcpy.ExportXYv_stats(mission_fc,
                                          fields_decoded,
                                          delimiter,
                                          export_csv,
                                          "ADD_FIELD_NAMES"
                                          )
                else:
                    print("This csv/txt file already exists, delete or rename if new subset desired.")
            except Exception:
                e = sys.exc_info()[1]
                print(e.args[0])

        except Exception:
            print("Error in writing feature layer to feature class")
            e = sys.exc_info()[1]
            print(e.args[0])

    else:
        print("target feature class does not exist")