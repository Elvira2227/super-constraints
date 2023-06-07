#! python3
import clr
import os
import os.path

clr.AddReference("System")
clr.AddReference('RevitAPI')
clr.AddReference('RevitServices')
import numpy as np
import pandas as pd

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import *
from System.Windows.Forms import FolderBrowserDialog
from System.Collections.Generic import List
from Autodesk.Revit.DB.IFC import *


from openpyxl.workbook import Workbook

global doc
global room_solid

app = __revit__.Application
doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument

t = Transaction(doc, "Get all elements from room")
t.Start()

# pic room object
choise = uidoc.Selection
pickedElement = choise.PickObject(ObjectType.Element, "Select room")
selectedElement = doc.GetElement(pickedElement.ElementId)
print(selectedElement.GetType().ToString())
if selectedElement.GetType().ToString() != "Autodesk.Revit.DB.Architecture.Room":
    print("Wrong element selected. Operation breaks.")
    t.Commit()

#empty database
df = pd.DataFrame()
# filter categories
directory = os.path.dirname(os.path.abspath(__file__))
name = "Revit-Categories-2022_arc.xlsx"
filename = os.path.join(directory,name)
# data directory
data_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(directory)))))

data_cat = pd.read_excel(filename)
df_cat = pd.DataFrame(data_cat)
df_cat = df_cat.loc[df_cat['Support'] == "Yes"]
df_fur = df_cat.loc[df_cat['Furniture'] == "Yes"]

# collector_2 = FilteredElementCollector(doc)
# # collector_2.OfClass(FamilyInstance)
# collector_2.WherePasses(ElementIntersectsSolidFilter(room_solid))
# furniture_elements = List[ElementId]()

#==============================================================================
#  function ckecks if element locates in the room 
#  otherwise check intersection between geometry representation
#  returns element id if element id located in the selected room
def find_room_from_elem_location(elem):
    location = elem.Location
    if location != None:
        location_type = location.GetType().ToString()
        if location_type == "LocationPoint":
            # point location
            loc_point = location.Point
            room_elem = doc.GetRoomAtPoint(loc_point)
            if room_elem != None:
                # cannot find room for columns
                if room_elem.Id.Equals(selectedElement.Id):
                    return elem.Id
            else:
                inter = find_intersection_elemToRoomSolid(elem,room_solid)
                if inter == 1:
                    return elem.Id
        elif location_type == "LocationCurve":
            # curve location
            loc_curve = location.Curve
            if room_solid.IntersectWithCurve(curve,SolidCurveIntersectionOptions()) != None:
                return elem.Id
            else:
                inter = find_intersection_elemToRoomSolid(elem,room_solid)
                if inter == 1:
                    return elem.Id
        # elif location_type == "Location":

        else:
            # find intersections
            inter = find_intersection_elemToRoomSolid(elem,room_solid)
            if inter == 1:
                return elem.Id

#==============================================================================
# function finds opening cut in the wall
def get_opening_cut(door,wall,dir,room):
    print("test")
    elem_geom = door.get_Geometry(Options())
    door_solid = None
    for geomInst in elem_geom:
        if geomInst.GetType().ToString() == "Autodesk.Revit.DB.GeometryInstance":
                instGeom = geomInst.GetInstanceGeometry()
                for instObj in instGeom:
                    if instObj.GetType().ToString() == "Autodesk.Revit.DB.Solid":
                        if instObj.Faces.Size != 0 and instObj.Edges.Size != 0 and instObj.Volume > 0.0:
                            door_solid = instObj
                            door_solid = BooleanOperationsUtils.ExecuteBooleanOperation(door_solid,instObj,BooleanOperationsType.Union)
    dif_solid = None
    wall_solid = None
    elem_geom = wall.get_Geometry(Options())
    for geomInst in elem_geom:
        # if geomInst.GetType().ToString() == "Autodesk.Revit.DB.Solid":
        if geomInst.Faces.Size != 0 and geomInst.Edges.Size != 0 and geomInst.Volume > 0.0:
            wall_solid = geomInst
            print(wall_solid.Volume)
            dif_solid = BooleanOperationsUtils.ExecuteBooleanOperation(door_solid,wall_solid,BooleanOperationsType.Difference)
            
    if dif_solid != None:
        for face in dif_solid.Faces:
            loc = room.Location.Point
            dir_rm = face.ComputeNormal(UV(loc.X,loc.Y))
            if dir.IsAlmostEqualTo(dir_rm):
                print("Curve loop funded!")
                return face.GetEdgesAsCurveLoops()
