#! python3
import sys
# for problems with packages once uncommet line below (with correct site-packages directory)
sys.path.append(r"C:\Users\elyah\AppData\Local\Programs\Python\Python38\Lib\site-packages")

from neo4j import GraphDatabase
import logging
from neo4j.exceptions import ServiceUnavailable


from Autodesk.Revit.UI import (TaskDialog, TaskDialogCommonButtons,
                               TaskDialogCommandLinkId, TaskDialogResult)
import os
import numpy as np
import pandas as pd
import statistics
import json

from Autodesk.Revit.DB import *
# from Autodesk.Revit.UI.Selection import *
# from System.Windows.Forms import FolderBrowserDialog
# from System.Collections.Generic import List
# from Autodesk.Revit.DB.IFC import *

from openpyxl.workbook import Workbook

app = __revit__.Application
doc = __revit__.ActiveUIDocument.Document
# uidoc = __revit__.ActiveUIDocument

class App:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        # Don't forget to close the driver connection when you are finished with it
        self.driver.close()

    def load_data(self):
        # delete all previos data
        # ask user if he will update or delete all data
        title = "Update or delete"
        dialog = TaskDialog(title)
        dialog.MainInstruction = "Do you want delete previous nodes and relationships?"
        dialog.CommonButtons = TaskDialogCommonButtons.Yes | TaskDialogCommonButtons.No
        result = dialog.Show()
        if result == TaskDialogResult.Yes:
            self.driver.execute_query("MATCH (n) DETACH DELETE n")
        
        # filter categories
        directory = os.path.dirname(os.path.abspath(__file__))
        name = "Revit-Categories-2022_arc.xlsx"
        filename = os.path.join(directory,name)
        # data directory for filter categories
        data_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(directory)))))
        data_cat = pd.read_excel(filename)
        df_cat = pd.DataFrame(data_cat)
        df_cat = df_cat.loc[df_cat['Support'] == "Yes"]
        categories = df_cat.values

        #collect all elements direct from Revit
        # create document as node
        doc_name = doc.Title
        doc_path = doc.PathName
        self.driver.execute_query("""MERGE (d:Document {name: $doc_name, 
                                                        path: $doc_path})""",doc_name = doc_name,doc_path = doc_path,database = "neo4j").summary

        all_collection = FilteredElementCollector(doc).WhereElementIsNotElementType().ToElements()
        for elem in all_collection:
            try:
                filter_cat = elem.Category.Name
            except:
                filter_cat = None
            if filter_cat in categories:
                id = elem.Id
                unique_Id = elem.UniqueId
                typ = elem.Name
                try:
                    eId = elem.GetTypeId()
                    elemType = doc.GetElement(eId)
                    if elemType != None:
                        fam_name = elemType.FamilyName
                except:
                    fam_name = elem.Symbol.Family.Nametype
                
                self.driver.execute_query("""MERGE (e:Element {category: $filter_cat,
                                                                id: $id,
                                                                unique_id: $unique_Id,
                                                                family_name: $fam_name,
                                                                typ:$typ})""",
                                                                id = id.IntegerValue,
                                                                unique_Id = unique_Id,
                                                                fam_name=fam_name,
                                                                typ = typ,
                                                                filter_cat = filter_cat,
                                                                database = "neo4j").summary
        room_collection = FilteredElementCollector(doc).WherePasses(ElementCategoryFilter(BuiltInCategory.OST_Rooms)).WhereElementIsNotElementType().ToElements()
        for room in room_collection:
            category = room.Category.Name
            id = room.Id
            unique_Id = room.UniqueId
            room_num = room.Number
            room_name = room.LookupParameter('Name').AsString()
            levelId = room.LevelId
            level_name = room.Level.Name
            self.driver.execute_query("""MERGE (e:Element {category: $category,
                                                                id: $id,
                                                                unique_id: $unique_Id,
                                                                room_number: $room_num,
                                                                room_name:$room_name,
                                                                levelId: $levelId,
                                                                level_name: $level_name})""",
                                                                id = id.IntegerValue,
                                                                unique_Id = unique_Id,
                                                                room_name=room_name,
                                                                room_num = room_num,
                                                                category = category,
                                                                levelId = levelId.IntegerValue,
                                                                level_name = level_name,
                                                                database = "neo4j").summary
        levels_collection =  FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Levels).WhereElementIsNotElementType().ToElements()
        for level in levels_collection:
            if level != None:
                category = level.Category.Name
                id = level.Id
                unique_Id = level.UniqueId
                level_name = level.Name
                level_elev = level.Elevation

                self.driver.execute_query("""MERGE (e:Element {category: $category,
                                                                    id: $id,
                                                                    unique_id: $unique_Id,
                                                                    level_name:$level_name,
                                                                    elevation: $level_elev})""",
                                                                    id = id.IntegerValue,
                                                                    unique_Id = unique_Id,
                                                                    category = category,
                                                                    level_elev = level_elev,
                                                                    level_name = level_name,
                                                                database = "neo4j").summary
        
        self.driver.execute_query("""MATCH (a:Element{category:"Levels"}),
                                            (b:Element{category:"Rooms"})
                                            WHERE a.id = b.levelId
                                            MERGE (b) - [r:BELONGS] -> (a)""",database = "neo4j").summary
        self.driver.execute_query("""MATCH (a:Document),
                                            (b:Element{category:"Levels"})
                                            MERGE (b) - [r:BELONGS] -> (a)""",database = "neo4j").summary
        # get windows - successfull
        nameOfFile_csv = 'data\\tables\\space_elements_windows.csv'
        completename_csv =os.path.join(data_dir,nameOfFile_csv)
        df_win = pd.read_csv(completename_csv)

        # get doors - integrated, in progress
        nameOfFile_csv = 'data\\tables\\space_elements_doors.csv'
        completename_csv =os.path.join(data_dir,nameOfFile_csv)
        df_doors = pd.read_csv(completename_csv)

        # get walls - not integrated
        nameOfFile_csv = 'data\\tables\\space_elements_walls.csv'
        completename_csv =os.path.join(data_dir,nameOfFile_csv)
        df_walls = pd.read_csv(completename_csv)

        # get floors - not integrated
        nameOfFile_csv = 'data\\tables\\space_elements_floors.csv'
        completename_csv =os.path.join(data_dir,nameOfFile_csv)
        df_floors = pd.read_csv(completename_csv)

        # get furniture - not integrated
        nameOfFile_csv = 'data\\tables\\space_elements_furniture.csv'
        completename_csv =os.path.join(data_dir,nameOfFile_csv)
        df_furniture = pd.read_csv(completename_csv)

        # get elements - successful
        nameOfFile_csv = 'data\\tables\\space_elements.csv'
        completename_csv =os.path.join(data_dir,nameOfFile_csv)
        df_elements = pd.read_csv(completename_csv)

        # get elements bounds - successfull
        nameOfFile_csv = 'data\\tables\\space_elements_bounds.csv'
        completename_csv =os.path.join(data_dir,nameOfFile_csv)
        df_bound = pd.read_csv(completename_csv)

        # define elements which contains in the room
        df_elements_gr = df_elements.groupby("Room_uniqueId")
        for key in df_elements_gr.groups.keys():
            df_room = df_elements_gr.get_group(key)
            for item,row in df_room.iterrows():
                # print(type(row['ElementId']))
                self.driver.execute_query("""MATCH (a:Element),
                                            (b:Element{category:"Rooms"})
                                            WHERE a.id = $elemId AND b.id = $roomId
                                            MERGE (b) - [r:CONTAINS] -> (a)""",
                                            elemId = row['ElementId'],
                                            roomId = row['Room_Id'], database = "neo4j").summary
        # define elements which bounds room        
        df_bound_gr = df_bound.groupby('Room_uniqueId')
        for key in df_elements_gr.groups.keys():
            df_b= df_bound_gr.get_group(key)
            for item,row in df_b.iterrows():
                # print(type(row['ElementId']))
                self.driver.execute_query("""MATCH (a:Element),
                                            (b:Element{category:"Rooms"})
                                            WHERE a.id = $elemId AND b.id = $roomId
                                            MERGE (a) - [r:BOUNDS] -> (b)""",
                                            elemId = row['ElementId'],
                                            roomId = row['Room_Id'], database = "neo4j").summary
        # working with windows
        for item,row in df_win.iterrows():
            unique_id = row['Element_uniqueId']
            width = row['Window_width']
            height = row['Window_height']
            elementId_vert = json.loads(row['ElementId_vert'])
            elementId_hor = json.loads(row['ElementId_hor'])
            distance_vert = json.loads(row['Distance_to_edges_vert'])
            distance_hor = json.loads(row['Distance_to_edges_hor'])
            dis_to_next = row['Distance_to_next_win_min']
            for el_v in elementId_vert:
                index = elementId_vert.index(el_v)
                dist = distance_vert[index]
                self.driver.execute_query("""MATCH (a:Element),
                                            (b:Element{category:"Windows"})
                                            WHERE b.unique_id = $unique_id AND a.id = $el_v
                                            MERGE (b) - [r:DISTANCE_VERT {distance: $dist}] -> (a)""",
                                            unique_id = unique_id,
                                            dist = dist, 
                                            el_v = el_v, database = "neo4j").summary
            for el_h in elementId_hor:
                index = elementId_hor.index(el_h)
                dist = distance_hor[index]
                self.driver.execute_query("""MATCH (a:Element),
                                            (b:Element{category:"Windows"})
                                            WHERE b.unique_id = $unique_id AND a.id = $el_h
                                            MERGE (b) - [r:DISTANCE_HOR {distance: $dist}] -> (a)""",
                                            unique_id = unique_id,
                                            dist = dist,
                                            el_h = el_h, database = "neo4j").summary
                
            self.driver.execute_query("""MATCH (a:Element{category:"Windows"})
                                            WHERE a.unique_id = $unique_id
                                            SET a.distance_to_next_win_min = $dis_to_next,
                                                a.width = $width,
                                                a.height = $height""",
                                            unique_id = unique_id,
                                            dis_to_next = dis_to_next,
                                            width = width,
                                            height = height,
                                            database = "neo4j").summary
        # working with doors
        for item,row in df_doors.iterrows():
            unique_id = row['Element_uniqueId']
            width = row['Door_width']
            height = row['Door_height']
            elementId_vert = json.loads(row['ElementId_vert'])
            elementId_hor = json.loads(row['ElementId_hor'])
            distance_vert = json.loads(row['Distance_to_edges_vert'])
            distance_hor = json.loads(row['Distance_to_edges_hor'])
            dis_to_next = row['Distance_to_next_door_min']
            for el_v in elementId_vert:
                index = elementId_vert.index(el_v)
                dist = distance_vert[index]
                self.driver.execute_query("""MATCH (a:Element),
                                            (b:Element{category:"Doors"})
                                            WHERE b.unique_id = $unique_id AND a.id = $el_v
                                            MERGE (b) - [r:DISTANCE_VERT {distance: $dist}] -> (a)""",
                                            unique_id = unique_id,
                                            dist = dist, 
                                            el_v = el_v, database = "neo4j").summary
            for el_h in elementId_hor:
                index = elementId_hor.index(el_h)
                dist = distance_hor[index]
                self.driver.execute_query("""MATCH (a:Element),
                                            (b:Element{category:"Doors"})
                                            WHERE b.unique_id = $unique_id AND a.id = $el_h
                                            MERGE (b) - [r:DISTANCE_HOR {distance: $dist}] -> (a)""",
                                            unique_id = unique_id,
                                            dist = dist,
                                            el_h = el_h, database = "neo4j").summary
                
            self.driver.execute_query("""MATCH (a:Element{category:"Doors"})
                                            WHERE a.unique_id = $unique_id
                                            SET a.distance_to_next_door_min = $dis_to_next,
                                                a.width = $width,
                                                a.height = $height""",
                                            unique_id = unique_id,
                                            dis_to_next = dis_to_next,
                                            width = width,
                                            height = height,
                                            database = "neo4j").summary


if __name__ == "__main__":
    # Aura queries use an encrypted connection using the "neo4j+s" URI scheme
    uri = "neo4j+s://8e5153b5.databases.neo4j.io"
    user = "neo4j"
    password = "Mmte2MYxy73Y0_pUSmCFy_ZxgHvjUaMTS14m4d8A5d8"
    app = App(uri, user, password)
    app.load_data()
    app.close()