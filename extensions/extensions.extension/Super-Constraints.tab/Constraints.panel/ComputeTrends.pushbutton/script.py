#! python3
import sys
# print(sys.version)
# for problems with packages once uncommet line below (with correct site-packages directory)
# sys.path.append(r"C:\Users\elyah\AppData\Local\Programs\Python\Python38\Lib\site-packages")
# import clr
import os
import os.path

# clr.AddReference("System")
# clr.AddReference('RevitAPI')
# clr.AddReference('RevitServices')
import numpy as np
import pandas as pd

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import *
from System.Windows.Forms import FolderBrowserDialog
from System.Collections.Generic import List
from Autodesk.Revit.DB.IFC import *

from openpyxl.workbook import Workbook

global doc
# global room_solid

app = __revit__.Application
doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument

t = Transaction(doc, "Get all elements in the model")
t.Start()


# filter categories
directory = os.path.dirname(os.path.abspath(__file__))

# data directory for filter categories
data_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(directory)))))

# get windows
nameOfFile_csv = 'data\\tables\\space_elements_windows.csv'
completename_csv =os.path.join(data_dir,nameOfFile_csv)
df_win = pd.read_csv(completename_csv)
# df_win['Distance_to_edges_min'] = np.nan
# df_win['Distance_to_edges_max'] = np.nan
df_win_new = pd.DataFrame()

# get doors
nameOfFile_csv = 'data\\tables\\space_elements_doors.csv'
completename_csv =os.path.join(data_dir,nameOfFile_csv)
df_doors = pd.read_csv(completename_csv)

# get walls
nameOfFile_csv = 'data\\tables\\space_elements_walls.csv'
completename_csv =os.path.join(data_dir,nameOfFile_csv)
df_walls = pd.read_csv(completename_csv)

# get floors
nameOfFile_csv = 'data\\tables\\space_elements_floors.csv'
completename_csv =os.path.join(data_dir,nameOfFile_csv)
df_floors = pd.read_csv(completename_csv)

# get furniture
nameOfFile_csv = 'data\\tables\\space_elements_furniture.csv'
completename_csv =os.path.join(data_dir,nameOfFile_csv)
df_furniture = pd.read_csv(completename_csv)

# get elements
nameOfFile_csv = 'data\\tables\\space_elements.csv'
completename_csv =os.path.join(data_dir,nameOfFile_csv)
df_elements = pd.read_csv(completename_csv)




# WINDOWS
# analyse windows
nameOfFile_txt = 'data\\tables\\windows_report.txt'
completename_txt = os.path.join(data_dir,nameOfFile_txt)
win_file = open(completename_txt,'w+')
win_file.write("Analyse windows \n")
win_file.write('1. Analyse all windows (by category:Windows) \n')
# analyse windows all by category - completed
str_wh = df_win.agg({'Window_width':['min','mean','max'],'Window_height':['min','mean','max']}).values
str_e_hor_min = df_win.agg({'Distance_to_edges_hor_mi':['min']}).values[0]
str_e_hor_mean = df_win.agg({'Distance_to_edges_hor_mean':['mean']}).values[0]
str_e_hor_max = df_win.agg({'Distance_to_edges_hor_ma':['max']}).values[0]
str_e_vert_min = df_win.agg({'Distance_to_edges_vert_mi':['min']}).values[0]
str_e_vert_mean = df_win.agg({'Distance_to_edges_vert_mean':['mean']}).values[0]
str_e_vert_max = df_win.agg({'Distance_to_edges_vert_ma':['max']}).values[0]
str_n_min = df_win.agg({'Distance_to_next_win_min':['min']}).values[0]
str_1 = pd.Series({'Category': 'Windows','Width':str_wh[0],'Height':str_wh[1],
                    'Distance_to_edges_hor':[str_e_hor_min[0],str_e_hor_mean[0],str_e_hor_max[0]],
                    'Distance_to_edges_vert':[str_e_vert_min[0],str_e_vert_mean[0],str_e_vert_max[0]],
                    'Distance_to_next':[str_n_min[0],0.,0.]})
