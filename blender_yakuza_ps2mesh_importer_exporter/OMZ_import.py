import bpy
from mathutils import *
from .binary_reader import BinaryReader 
import time
import bmesh

def import_omz(context, filepath, omz_orient,OMZPARENT):
    
    time_start = time.time()
    
    if OMZPARENT:   
        activeobj = bpy.context.active_object

    print("running OMZ_import...")
    OMZ = open(filepath, 'rb')
    reader = BinaryReader(OMZ.read())
    
    reader.seek(4,0)
    OMZCount = reader.read_uint32()
    OMZPointers = []
    for omzs in range (OMZCount):
        OMZSize = reader.read_uint32()
        OMZPointer = reader.read_uint32()
        OMZPointers.append(OMZPointer)
        
    new_collection = bpy.data.collections.new('OMZ_collection')
    bpy.context.scene.collection.children.link(new_collection)
    
    for OMZS in range (OMZCount):
        reader.seek(OMZPointers[OMZS])
        
        if reader.read_str(3) != 'OMZ':
            print("File is invalid lole")
            raise Exception("Breaking op, file has invalid header")
        else:
            print("File is valid")
            
        
        unk = reader.read_bytes(5)
        UNKChunkExist = reader.read_uint32()
        constinfo = []
        if UNKChunkExist == 1:
            flow = reader.read_uint16() # actually treated like a uint8
            damp = reader.read_uint16() # actually treated like a uint8
            pad0 = reader.read_bytes(12)
            UnkownChunkCount = reader.read_uint32() ## constraint count
            pad0 = reader.read_bytes(12)
            for i in range(UnkownChunkCount):
                posx = reader.read_float()
                posy = reader.read_float()
                posz = reader.read_float()
                radius = reader.read_float()
                parentinx = reader.read_uint32()
                pad0 = reader.read_bytes(12)
                if OMZPARENT == True:
                    
                    Bone = activeobj.pose.bones[parentinx]
                    BoneMatrix = activeobj.matrix_world @ Bone.matrix
                    BoneOrigin = BoneMatrix.translation
                    NewPos = BoneOrigin + Vector((posx,posz,posy))
                    constinfo.append((NewPos.x,NewPos.y,NewPos.z,radius,parentinx))
                else:
                    constinfo.append((posx,posz,posy,radius,parentinx))
            
        BoneFaceNum = reader.read_uint32()
        CPOS1 = reader.pos()
        pad1 = reader.read_bytes(12)
        FacesOffset = reader.pos()
        reader.seek(CPOS1)
        SkipFace = reader.read_bytes(BoneFaceNum*32)
        
        VertexNum = reader.read_uint32()
        
        VertexOffset = reader.pos()
        NormalOffset = (VertexOffset + 12)
        UVsOffset = (NormalOffset + 12)
        
        
        reader.seek (VertexOffset)
        
        Vertices = []
        Normals = []       
        UVs = []        
        Faces = []
        Pins = []

        for v in range (VertexNum):
            VX = reader.read_float()        
            VY = reader.read_float()
            VZ = reader.read_float()
            
            if omz_orient == True:
                Vertices.append ((VX,VZ,VY))
                
            else:
                Vertices.append ((VX,VY,VZ))
                
                
            reader.seek ((VertexOffset) + (v+1)*32)
            
        reader.seek (NormalOffset)
        for n in range (VertexNum):
            NX = reader.read_float()
            NY = reader.read_float()
            NZ = reader.read_float()
            
            if omz_orient == True:
                Normals.append ((NX,NZ,NY))
            else:
                Normals.append ((NX,NY,NZ))                
            
            reader.seek ((NormalOffset) + (n+1)*32)
            
        reader.seek (UVsOffset)
        for uv in range(VertexNum):
            U = reader.read_float()
            V = reader.read_float()
            VF = (1 - V)
            
            if omz_orient == True:
                UVs.append ((U,VF))
            else:
                UVs.append ((U,V))
            
            reader.seek ((UVsOffset) + (uv+1)*32)
        
        reader.seek(VertexOffset+(VertexNum*32)+8)
        ParentBone = reader.read_uint32()
        print(ParentBone)
        
        reader.seek (FacesOffset)
        for f in range (BoneFaceNum):
            F1 = reader.read_int16()
            F2 = reader.read_int16()
            F3 = reader.read_int16()
            reader.read_bytes(10)
            Pin1 = reader.read_uint8()
            Pin2 = reader.read_uint8()
            Pin3 = reader.read_uint8()
            
            Pins.append((Pin1,F1))
            Pins.append((Pin2,F2))
            Pins.append((Pin3,F3))

            Faces.append ((F1,F2,F3))
            
            reader.seek ((FacesOffset) + (f+1)*32)
        

        OMZNAME = "OMZ"
        OMZMESH = bpy.data.meshes.new(OMZNAME) #(f"{OMZNAME}_Mesh")
        OMZMESH.from_pydata(Vertices,[],Faces)
        
        obj = bpy.data.objects.new(f"{OMZNAME}_Object",OMZMESH)
        new_collection.objects.link(obj)
        OMZMESH.update()
        bm = bmesh.new()
        bm.from_mesh(OMZMESH)
        bm_faces = bm.faces
        uv_verify = bm.loops.layers.uv.verify()
        ff = 0 
        
        for bm_face in bm_faces:
            bm_idx = bm_face.index
            uv_idx_tup = Faces[bm_idx]
        
            loop_idx = 0
            face_loops = bm_face.loops                        
           
            for bm_loop in face_loops:
                loop_uv_layer = bm_loop[uv_verify]
                uv_idx = uv_idx_tup[loop_idx]

                loop_uv_layer.uv = UVs[uv_idx]
                loop_idx = loop_idx + 1
                bm_face.smooth = True             
            
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        
        bm.verts.ensure_lookup_table()

        bm.to_mesh(OMZMESH)
        bm.free()
        
        VertGroup1 = obj.vertex_groups.new(name="OMZ Pin")
        if UNKChunkExist == 1:
            VertGroup2 = obj.vertex_groups.new(name="OMZ Flow Weight")
            VertGroup3 = obj.vertex_groups.new(name="OMZ Damp Weight")
        for pin,vert in Pins:
            VertGroup1.add([vert],weight=(float(pin)),type='REPLACE')
            if UNKChunkExist == 1:
                VertGroup2.add([vert],weight=(float(flow/255)),type='REPLACE')        
                VertGroup3.add([vert],weight=(float(damp/255)),type='REPLACE')
            obj.data.update()


        OMZMESH.normals_split_custom_set([(0, 0, 0) for l in OMZMESH.loops])

        increase = 0
        normals = []
        count = 0
        for vnn in OMZMESH.vertices:
            
            if vnn == OMZMESH.vertices[count]:
                normals.append(Normals[count])
            else:
                normals.append(vnn.normal)
   
            count_up_count = 1
            count += count_up_count
       
        OMZMESH.normals_split_custom_set_from_vertices(normals)
        
        increase += 1
        if OMZPARENT == True:
            Bone = activeobj.pose.bones[ParentBone]
            BoneMatrix = activeobj.matrix_world @ Bone.matrix
            BoneOrigin = BoneMatrix.translation
            obj.location = BoneOrigin
        
        if UNKChunkExist == 1:
            amt_name = "OMZ_Const_COL_" + str(OMZS)
            amt = bpy.data.armatures.new(amt_name)
            amt_object = bpy.data.objects.new(amt_name, amt)
            new_collection.objects.link(amt_object)

            bpy.context.view_layer.objects.active = amt_object
            current_arm_name = amt_object.name
                
            for i in range(UnkownChunkCount):
                bpy.ops.object.mode_set(mode='EDIT')
                bone = amt.edit_bones.new(str(i))
                bone.head = (constinfo[i][0],constinfo[i][1],constinfo[i][2])
                bone.tail = (constinfo[i][0],constinfo[i][1] + constinfo[i][3],constinfo[i][2])
                bpy.ops.object.mode_set(mode='OBJECT')
            
            if OMZPARENT == True:
                for bone in amt_object.pose.bones:
                    Bone2 = activeobj.pose.bones[constinfo[int(bone.name)][4]]
                    copy = bone.constraints.new(type='COPY_ROTATION')
                    copy.target = activeobj
                    copy.subtarget = Bone2.name


    print("OMZ Import Finished: %.4f sec" % (time.time() - time_start))
        
    OMZ.close()
    return {'FINISHED'}