#==============================================================================
#  function finds intersections between element solid and room solid
#  returns i if intersections occured   
def find_intersection_elemToRoomSolid(elem, room_solid):
    elem_geom = elem.get_Geometry(Options())
    inter = 0
    for geomInst in elem_geom:
        if geomInst.GetType().ToString() == "Autodesk.Revit.DB.GeometryInstance":
                instGeom = geomInst.GetInstanceGeometry()
                for instObj in instGeom:
                    if instObj.GetType().ToString() == "Autodesk.Revit.DB.Solid":
                        if instObj.Faces.Size != 0 and instObj.Edges.Size != 0:
                            furn_solid = instObj
                            try:
                                interSolid = BooleanOperationsUtils.ExecuteBooleanOperation(room_solid,furn_solid,BooleanOperationsType.Intersect)
                                if interSolid.Volume > 0.0000001:
                                    inter = 1 
                                    return inter
                            except:
                                pass
        elif geomInst.GetType().ToString() == "Autodesk.Revit.DB.Solid":
                if geomInst.Faces.Size != 0 and geomInst.Edges.Size != 0:
                    furn_solid = geomInst
                    try:
                        interSolid = BooleanOperationsUtils.ExecuteBooleanOperation(room_solid,furn_solid,BooleanOperationsType.Intersect)
                        if interSolid.Volume > 0.0:
                            inter = 1 
                            return inter
                    except:
                        pass
        elif geomInst.GetType().ToString() == "Autodesk.Revit.DB.Line":
            inter_options = SolidCurveIntersectionOptions()
            interSolid = room_solid.IntersectWithCurve(geomInst,inter_options)
            print(interSolid.ResultType)
            res = interSolid.ResultType
            if res == 0:
                return 1          
    return inter

# get room solid from spatial calculator
sel_location = selectedElement.Location.Point
options = SpatialElementBoundaryOptions()
calculator = SpatialElementGeometryCalculator(doc,options)
results = calculator.CalculateSpatialElementGeometry(selectedElement)
room_solid = results.GetGeometry()

# collect all bounding elements of the room: walls and floors
face_dic = {}
room_faces_dw = {}
bounds_elem = List[ElementId]()
added_elements = List[ElementId]()
furniture_elements = List[ElementId]()
doors_elements = List[ElementId]()
windows_elements = List[ElementId]()
count = 0
faces = []
for face in room_solid.Faces:
    count = count + 1
    faces.append(face)
    face_list = results.GetBoundaryFaceInfo(face)
    for f in face_list:
        link_elem = f.SpatialBoundaryElement
        try:
            link_elem_Id = link_elem.HostElementId
        except:
            link_elem_Id = link_elem.LinkedElementId
        elem = doc.GetElement(link_elem_Id)
        if not added_elements.Contains(elem.Id) and not bounds_elem.Contains(elem.Id):
            added_elements.Add(elem.Id)
            bounds_elem.Add(elem.Id)
            face_dic[elem.Id.IntegerValue] = f.GetSubface().ComputeNormal(UV(sel_location.X,sel_location.Y))
            if elem.Id.IntegerValue in room_faces_dw.keys():
                val = room_faces_dw[elem.Id.IntegerValue]
                room_faces_dw[elem.Id.IntegerValue] = val.append(face)
            else:
                room_faces_dw[elem.Id.IntegerValue] = [face]
df_bound = pd.DataFrame()
print(count)
for id in bounds_elem:
    elem = doc.GetElement(id)
    new_row = pd.Series({'ElementId':id,
                        'Type' : elem.Name,
                        'Bounded_elemId':selectedElement.Id,
                        'Normal_to_center_room': face_dic[id.IntegerValue]})
    df_bound = pd.concat([df_bound,new_row.to_frame().T],ignore_index=True)
#print bounding elements
nameOfFile_csv = 'data\\tables\\space_elements_bounds.csv'
completename_csv =os.path.join(data_dir,nameOfFile_csv)
df_bound.to_csv(completename_csv)

# create collection of ellements passes into room-bounding-box
boundingBox = selectedElement.ClosedShell.GetBoundingBox()
offset = 0.164042 # 0.05 m
boundingBox.Min = XYZ(boundingBox.Min.X- offset, boundingBox.Min.Y- offset, boundingBox.Min.Z)
boundingBox.Max = XYZ(boundingBox.Max.X + offset, boundingBox.Max.Y + offset, boundingBox.Max.Z)