win_file.write(str_1.to_frame().T.to_string(index = False) + '\n')
df_win_new_cat = pd.concat([df_win_new,str_1.to_frame().T],ignore_index=True)
nameOfFile_csv = 'data\\tables\\windows_report_cateqory.csv'
completename_csv = os.path.join(data_dir,nameOfFile_csv)
df_win_new_cat.to_csv(completename_csv)

# analyse by room names - completed
win_file.write('2. Analyse all windows by room names \n')
df_elements_groped = df_elements.groupby('Room_name')
df_elements_keys = df_elements_groped.groups.keys()
df_win_new_roomname = pd.DataFrame()
for key in df_elements_keys:
    df_elements_gr = df_elements_groped.get_group(key)
    uniqueid = df_elements_gr['Element_uniqueId'].values
    df_win_sorted = df_win.loc[df_win['Element_uniqueId'].isin(uniqueid)]
    if len(df_win_sorted)>0:
        str_wh = df_win_sorted.agg({'Window_width':['min','mean','max'],'Window_height':['min','mean','max']}).values
        str_e_hor_min = df_win_sorted.agg({'Distance_to_edges_hor_mi':['min']}).values[0]
        str_e_hor_mean = df_win_sorted.agg({'Distance_to_edges_hor_mean':['mean']}).values[0]
        str_e_hor_max = df_win_sorted.agg({'Distance_to_edges_hor_ma':['max']}).values[0]
        str_e_vert_min = df_win_sorted.agg({'Distance_to_edges_vert_mi':['min']}).values[0]
        str_e_vert_mean = df_win_sorted.agg({'Distance_to_edges_vert_mean':['mean']}).values[0]
        str_e_vert_max = df_win_sorted.agg({'Distance_to_edges_vert_ma':['max']}).values[0]
        str_n_min = df_win_sorted.agg({'Distance_to_next_win_min':['min']}).values[0]
        str_2 = pd.Series({'Room_name': key,'Width':str_wh[0],'Height':str_wh[1],
                           'Distance_to_edges_hor':[str_e_hor_min[0],str_e_hor_mean[0],str_e_hor_max[0]],
                           'Distance_to_edges_vert':[str_e_vert_min[0],str_e_vert_mean[0],str_e_vert_max[0]],
                           'Distance_to_next':[str_n_min[0],0.,0.]})
        win_file.write(str_2.to_frame().T.to_string()  + '\n')
        df_win_new_roomname = pd.concat([df_win_new_roomname,str_2.to_frame().T],ignore_index=True)

nameOfFile_csv = 'data\\tables\\windows_report_roomname.csv'
completename_csv = os.path.join(data_dir,nameOfFile_csv)
df_win_new_roomname.to_csv(completename_csv,index=False)

# analyse by room names - completed
win_file.write('3. Analyse all windows by their family name \n')
df_elements_groped = df_elements.groupby('Family')
df_elements_keys = df_elements_groped.groups.keys()
df_win_new_famname = pd.DataFrame()
for key in df_elements_keys:
    df_elements_gr = df_elements_groped.get_group(key)
    uniqueid = df_elements_gr['Element_uniqueId'].values
    df_win_sorted = df_win.loc[df_win['Element_uniqueId'].isin(uniqueid)]
    if len(df_win_sorted)>0:
        str_wh = df_win_sorted.agg({'Window_width':['min','mean','max'],'Window_height':['min','mean','max']}).values
        str_e_hor_min = df_win_sorted.agg({'Distance_to_edges_hor_mi':['min']}).values[0]
        str_e_hor_mean = df_win_sorted.agg({'Distance_to_edges_hor_mean':['mean']}).values[0]
        str_e_hor_max = df_win_sorted.agg({'Distance_to_edges_hor_ma':['max']}).values[0]
        str_e_vert_min = df_win_sorted.agg({'Distance_to_edges_vert_mi':['min']}).values[0]
        str_e_vert_mean = df_win_sorted.agg({'Distance_to_edges_vert_mean':['mean']}).values[0]
        str_e_vert_max = df_win_sorted.agg({'Distance_to_edges_vert_ma':['max']}).values[0]
        str_n_min = df_win_sorted.agg({'Distance_to_next_win_min':['min']}).values[0]
        str_2 = pd.Series({'Family': key,'Width':str_wh[0],'Height':str_wh[1],
                           'Distance_to_edges_hor':[str_e_hor_min[0],str_e_hor_mean[0],str_e_hor_max[0]],
                           'Distance_to_edges_vert':[str_e_vert_min[0],str_e_vert_mean[0],str_e_vert_max[0]],
                           'Distance_to_next':[str_n_min[0],0.,0.]})
        win_file.write(str_2.to_frame().T.to_string()  + '\n')
        df_win_new_famname = pd.concat([df_win_new_famname,str_2.to_frame().T],ignore_index=True)

