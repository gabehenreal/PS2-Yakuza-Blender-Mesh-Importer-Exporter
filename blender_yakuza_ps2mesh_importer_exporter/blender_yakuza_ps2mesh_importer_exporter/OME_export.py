import bpy
from mathutils import *
from .binary_reader import BinaryReader 
import time
    
def export_ome(context, filepath, self):

    time_start = time.time()
    def retrive_mesh_data_from_blender(me):
    
        face_og = []       
        for f in me.polygons:
            if f.loop_total != 3:
                print(f.loop_total)
                raise Exception("Model has polygons that are not triangles!")
            else:
                g = [f.vertices[0],f.vertices[1],f.vertices[2]] 
                face_og.append(g)   
  
        face_len = len(face_og)    
        limito = face_len-1
        exported_face_index = []
        previous_was_dead = False

        for face in range(face_len): 
        
            if face == 0:               
                face0 = face_og[face]
                exported_face_index.append(face0[0])
                exported_face_index.append(face0[1])
                exported_face_index.append(face0[2])                
                face_og.remove(face0)   ## remove this face from the list
                
            else:                    
                prev_face2 = exported_face_index[-2]
                prev_face1 = exported_face_index[-1]   
                
                for n in face_og:                       
                    newface = n
                        
                    if prev_face2 in newface and prev_face1 in newface:                           
                        ## find index   
                        inx1 = newface.index(prev_face2)
                        inx2 = newface.index(prev_face1)        

                        ### get index of leftover element
                        inx3 = 3 - (inx1+inx2)                            
                        elem3 = newface[inx3]                    
                        exported_face_index.append(elem3)
                            
                        ## remove index of this 
                        face_og.remove(n)                   
                        previous_was_dead = False                    
                        break
                            
                    else:
                        previous_was_dead = True
                            
                if previous_was_dead == True:                    
                    newdeadface = face_og[0]            
                    
                    exported_face_index.append(prev_face1)
                    exported_face_index.append(newdeadface[0])
                    exported_face_index.append(newdeadface[0])              
                    
                    exported_face_index.append(newdeadface[0])
                    exported_face_index.append(newdeadface[1])
                    exported_face_index.append(newdeadface[2])  
                    
                    face_og.remove(newdeadface)            
                    previous_was_dead = False 
        uvb = []        

        #https://blender.stackexchange.com/questions/30677/get-set-coordinates-for-uv-vertices-using-python
        for face in me.polygons:
            for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                uv_coords = me.uv_layers.active.data[loop_idx].uv
                uvb.append([vert_idx, uv_coords.x, uv_coords.y])       

        uv_ref_index = []
        uv_vert = []
        for v in me.vertices :
            i = (v.index)          
            for j in uvb:
                if i == j[0] and j[0] not in uv_ref_index:
                    uv_ref_index.append(j[0])
                    uv_vert.append( [j[1],j[2]] )            

        verts = []
        vert_normals = []
        vert_uv = []
        vert_weights = []
        vert_weight_indices = []
        uv_inc = 0
        loop_inx = 0
        
        vertex_normals = [[] for v in me.vertices]
        for poly in me.polygons:
            for loop_index in poly.loop_indices:
                loop = me.loops[loop_index]
                v_index = loop.vertex_index
                if loop.normal not in vertex_normals[v_index]:
                    vertex_normals[v_index].append(loop.normal)

        for v in me.vertices:
            v1,v2,v3 = float(v.co[0]) ,float(v.co[1]) ,float(v.co[2])   
            verts.append([v1,v2,v3])
           
            mesh_weight_group = []
            mesh_weight_value = []
            for g in v.groups:    
                mesh_weight_group.append(g.group)
                mesh_weight_value.append(g.weight)
                
            vg1,vg2 = 0,0
            vgw1,vgw2 = 0,0        
                
            if len(mesh_weight_group) >=2 :
                max_w1 = max(mesh_weight_value)
                max_w1_inx =  mesh_weight_value.index(max_w1)
                vg1 = mesh_weight_group[max_w1_inx]
                
                mesh_weight_value.pop(max_w1_inx)
                mesh_weight_group.pop(max_w1_inx)
                
                max_w2 = max(mesh_weight_value)
                max_w2_inx =  mesh_weight_value.index(max_w2)
                vg2 = mesh_weight_group[max_w2_inx]
                
                vgw1,vgw2 =float(max_w1),float(1 - max_w1)     
                
            elif len(mesh_weight_group) < 2 and len(mesh_weight_group) != 0 :
                vg1,vg2 = mesh_weight_group[0], 0
                vgw1,vgw2 =float(mesh_weight_value[0]),float(1 - mesh_weight_value[0])  
                
            else:
                vg1,vg2 = 0, 0
                vgw1,vgw2 =float(1),float(0) 
                #vg1,vg2 = mesh_weight_group[0], 0
                #vgw1,vgw2 =float(mesh_weight_value[0]),float(1 - mesh_weight_value[0])   
                
            vert_weights.append([vgw1,vgw2])
            vert_weight_indices.append([vg1,vg2])
                
            #vn1,vn2,vn3 = float(v.normal[0]),float(v.normal[1]),float(v.normal[2])
            vert_normals.append( [float( vertex_normals[loop_inx][0][0] ),float( vertex_normals[loop_inx][0][1] ),float( vertex_normals[loop_inx][0][2] )] )
                
            uv1x,uv1y = float(uv_vert[uv_inc][0]),float(uv_vert[uv_inc][1])   
            vert_uv.append([uv1x,uv1y])
            uv_inc+=1            
            loop_inx += 1
        return verts,vert_weights ,vert_weight_indices ,vert_normals, vert_uv ,exported_face_index
    
    def identify_and_get_ome_data(filepath):   
        ##
        # Identifies the type of the ome file
        # If the type is correct, copy necessary data from it
        # Should also work as a first line of defence from data mismatch etc
        ##        
        
        OME_data =  open(filepath, 'rb')
        reader = BinaryReader(OME_data.read())
        
        if reader.read_str(3) != 'OME':
            print("EXPORT: File is invalid")
            raise Exception("Halting file export, file has invalid header")
        else:
            print("EXPORT: File is valid")
        
        reader.seek(8,0)
        obdp_pointer = reader.read_uint16()     ## ODBP table loc

        reader.seek(obdp_pointer,0)
        if (reader.read_str(4)) != "ODBP":
            if (reader.read_str(4)) != "MDBP":
                print("EXPORT: File is invalid")
                raise Exception("EXPORT: File is invalid, Unsupported version (expected ODBP, not MDBP)!!!")
                
            else:
                print("File is invalid")
                raise Exception("EXPORT: File is invalid, Invalid sub header!!!")       
        else:
            print("EXPORT: File is valid")
    
        reader.seek(obdp_pointer + 36 ,0)
        mesh_count = reader.read_uint16()  
        
        ### check also if the vert table is 40 byte one, this tends to overlook it
        if mesh_count == 1:
            pass
        else:
            raise Exception("EXPORT: Export of multiple meshes is not supported yet!")
            
        reader.seek(obdp_pointer + 12 ,0)    
        f_size_offset = reader.pos()
        filesize_offset = reader.read_uint32()
        
        reader.seek(obdp_pointer + 128 ,0)       
        vertex_offset = reader.read_uint32()
        v_table_offset = reader.pos()
        
        end_of_file_offset = reader.read_uint32()
        
        reader.seek(obdp_pointer + 32 + vertex_offset + 12,0)
        v_data_offset = reader.pos()
        
        vertex_count = reader.read_uint32() 
        face_pointer = reader.read_uint32() 
        face_count = reader.read_uint32() 
        dummy = reader.read_uint64() 
        
        verttabletotalsize = (face_pointer+32) - (vertex_offset+64 )
        verttbalesize = verttabletotalsize/vertex_count
        if verttbalesize != 40:
            raise Exception(f"EXPORT: Unsupported export type for vertex row size {verttbalesize}")
        
        ### then 8 bytes of 0s
        ## now to copy data
        
        test1 = reader.pos() 
        print(test1)
        reader.seek(0,0)
        data1 = reader.read_bytes(test1)
        print(len(data1))
        
        reader.seek(obdp_pointer + 32 +end_of_file_offset,0)
        
        print(filesize_offset,end_of_file_offset,filesize_offset - end_of_file_offset)
        
        print(reader.pos())
        end_data = reader.read_bytes(20)#( filesize_offset - end_of_file_offset )
        
        OME_data.close()       
        return data1,end_data,f_size_offset,v_table_offset,v_data_offset,obdp_pointer 
        
        
    def write_to_file(  filepath,
                        data1,
                        end_data,
                        f_size_offset,
                        v_table_offset,
                        v_data_offset,
                        obdp_pointer,
                        verts,
                        vert_weights,
                        vert_weight_indices,
                        vert_normals,
                        vert_uv,
                        exported_face_index):         
        ## first write the main data part
        
        writer = BinaryReader()        
        of_a = len(data1)
        writer.write_bytes(data1) 
        writer.seek(of_a,0)        
        vertex_count = len(verts)
        
        for i in range(vertex_count):        
            writer.write_float(verts[i][0])
            writer.write_float(verts[i][2])
            writer.write_float(verts[i][1]) 
                            
            writer.write_float(vert_weights[i][0])
            writer.write_uint8(vert_weight_indices[i][0])
            writer.write_uint8(vert_weight_indices[i][1])
            writer.write_uint16(0)

            writer.write_float(vert_normals[i][0])
            writer.write_float(vert_normals[i][2])
            writer.write_float(vert_normals[i][1])
                
            writer.write_float(vert_uv[i][0])
            writer.write_float(vert_uv[i][1]*-1)  

        new_face_pointer = writer.pos()
        face_count = len(exported_face_index)
        
        for j in exported_face_index:        
            writer.write_uint16(j)
            
        new_end_pointer = writer.pos()        
        writer.write_bytes(end_data)        
        file_size = writer.pos()
        
        ## todo: write the offsets and such        
        ## face offset is 32 from obdp to start of face
        
        writer.seek(f_size_offset)        
        writer.write_uint32(file_size - obdp_pointer)                       ## new_filesize_offset         
        writer.seek(v_table_offset)
        writer.write_uint32( int(new_end_pointer - (obdp_pointer + 32)) )   ## new_end_offset         
        writer.seek(v_data_offset)                                          ## table data stuff
        writer.write_uint32(vertex_count)                                   ## vertex_count 
        writer.write_uint32(new_face_pointer - (obdp_pointer + 32))         ## face_pointer
        writer.write_uint32(face_count)                                     ## face_count
        
        file = open(filepath,'wb')
        file.write(writer.buffer())
        file.close()       

    
    me = bpy.context.object.data    
    verts,vert_weights ,vert_weight_indices ,vert_normals, vert_uv ,exported_face_index = retrive_mesh_data_from_blender(me)
    data1,end_data,f_size_offset,v_table_offset,v_data_offset,obdp_pointer = identify_and_get_ome_data(filepath)   
    write_to_file(filepath,data1,end_data,f_size_offset,v_table_offset,v_data_offset,obdp_pointer,verts,vert_weights,vert_weight_indices,vert_normals,vert_uv,exported_face_index)
    
    self.report({'INFO'}, "OME Export Finished in %.4f sec" % (time.time() - time_start))
    return {'FINISHED'}
    