outline = Outline(boundingBox.Min,boundingBox.Max)
collection = FilteredElementCollector(doc).WherePasses(BoundingBoxIntersectsFilter(outline))
elements = collection.ToElements()  

for elem in elements:
    try:
        filter_cat = elem.Category.Name
    except:
        filter_cat = None

    if df_cat['Support'][(df_cat['English'] == filter_cat)].any():
        if not added_elements.Contains(elem.Id):
            if not (df_fur['English'] == filter_cat).any():
                elemId = find_room_from_elem_location(elem)
                if elemId != None:
                    added_elements.Add(elemId)

                if filter_cat == "Doors" or filter_cat == "Windows" and not added_elements.Contains(elem.Id):
                    if filter_cat == "Doors" and not doors_elements.Contains(elem.Id):
                        doors_elements.Add(elem.Id)
                        print(filter_cat)
                    if filter_cat == "Windows" and not windows_elements.Contains(elem.Id):
                        windows_elements.Add(elem.Id)
                    # room = elem.FromRoom
                    # if room != None:
                    #     print()
                    #     print(filter_cat)
                    #     roomId = room.Id
                    #     if room.Id.Equals(selectedElement.Id):
                    #             added_elements.Add(elem.Id)
                    #             if filter_cat == "Doors" and not doors_elements.Contains(elem.Id):
                    #                 doors_elements.Add(elem.Id)
                    #                 print(filter_cat)
                    #             if filter_cat == "Windows" and not windows_elements.Contains(elem.Id):
                    #                 windows_elements.Add(elem.Id)

            else:
                elemId = find_room_from_elem_location(elem)
                if elemId != None:
                    added_elements.Add(elemId)
                    furniture_elements.Add(elem.Id)
                else:
                    inter = find_intersection_elemToRoomSolid(elem,room_solid)
                    if inter == 1:
                        added_elements.Add(elemId)
                        furniture_elements.Add(elem.Id)

                # furn_geom = elem.get_Geometry(Options())
                # print("Furniture")
                # inter = 0
                # for f_g in furn_geom:
                #     if f_g != None and inter == 0:
                #         insGeom = f_g.GetInstanceGeometry()
                #         for instObj in insGeom:
                #             # if instObj.GetType().ToString() == "Autodesk.Revit.DB.Solid":
                #             if instObj.Faces.Size != 0 and instObj.Edges.Size != 0 and instObj.Volume > 0.0:
                #                 furn_solid = instObj
                #                 try:  
                #                     interSolid = BooleanOperationsUtils.ExecuteBooleanOperation(room_solid,furn_solid,BooleanOperationsType.Intersect)
                #                     if interSolid.Volume > 0.0000001:
                #                         print(interSolid.Volume)
                #                         inter = 1   
                #                 except:
                #                     pass                
                # if inter == 1:
                #     furniture_elements.Add(elem.Id)
                #     added_elements.Add(elem.Id)
                