nameOfFile_csv = 'data\\tables\\windows_report_family.csv'
completename_csv = os.path.join(data_dir,nameOfFile_csv)
df_win_new_famname.to_csv(completename_csv)
#
#
#
# DOORS - WIP
# analyse doors all by category
nameOfFile_txt = 'data\\tables\\doors_report.txt'
completename_txt = os.path.join(data_dir,nameOfFile_txt)
door_file = open(completename_txt,'w+')
door_file.write("Analyse doors \n")
door_file.write('1. Analyse all doors (by category: Doors) \n')
df_door_new_cat = pd.DataFrame()
# str_1 = df_doors.agg({'Door_width':['mean','min','max'],
#             'Door_height':['mean','min','max'],
#             'Distance_to_edges_mi':['mean','min','max'],
#             'Distance_to_edges_mean':['mean','min','max'],
#             'Distance_to_edges_ma':['mean','min','max'],
#             'Distance_to_next_door_min':['mean','min','max']})
str_wh = df_doors.agg({'Door_width':['min','mean','max'],'Door_height':['min','mean','max']}).values
str_e_hor_min = df_doors.agg({'Distance_to_edges_hor_mi':['min']}).values[0]
str_e_hor_mean = df_doors.agg({'Distance_to_edges_hor_mean':['mean']}).values[0]
str_e_hor_max = df_doors.agg({'Distance_to_edges_hor_ma':['max']}).values[0]
str_e_vert_min = df_doors.agg({'Distance_to_edges_vert_mi':['min']}).values[0]
str_e_vert_mean = df_doors.agg({'Distance_to_edges_vert_mean':['mean']}).values[0]
str_e_vert_max = df_doors.agg({'Distance_to_edges_vert_ma':['max']}).values[0]
str_n_min = df_doors.agg({'Distance_to_next_door_min':['min']}).values[0]
str_1 = pd.Series({'Category': 'Doors','Width':str_wh[0],'Height':str_wh[1],
                    'Distance_to_edges_hor':[str_e_hor_min[0],str_e_hor_mean[0],str_e_hor_max[0]],
                    'Distance_to_edges_vert':[str_e_vert_min[0],str_e_vert_mean[0],str_e_vert_max[0]],
                    'Distance_to_next':[str_n_min[0],0.,0.]})
door_file.write(str_1.to_frame().T.to_string(index = False) + '\n')
df_door_new_cat = pd.concat([df_door_new_cat,str_1.to_frame().T],ignore_index=True)
nameOfFile_csv = 'data\\tables\\doors_report_category.csv'
completename_csv = os.path.join(data_dir,nameOfFile_csv)
df_door_new_cat.to_csv(completename_csv)

