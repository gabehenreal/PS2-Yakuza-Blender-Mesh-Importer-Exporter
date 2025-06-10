import bpy
from mathutils import *
from .binary_reader import BinaryReader
from collections import defaultdict
import math 
import time

def export_omz(context,filepath,ParentBone,FlowVal,DampVal,Armature,CollisionObj,UseOldConsts,self):
    time_start = time.time()
    activeobj=bpy.context.active_object
    activemesh=activeobj.data
    Vertices = [v.co for v in activemesh.vertices]
    Normals = [v.normal for v in activemesh.vertices]
    Faces = []
    FaceMidpoint = []
    """
    UVs = []
    UVLAYER= activemesh.uv_layers.active.data   
    for uvo in activemesh.loops:
        UVs.append(UVLAYER[uvo.index].uv)
    """
    
    uvb = []        

    #https://blender.stackexchange.com/questions/30677/get-set-coordinates-for-uv-vertices-using-python
    for face in activemesh.polygons:
        for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
            uv_coords = activemesh.uv_layers.active.data[loop_idx].uv
            uvb.append([vert_idx, uv_coords.x, uv_coords.y])       

    uv_ref_index = []
    UVs = []
    for v in activemesh.vertices :
        i = (v.index)          
        for j in uvb:
            if i == j[0] and j[0] not in uv_ref_index:
                uv_ref_index.append(j[0])
                UVs.append( [j[1],j[2]] )     
    #print("length: ",len(UVs),"vert:", len(Vertices))
                    
    FaceCount = activemesh.calc_loop_triangles()
    for tri in (activemesh.loop_triangles):
        Faces.append(tri.vertices[:])
    

    Weights = []
    for v in activemesh.vertices:
        if len(v.groups) == 0:
            Weights.append(0)
        else:
            mesh_weight_group = []
            mesh_weight_value = []
            for g in v.groups:               
                mesh_weight_group.append(g.group)
                mesh_weight_value.append(g.weight)
                break
                    
            vg1 = 0
            vgw1 = 0            
                    
            if len(mesh_weight_group) >= 1:
                vg1 = mesh_weight_group[0]
                vgw1 = float(mesh_weight_value[0])
                if vgw1 > 0:
                    vgw1 = 1
                    Weights.append(vgw1)
                else:
                    vgw1 = 0
                    Weights.append(vgw1)
            else:
                vg1 = 0
                vgw1 =0  
                Weights.append(vgw1)

    print(len(Weights),Weights)
    for tri in (activemesh.loop_triangles):
        V1 = tri.vertices[0]
        V2 = tri.vertices[1]
        V3 = tri.vertices[2]
        VRT1 = activemesh.vertices[V1].co
        VRT2 = activemesh.vertices[V2].co
        VRT3 = activemesh.vertices[V3].co
        Midpoint = (VRT1+VRT2+VRT3)/3.0
        FaceMidpoint.append(Midpoint)
    #print(FaceMidpoint)
    
    BoneInfo = []

    #CollisionObj = bpy.data.objects["OMZ_Const_COL"]
    for bone in CollisionObj.pose.bones:
        BoneOrigin = bone.matrix.translation
        for constraint in bone.constraints:
            if constraint.type == 'COPY_ROTATION':
                ParentBoneAmtName = constraint.subtarget
        ParentBoneAmt = Armature.pose.bones[ParentBoneAmtName]
        BoneAmtOrigin = ParentBoneAmt.matrix.translation
        RelativeLoc =   BoneOrigin - BoneAmtOrigin
        HeadLoc = Armature.matrix_world @ bone.head
        TailLoc = Armature.matrix_world @ bone.tail
        Radius = (HeadLoc - TailLoc).length

        BoneInfo.append((RelativeLoc.x*-1,RelativeLoc.z,RelativeLoc.y,Radius,int(ParentBoneAmtName)))
    GroupedConsts = defaultdict(list)
    for constraint in BoneInfo:
        GroupedConsts[constraint[4]].append(constraint)

    Consts = []
    for boneInx,group in GroupedConsts.items():
        while True:
            if len(group)%2 != 0:
                group.append((0,0,0,0,boneInx))
            else:
                for const in group:
                    Consts.append(const)
                break
    Consts.sort(key=lambda x:x[4])
    print(Consts)
    
    OMZ_data = open(filepath, 'rb')
    reader = BinaryReader(OMZ_data.read())
    reader.seek(4)
    count = reader.read_uint32()
    oldbytes = ""
    if count == 1:
        reader.seek(0)
        oldbytes = reader.read_bytes(60)
        OMZ_data.close()
    else:
        OMZ_data.close()
        raise Exception("Export of multi-mesh OMZs are not supported yet!")
      
    writer = BinaryReader()
    writer.write_bytes(oldbytes)
    writer.seek(28)
    if UseOldConsts == False:
        writer.write_uint16(int(FlowVal))
        writer.write_uint16(int(DampVal))
    writer.seek(44)
    writer.write_uint32(len(Consts))
    writer.seek(60)
    
    for info in Consts:
        writer.write_float(info[0]*(-1))
        writer.write_float(info[1])
        writer.write_float(info[2])
        writer.write_float(info[3])
        writer.write_uint32(info[4])
        writer.pad(12)
    writer.write_uint32(len(Faces))

    
    for wrtef in range(len(Faces)):
        writer.write_float((FaceMidpoint[wrtef][0]))
        writer.write_float(FaceMidpoint[wrtef][2])
        writer.write_float(FaceMidpoint[wrtef][1])
        writer.write_uint16(Faces[wrtef][0])
        writer.write_uint16(Faces[wrtef][2])
        writer.write_uint32(Faces[wrtef][1])
        writer.write_uint32(2)
        writer.pad(0x4)## set to 4 because theres anchor flag

        writer.write_uint8(Weights[Faces[wrtef][0]])
        writer.write_uint8(Weights[Faces[wrtef][2]])
        writer.write_uint8(Weights[Faces[wrtef][1]])
        writer.write_uint8(0)
        
        
    writer.write_uint32(len(Vertices))
    for wrte in range(len(Vertices)):
        writer.write_float(Vertices[wrte][0])
        writer.write_float(Vertices[wrte][2])
        writer.write_float(Vertices[wrte][1])
        writer.write_float(Normals[wrte][0])
        writer.write_float(Normals[wrte][2])
        writer.write_float(Normals[wrte][1])
        writer.write_float(UVs[wrte][0])
        writer.write_float(1-(UVs[wrte][1]))
        
    writer.pad(0x8)
    writer.write_uint32(int(ParentBone))
    writer.pad(0x104)
    FileSize = writer.pos()
    writer.seek(8)
    writer.write_uint32(FileSize)
    OMZ = open(filepath, 'wb')
    OMZ.write(writer.buffer())
    OMZ.close()
    
    self.report({'INFO'}, "OMZ Export Finished in %.4f sec" % (time.time() - time_start))   
    return {'FINISHED'}