# collect constraints from walls: perpendiculary, parallelity, angles, distance           
df_walls = pd.DataFrame()
df_floors = pd.DataFrame()
resultArray = IntersectionResultArray()
# check if volume of intersection/touching between walls are max
# filter for only maximum values
perpId_dic ={}
for id in face_dic.keys():
    dir = face_dic[id]
    elem = doc.GetElement(ElementId(id))
    perpId = []
    angles = []
    nearest_walls = []
    nearest_angles = []
    distances = []
    parallel_walls = []
    if abs(dir.X) == 1.0 or abs(dir.Y)==1.0 and abs(dir.Z) == 0.0:
        # we mean that is a wall
        loc_curve = elem.get_Location()
        curve = loc_curve.Curve
        start_point = curve.GetEndPoint(0)
        end_point = curve.GetEndPoint(1)
        direction = Line.CreateBound(start_point,end_point).Direction
        line = Line.CreateUnbound(start_point,direction)
        vec_1 = end_point.Subtract(start_point).Normalize()
        width_1 = elem.Width
        # perpId = []
        # angles = []
        # nearest_walls = []
        # nearest_angles = []
        # distances = []
        # parallel_walls = []
        for id_temp in face_dic.keys():
            dir_temp = face_dic[id_temp]
            if id != id_temp and (abs(dir_temp.X) == 1.0 or abs(dir_temp.Y)==1.0) and abs(dir_temp.Z)==0.0:
                elem_an = doc.GetElement(ElementId(id_temp))
                # print(id_temp)
                loc_curve_an = elem_an.Location
                curve_an = loc_curve_an.Curve
                start_point_an = curve_an.GetEndPoint(0)
                end_point_an = curve_an.GetEndPoint(1)
                direction_an = Line.CreateBound(start_point_an,end_point_an).Direction
                line_an = Line.CreateUnbound(start_point_an,direction_an)
                vec_2 = end_point_an.Subtract(start_point_an).Normalize()
                inter = curve.Intersect(curve_an)
                # print(inter)
                width_2 = elem_an.Width
                angle = round(vec_1.AngleTo(vec_2)*180/np.pi)
                if inter == SetComparisonResult.Overlap:
                    # check if walls are perpendicular 
                    distances.append(None)
                    parallel_walls.append(None)
                    if angle == 90 or angle == 0:
                        angles.append(90)
                        perpId.append(id_temp)
                        nearest_walls.append(id_temp)
                    else:
                        angles.append(angle)
                        perpId.append(None)
                        nearest_walls.append(None)
                if inter == SetComparisonResult.Disjoint:
                    # means that walls are disjoint!
                    # check if walls perpendicular
                    if line.Intersect(line_an) == SetComparisonResult.Overlap:
                        distances.append(None)
                        parallel_walls.append(None)
                        if angle == 90 or angle == 0:
                            angles.append(90)
                            perpId.append(id_temp)
                            nearest_walls.append(id_temp)
                        else:
                            angles.append(angle)
                            perpId.append(None)
                            nearest_walls.append(id_temp)
                    else:
                        if angle == 0 or angle == 180:
                            # parallel
                            angles.append(0)
                            distance = round((line.Project(start_point_an).Distance - width_1/2 - width_2/2)*0.3048,3)
                            distances.append(distance)
                            perpId.append(None)
                            nearest_walls.append(None)
                            parallel_walls.append(id_temp)
                        elif angle == 90:
                            #perpendicular
                            angles.append(90)
                            distances.append(None)
                            perpId.append(id_temp)
                            nearest_walls.append(None)
                            parallel_walls.append(None)
                        else:
                            # not parallel or perpendicular
                            angles.append(angle)
                            distances.append(None)
                            perpId.append(None)
                            nearest_walls.append(id_temp)
                            parallel_walls.append(None)
            elif id != id_temp and abs(dir_temp.Z) == 1 and abs(dir_temp.X) == 0.0 and abs(dir_temp.Y) == 0.0:
                # means that walls are perpendicular to the floor
                angles.append(90)
                distances.append(None)
                perpId.append(id_temp)
                nearest_walls.append(None)
                parallel_walls.append(None)
        
        perpId_dic[id] = perpId
                            
        new_row_walls = pd.Series({'ElementId': id,
                            'Perpendicular_walls_id':perpId,
                            'Parallel_walls_id':parallel_walls,
                            'Distance_to_parall':distances,
                            'Nearest_walls_id':nearest_walls,
                            'Angles_to_walls':angles})
        df_walls = pd.concat([df_walls,new_row_walls.to_frame().T],ignore_index= True)

# write walls into dataframe
nameOfFile_csv = 'data\\tables\\space_elements_walls.csv'
completename_csv =os.path.join(data_dir,nameOfFile_csv)
df_walls.to_csv(completename_csv)

# collect constraints from floors: parallelity!, angles?, distance!         
df_floors = pd.DataFrame()
resultArray = IntersectionResultArray()
floor_distance = {}
for id in face_dic.keys():
    dir = face_dic[id]
    elem = doc.GetElement(ElementId(id))
    if abs(dir.Z) == 1.0 and dir.X == 0.0 and dir.Y == 0.0:
        # print(elem)
        elem_geom = elem.get_Geometry(Options())
        for geomInst in elem_geom:
            if geomInst.Faces.Size != 0 and geomInst.Edges.Size != 0:
                    floor_solid = geomInst
                    for face in floor_solid.Faces:
                        normal = face.ComputeNormal(UV(sel_location.X,sel_location.Y))
                        if abs(normal.Z)==1:
                            dis = face.Project(sel_location).Distance
                            floor_distance[id] = [dir.Z,dis]
                            break