# analyse by room names - WIP
door_file.write('2. Analyse all doors by room names \n')
df_elements_groped = df_elements.groupby('Room_name')
df_elements_keys = df_elements_groped.groups.keys()
df_doors_new_roomname = pd.DataFrame()
for key in df_elements_keys:
    df_elements_gr = df_elements_groped.get_group(key)
    uniqueid = df_elements_gr['Element_uniqueId'].values
    df_doors_sorted = df_doors.loc[df_doors['Element_uniqueId'].isin(uniqueid)]
    if len(df_doors_sorted)>0:
        # str_2 = df_doors_sorted.agg({'Door_width':['mean','min','max'],
        #         'Door_height':['mean','min','max'],
        #         'Distance_to_edges_mi':['mean','min','max'],
        #         'Distance_to_edges_mean':['mean','min','max'],
        #         'Distance_to_edges_ma':['mean','min','max'],
        #         'Distance_to_next_door_min':['mean','min','max']})
        str_wh = df_doors_sorted.agg({'Door_width':['min','mean','max'],'Door_height':['min','mean','max']}).values
        str_e_hor_min = df_doors_sorted.agg({'Distance_to_edges_hor_mi':['min']}).values[0]
        str_e_hor_mean = df_doors_sorted.agg({'Distance_to_edges_hor_mean':['mean']}).values[0]
        str_e_hor_max = df_doors_sorted.agg({'Distance_to_edges_hor_ma':['max']}).values[0]
        str_e_vert_min = df_doors_sorted.agg({'Distance_to_edges_vert_mi':['min']}).values[0]
        str_e_vert_mean = df_doors_sorted.agg({'Distance_to_edges_vert_mean':['mean']}).values[0]
        str_e_vert_max = df_doors_sorted.agg({'Distance_to_edges_vert_ma':['max']}).values[0]
        str_n_min = df_doors_sorted.agg({'Distance_to_next_door_min':['min']}).values[0]
        str_2 = pd.Series({'Room_name': key,'Width':str_wh[0],'Height':str_wh[1],
                           'Distance_to_edges_hor':[str_e_hor_min[0],str_e_hor_mean[0],str_e_hor_max[0]],
                           'Distance_to_edges_vert':[str_e_vert_min[0],str_e_vert_mean[0],str_e_vert_max[0]],
                           'Distance_to_next':[str_n_min[0],0.,0.]})
        door_file.write(str_2.to_frame().T.to_string()  + '\n')
        df_doors_new_roomname = pd.concat([df_doors_new_roomname,str_2.to_frame().T])

nameOfFile_csv = 'data\\tables\\doors_report_roomname.csv'
completename_csv = os.path.join(data_dir,nameOfFile_csv)
df_doors_new_roomname.to_csv(completename_csv)

# analyse by families - WIP
door_file.write('3. Analyse all doors by their family name \n')
df_elements_groped = df_elements.groupby('Family')
df_elements_keys = df_elements_groped.groups.keys()
df_doors_new_famname = pd.DataFrame()
for key in df_elements_keys:
    df_elements_gr = df_elements_groped.get_group(key)
    uniqueid = df_elements_gr['Element_uniqueId'].values
    df_doors_sorted = df_doors.loc[df_doors['Element_uniqueId'].isin(uniqueid)]
    if len(df_doors_sorted)>0:
        # str_3 = df_doors_sorted.agg({'Door_width':['mean','min','max'],
        #         'Door_height':['mean','min','max'],
        #         'Distance_to_edges_mi':['mean','min','max'],
        #         'Distance_to_edges_mean':['mean','min','max'],
        #         'Distance_to_edges_ma':['mean','min','max'],
        #         'Distance_to_next_door_min':['mean','min','max']})
        str_wh = df_doors_sorted.agg({'Door_width':['min','mean','max'],'Door_height':['min','mean','max']}).values
        str_e_hor_min = df_doors_sorted.agg({'Distance_to_edges_hor_mi':['min']}).values[0]
        str_e_hor_mean = df_doors_sorted.agg({'Distance_to_edges_hor_mean':['mean']}).values[0]
        str_e_hor_max = df_doors_sorted.agg({'Distance_to_edges_hor_ma':['max']}).values[0]
        str_e_vert_min = df_doors_sorted.agg({'Distance_to_edges_vert_mi':['min']}).values[0]
        str_e_vert_mean = df_doors_sorted.agg({'Distance_to_edges_vert_mean':['mean']}).values[0]
        str_e_vert_max = df_doors_sorted.agg({'Distance_to_edges_vert_ma':['max']}).values[0]
        str_n_min = df_doors_sorted.agg({'Distance_to_next_door_min':['min']}).values[0]
        str_3 = pd.Series({'Family': key,'Width':str_wh[0],'Height':str_wh[1],
                           'Distance_to_edges_hor':[str_e_hor_min[0],str_e_hor_mean[0],str_e_hor_max[0]],
                           'Distance_to_edges_vert':[str_e_vert_min[0],str_e_vert_mean[0],str_e_vert_max[0]],
                           'Distance_to_next':[str_n_min[0],0.,0.]})
        door_file.write(str_3.to_frame().T.to_string()  + '\n')
        df_doors_new_famname = pd.concat([df_doors_new_famname,str_3.to_frame().T])

