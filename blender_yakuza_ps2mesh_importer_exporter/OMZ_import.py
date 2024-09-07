import bpy
from mathutils import *
from .binary_reader import BinaryReader 
import time
import bmesh

def import_omz(context, filepath, omz_orient):
    
    time_start = time.time()
    
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
    
    for OMZS in range (OMZCount):
        reader.seek(OMZPointers[OMZS])
        
        if reader.read_str(3) != 'OMZ':
            print("File is invalid lole")
            raise Exception("Breaking op, file has invalid header")
        else:
            print("File is valid")
            
        
        unk = reader.read_bytes(5)
        UNKChunkExist = reader.read_uint32()
        if UNKChunkExist == 1:
            pad0 = reader.read_bytes(16)
            UnkownChunkCount = reader.read_uint32()
            pad0 = reader.read_bytes(12)
            unkchunk = reader.read_bytes(UnkownChunkCount*32)
            
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
        
        for v in range (VertexNum):
            VX = reader.read_float()        
            VY = reader.read_float()
            VZ = reader.read_float()
            
            if omz_orient == True:
                Vertices.append ((-VX,-VZ,VY))
                print(v,"",VX,VY,VZ)
            else:
                Vertices.append ((VX,VY,VZ))
                print(v,"",VX,VY,VZ)
                
            reader.seek ((VertexOffset) + (v+1)*32)
            
        reader.seek (NormalOffset)
        for n in range (VertexNum):
            NX = reader.read_float()
            NY = reader.read_float()
            NZ = reader.read_float()
            
            if omz_orient == True:
                Normals.append ((-NX,-NZ,NY))
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
            
        reader.seek (FacesOffset)
        for f in range (BoneFaceNum):
            F1 = reader.read_int16()
            F2 = reader.read_int16()
            F3 = reader.read_int16()
            
            Faces.append ((F1,F2,F3))
            
            print(f,"",F1,F2,F3)
            reader.seek ((FacesOffset) + (f+1)*32)
            
        OMZNAME = "OMZ"
        OMZMESH = bpy.data.meshes.new(OMZNAME) #(f"{OMZNAME}_Mesh")
        OMZMESH.from_pydata(Vertices,[],Faces)
        
        obj = bpy.data.objects.new(f"{OMZNAME}_Object",OMZMESH)
        bpy.context.collection.objects.link(obj)
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

        print("My Script Finished: %.4f sec" % (time.time() - time_start))
        
    OMZ.close()
    return {'FINISHED'} 