distance_between_floors = {}
for id in floor_distance.keys():
    val = floor_distance[id]
    dir = val[0]
    dis_to_room = val[1]
    for id_t in floor_distance.keys():
        if id_t != id:
            val_t = floor_distance[id_t]
            dir_t = val_t[0]
            dis_to_room_t = val_t[1]
            if dir != dir_t:
                distance = dis_to_room + dis_to_room_t
                # print(distance)
                
                distance_between_floors[distance] = [id,id_t]
            new_row_floors = pd.Series({'ElementId': id,
                                        'Parallel_floor_id':id_t,
                                        'Distance_to_parall':distance})
            df_floors = pd.concat([df_floors,new_row_floors.to_frame().T],ignore_index= True)

#distance between floors or ceilings
nameOfFile_csv = 'data\\tables\\space_elements_floors.csv'
completename_csv =os.path.join(data_dir,nameOfFile_csv)
df_floors.to_csv(completename_csv)

# collect constraints from doors: distance to edges (floor, wall), width, hight
df_doors = pd.DataFrame()
doors_wh = {}
distance_dic = {}
for id in doors_elements:
    door = doc.GetElement(id)
    wall = door.Host
    width = wall.Width
    id_wall = wall.Id
    cut_loop = None
    dir = face_dic[id_wall.IntegerValue]
    try:
        cut_loop = ExporterIFCUtils.GetInstanceCutoutFromWall(doc, wall, door, dir)[0]
    except:
        print(door.Name)
        cuts = get_opening_cut(door,wall,dir,selectedElement)
        for cut_loop in cuts:
            # print(cut_loop.GetRectangularHeight())
            print(cut_loop.NumberOfCurves())
        pass
    perp_elem = perpId_dic[id_wall.IntegerValue]
    print(perp_elem)
    closest_dis = []
    for id_el in perp_elem:
        if id_el != None:
            elem = doc.GetElement(ElementId(id_el))
            if cut_loop != None:
                if face_dic[id_el].Z == 0.0:
                    for curve in cut_loop:
                        dir_c = Line.CreateBound(curve.GetEndPoint(0),curve.GetEndPoint(1)).Direction
                        line = Line.CreateUnbound(curve.GetEndPoint(0),dir_c)
                        # try:
                        if abs(dir_c.Z) == 1.0:
                            width_p = elem.Width
                            loc_elem = elem.Location.Curve
                            point_list = List[ClosestPointsPairBetweenTwoCurves]()
                            closest_pnt = curve.ComputeClosestPoints(loc_elem, False, False,False,point_list)
                            for points in closest_pnt:
                                first_point = points.XYZPointOnFirstCurve
                                second_point = points.XYZPointOnSecondCurve
                                dis_to_cut = round(first_point.DistanceTo(second_point)*0.3048 - width_p/2*0.3048,2)
                                closest_dis.append(dis_to_cut)
                        # except:
                        #     pass
    print("Distance: ")
    print(closest_dis)
    distance_dic[id] = closest_dis
    dType = doc.GetElement(door.GetTypeId())
    width = dType.get_Parameter(BuiltInParameter.DOOR_WIDTH).AsDouble() 
    height = dType.get_Parameter(BuiltInParameter.DOOR_HEIGHT).AsDouble()
    print(width, height)
    doors_wh[id] = [width,height]
    new_row_doors = pd.Series({'ElementId': id,
                            'Door_width':width,
                            'Door_height':height,
                            'Distance_to_edges':distance_dic[id]})
    df_doors = pd.concat([df_doors,new_row_doors.to_frame().T],ignore_index= True)
                            
#distance between floors or ceilings
nameOfFile_csv = 'data\\tables\\space_elements_doors.csv'
completename_csv =os.path.join(data_dir,nameOfFile_csv)
df_doors.to_csv(completename_csv)                        
# print(dist_to_faces)