nameOfFile_csv = 'data\\tables\\doors_report_family.csv'
completename_csv = os.path.join(data_dir,nameOfFile_csv)
df_doors_new_famname.to_csv(completename_csv)
#
#
#
# WALLS
# analyse walls all by category
nameOfFile_txt = 'data\\tables\\walls_report.txt'
completename_txt = os.path.join(data_dir,nameOfFile_txt)
walls_file = open(completename_txt,'w+')
walls_file.write("Analyse walls \n")
walls_file.write('1. Analyse all walls (by category: Walls) \n')
df_walls_new_cat = pd.DataFrame()
str_1 = df_walls.agg({'Width':['mean','min','max'],
                    'Height':['mean','min','max'],
                    'Distance_to_parall_mi':['mean','min','max'],
                    'Distance_to_parall_mean':['mean','min','max'],
                    'Distance_to_parall_ma':['mean','min','max'],
                    'Angles_to_walls_mi':['mean','min','max'],
                    'Angles_to_walls_mean':['mean','min','max'],
                    'Angles_to_walls_ma':['mean','min','max']})
walls_file.write(str_1.to_string(index = False) + '\n')
df_walls_new_cat = pd.concat([df_walls_new_cat,str_1],ignore_index=True)
nameOfFile_csv = 'data\\tables\\walls_report_category.csv'
completename_csv = os.path.join(data_dir,nameOfFile_csv)
df_walls_new_cat.to_csv(completename_csv)

# analyse by room names
walls_file.write('2. Analyse all walls by room names \n')
df_elements_groped = df_elements.groupby('Room_name')
df_elements_keys = df_elements_groped.groups.keys()
df_walls_new_roomname = pd.DataFrame()
for key in df_elements_keys:
    df_elements_gr = df_elements_groped.get_group(key)
    uniqueid = df_elements_gr['Element_uniqueId'].values
    df_walls_sorted = df_walls.loc[df_walls['Element_uniqueId'].isin(uniqueid)]
    if len(df_walls_sorted)>0:
        str_2 = df_walls_sorted.agg({'Width':['mean','min','max'],
                            'Height':['mean','min','max'],
                            'Distance_to_parall_mi':['mean','min','max'],
                            'Distance_to_parall_mean':['mean','min','max'],
                            'Distance_to_parall_ma':['mean','min','max'],
                            'Angles_to_walls_mi':['mean','min','max'],
                            'Angles_to_walls_mean':['mean','min','max'],
                            'Angles_to_walls_ma':['mean','min','max']})
        old_idx = str_2.index.to_frame()
        old_idx.insert(0,'Room_name',key)
        str_2.index = pd.MultiIndex.from_frame(old_idx)
        walls_file.write(str_2.to_string()  + '\n')
        df_walls_new_roomname = pd.concat([df_walls_new_roomname,str_2])

nameOfFile_csv = 'data\\tables\\walls_report_roomname.csv'
completename_csv = os.path.join(data_dir,nameOfFile_csv)
df_walls_new_roomname.to_csv(completename_csv)

# analyse by room names
walls_file.write('3. Analyse all walls by their family name \n')
df_elements_groped = df_elements.groupby('Family')
df_elements_keys = df_elements_groped.groups.keys()
df_wall_new_famname = pd.DataFrame()
for key in df_elements_keys:
    df_elements_gr = df_elements_groped.get_group(key)
    uniqueid = df_elements_gr['Element_uniqueId'].values
    df_walls_sorted = df_walls.loc[df_walls['Element_uniqueId'].isin(uniqueid)]
    if len(df_walls_sorted)>0:
        str_3 = df_walls_sorted.agg({'Width':['mean','min','max'],
                    'Height':['mean','min','max'],
                    'Distance_to_parall_mi':['mean','min','max'],
                    'Distance_to_parall_mean':['mean','min','max'],
                    'Distance_to_parall_ma':['mean','min','max'],
                    'Angles_to_walls_mi':['mean','min','max'],
                    'Angles_to_walls_mean':['mean','min','max'],
                    'Angles_to_walls_ma':['mean','min','max']})
        old_idx = str_3.index.to_frame()
        old_idx.insert(0,'Family',key)
        str_3.index = pd.MultiIndex.from_frame(old_idx)
        walls_file.write(str_3.to_string()  + '\n')
        df_wall_new_famname = pd.concat([df_wall_new_famname,str_3])

nameOfFile_csv = 'data\\tables\\walls_report_family.csv'
completename_csv = os.path.join(data_dir,nameOfFile_csv)
df_wall_new_famname.to_csv(completename_csv)
#
#
#
# FLOORS
# analyse floors all by category
nameOfFile_txt = 'data\\tables\\floors_report.txt'
completename_txt = os.path.join(data_dir,nameOfFile_txt)
floors_file = open(completename_txt,'w+')
floors_file.write("Analyse floors \n")
floors_file.write('1. Analyse all floors (by category: Floors) \n')
df_floors_new_cat = pd.DataFrame()
str_1 = df_floors.agg({'Distance_max':['mean','min','max']})
floors_file.write(str_1.to_string(index = False) + '\n')
df_floors_new_cat = pd.concat([df_floors_new_cat,str_1],ignore_index=True)
nameOfFile_csv = 'data\\tables\\floors_report_category.csv'
completename_csv = os.path.join(data_dir,nameOfFile_csv)
df_floors_new_cat.to_csv(completename_csv)

# analyse by room names
floors_file.write('2. Analyse all floors by room names \n')
df_elements_groped = df_elements.groupby('Room_name')
df_elements_keys = df_elements_groped.groups.keys()
df_floors_new_roomname = pd.DataFrame()
for key in df_elements_keys:
    df_elements_gr = df_elements_groped.get_group(key)
    uniqueid = df_elements_gr['Element_uniqueId'].values
    df_floors_sorted = df_floors.loc[df_floors['Element_uniqueId'].isin(uniqueid)]
    if len(df_floors_sorted)>0:
        str_2 = df_floors_sorted.agg({'Distance_max':['mean','min','max']})
        old_idx = str_2.index.to_frame()
        old_idx.insert(0,'Room_name',key)
        str_2.index = pd.MultiIndex.from_frame(old_idx)
        floors_file.write(str_2.to_string()  + '\n')
        df_floors_new_roomname = pd.concat([df_floors_new_roomname,str_2])

nameOfFile_csv = 'data\\tables\\floors_report_roomname.csv'
completename_csv = os.path.join(data_dir,nameOfFile_csv)
df_floors_new_roomname.to_csv(completename_csv)

# analyse by family names
floors_file.write('3. Analyse all floors by their family name \n')
df_elements_groped = df_elements.groupby('Family')
df_elements_keys = df_elements_groped.groups.keys()
df_floors_new_famname = pd.DataFrame()
for key in df_elements_keys:
    df_elements_gr = df_elements_groped.get_group(key)
    uniqueid = df_elements_gr['Element_uniqueId'].values
    df_floors_sorted = df_floors.loc[df_floors['Element_uniqueId'].isin(uniqueid)]
    if len(df_floors_sorted)>0:
        str_3 = df_floors_sorted.agg({'Distance_max':['mean','min','max']})
        old_idx = str_3.index.to_frame()
        old_idx.insert(0,'Family',key)
        str_3.index = pd.MultiIndex.from_frame(old_idx)
        floors_file.write(str_3.to_string()  + '\n')
        df_floors_new_famname = pd.concat([df_floors_new_famname,str_3])