#collect constraints from windows: distance to edges (floor, wall), width, hight
# for id in windows_elements:
#     print(id)
            
            
# analyse furniture, calculate nearest furniture
# not sure that code below is usefull
df_furn_dist = pd.DataFrame()
i = 0
for id in furniture_elements:
    elem = doc.GetElement(id)
    location_point = elem.Location.Point
    nearest_elem = []
    distance = []
    nearest_elem_dict = {}
    nearest_elem_dict['ElementId'] = id
    n = 0
    for b_id in bounds_elem:
        b_elem = doc.GetElement(b_id)
        b_geom = b_elem.get_Geometry(Options())
        b_elem_cat = b_elem.Category.Name
        for solid in b_geom:
            if solid.GetType().ToString() == "Autodesk.Revit.DB.Solid":
                for face in solid.Faces:
                    projection = face.Project(location_point)
                    if projection != None:
                        normal = face.ComputeNormal(UV(location_point.X,location_point.Y))
                        if b_elem_cat == "Floors" and normal.Z == -1.0:
                            # dist_dic[b_id] = projection.Distance
                            nearest_elem_dict['Nearest_elem_id_'f'{n}'] = b_id
                            nearest_elem_dict['Distance_to_nearest_'f'{n}'] = projection.Distance
                            # nearest_elem.append(b_id)
                            # distance.append(projection.Distance)
                            n = n + 1

                        if b_elem_cat == "Walls" and (normal.X == -1.0 or normal.Y == -1.0):
                            # nearest_elem.append(b_id)
                            # distance.append(projection.Distance)
                            nearest_elem_dict['Nearest_elem_id_'f'{n}'] = b_id
                            nearest_elem_dict['Distance_to_nearest_'f'{n}'] = projection.Distance
                            n = n + 1

    new_row = pd.Series(nearest_elem_dict)
    df_furn_dist = pd.concat([df_furn_dist,new_row.to_frame().T],ignore_index= True)

# write furn into dataframe
nameOfFile_csv = 'data\\tables\\space_elements_furniture.csv'
completename_csv =os.path.join(data_dir,nameOfFile_csv)
df_furn_dist.to_csv(completename_csv)

# for id in added_elements:
#     # print(id)
#     elem = doc.GetElement(id)
#     try:

#         dep_el = elem.FindInserts(True,True,True,True)
#         for d in dep_el:
#             if added_elements.Contains(d):
#                 # recognise windows and door which belongs to the room
#                 print("Connections between wall and door/window")
#                 print(str(id) + ":" + str(d))
#     except:
#         pass
    # find connections between walls
    # try:
    #     location = elem.Location
    #     elem_join = location.get_ElementsAtJoin(0) #connections on the start point
    #     for e in elem_join:
    #         if added_elements.Contains(e.Id):
    #             print("connections in the beginnig of the wall")
    #             print(str(id) + ":" + str(e.Id))
    # except:
    #     pass
    # # find connections between walls
    # try:
    #     location = elem.Location
    #     elem_join = location.get_ElementsAtJoin(1) #connections on the end point
    #     for e in elem_join:
    #         if added_elements.Contains(e.Id):
    #             print("connections in the end of the wall")
    #             print(str(id) + ":" + str(e.Id))
    #     # after finding adjacent walls check if the walls are perpendicular to each other 
    #     # here find destination curve with Location.Curve.Derivative(add specific point on curve)
    # except:
    #     pass


# write all in dataframe
for id in added_elements:

    elem = doc.GetElement(id)
    try:
            eId = elem.GetTypeId()
            elemType = doc.GetElement(eId)
            if elemType != None:
                fam_name = elemType.FamilyName
    except:
        fam_name = elem.Symbol.Family.Name
    new_row = pd.Series({'Selected_roomI_uniqueId':selectedElement.UniqueId,
                                    'Selected_roomI_Id': selectedElement.Id,
                                    'UniqueId':elem.UniqueId,
                                    'ElementId': elem.Id,
                                    'Family':fam_name,
                                    'Typ':elem.Name,
                                    'Category':elem.Category.Name,
                                    'LevelId': elem.LevelId})
    df = pd.concat([df,new_row.to_frame().T],ignore_index= True)

# print space elements
nameOfFile = 'data\\tables\\space_elements.xlsx'
nameOfFile_csv = 'data\\tables\\space_elements.csv'
completename_csv =os.path.join(data_dir,nameOfFile_csv)
df.to_csv(completename_csv)


df_sum = pd.DataFrame()
print('####### ROOM REPORT ######')
print(df['Category'].value_counts())
print("Number of doors:" + str(df_doors.shape[0]))
print(df_doors.agg({'Door_width':['mean','min','max'],'Door_height':['mean','min','max']}))
print("Number of floors:" + str(df_floors.shape[0]))
print(df_floors.agg({'Distance_to_parall':['count','mean','min','max']}))
t.Commit()