nameOfFile_csv = 'data\\tables\\floors_report_family.csv'
completename_csv = os.path.join(data_dir,nameOfFile_csv)
df_floors_new_famname.to_csv(completename_csv)
#
#
#
# FURNITURE
# analyse furniture all by category
nameOfFile_txt = 'data\\tables\\furniture_report.txt'
completename_txt = os.path.join(data_dir,nameOfFile_txt)
furniture_file = open(completename_txt,'w+')
furniture_file.write("Analyse furniture \n")
furniture_file.write('1. Analyse all furniture (by category: Furniture) \n')
df_furniture_new_cat = pd.DataFrame()
str_1 = df_furniture.agg({'Distance_to_nearest_mi':['mean','min','max'],
                          'Distance_to_nearest_mean':['mean','min','max'],
                          'Distance_to_nearest_ma':['mean','min','max']})
floors_file.write(str_1.to_string(index = False) + '\n')
df_furniture_new_cat = pd.concat([df_floors_new_cat,str_1],ignore_index=True)
nameOfFile_csv = 'data\\tables\\furniture_report_category.csv'
completename_csv = os.path.join(data_dir,nameOfFile_csv)
df_furniture_new_cat.to_csv(completename_csv)

# analyse by room names
furniture_file.write('2. Analyse all furniture by room names \n')
df_elements_groped = df_elements.groupby('Room_name')
df_elements_keys = df_elements_groped.groups.keys()
df_furniture_new_roomname = pd.DataFrame()
for key in df_elements_keys:
    df_elements_gr = df_elements_groped.get_group(key)
    uniqueid = df_elements_gr['Element_uniqueId'].values
    df_furniture_sorted = df_furniture.loc[df_furniture['Element_uniqueId'].isin(uniqueid)]
    if len(df_furniture_sorted)>0:
        str_2 = df_furniture_sorted.agg({'Distance_to_nearest_mi':['mean','min','max'],
                                        'Distance_to_nearest_mean':['mean','min','max'],
                                        'Distance_to_nearest_ma':['mean','min','max']})
        old_idx = str_2.index.to_frame()
        old_idx.insert(0,'Room_name',key)
        str_2.index = pd.MultiIndex.from_frame(old_idx)
        furniture_file.write(str_2.to_string()  + '\n')
        df_furniture_new_roomname = pd.concat([df_furniture_new_roomname,str_2])

nameOfFile_csv = 'data\\tables\\furniture_report_roomname.csv'
completename_csv = os.path.join(data_dir,nameOfFile_csv)
df_furniture_new_roomname.to_csv(completename_csv)

# analyse by family names
furniture_file.write('3. Analyse all furniture by their family name \n')
df_elements_groped = df_elements.groupby('Family')
df_elements_keys = df_elements_groped.groups.keys()
df_furniture_new_famname = pd.DataFrame()
for key in df_elements_keys:
    df_elements_gr = df_elements_groped.get_group(key)
    uniqueid = df_elements_gr['Element_uniqueId'].values
    df_furniture_sorted = df_furniture.loc[df_furniture['Element_uniqueId'].isin(uniqueid)]
    if len(df_furniture_sorted)>0:
        str_3 = df_furniture_sorted.agg({'Distance_to_nearest_mi':['mean','min','max'],
                                        'Distance_to_nearest_mean':['mean','min','max'],
                                        'Distance_to_nearest_ma':['mean','min','max']})
        old_idx = str_3.index.to_frame()
        old_idx.insert(0,'Family',key)
        str_3.index = pd.MultiIndex.from_frame(old_idx)
        furniture_file.write(str_3.to_string()  + '\n')
        df_furniture_new_famname = pd.concat([df_furniture_new_famname,str_3])

nameOfFile_csv = 'data\\tables\\furniture_report_family.csv'
completename_csv = os.path.join(data_dir,nameOfFile_csv)
df_furniture_new_famname.to_csv(completename_csv)
t.Commit()