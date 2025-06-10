import bpy
from mathutils import *
from .binary_reader import BinaryReader 
from .TXB_parser import *
import time
import bmesh 
import os

def import_ome( context,
                filepath,
                use_armature,
                use_uv,
                use_normals,
                create_mats, 
                orient, 
                debug_data, 
                self,
                TXB_filepaths,
                TXB_filename,
                TXB_fileformat,
                txbfilepath,
                use_phys,
                use_origin):
    
    if debug_data == True:
        print("import_ome func debug:")
        print(context, filepath, use_armature, use_uv , use_normals, create_mats, orient,sep = "\n")
        print(TXB_filepaths, TXB_filename, sep = "\n")

    def create_armature(new_collection, armature_count, arm, qarm, group_idx, last_parented):
        """Creates a usable armature for the mesh"""
        amt_name = "OME_Armature"
        amt = bpy.data.armatures.new(amt_name)
        amt_object = bpy.data.objects.new(amt_name, amt)
        new_collection.objects.link(amt_object)
        bpy.context.view_layer.objects.active = amt_object
        current_arm_name = amt_object.name
            
        num = 0
        for z in range(armature_count):      
            bpy.ops.object.mode_set(mode='EDIT')
            bone = amt.edit_bones.new(group_idx[num])
            bone.head = arm[num]
            bone.tail = qarm[num]
            bpy.ops.object.mode_set(mode='OBJECT')
           
            num += 1  
        bpy.ops.object.mode_set(mode='EDIT') 
        
        if mesh_count == 1: ## fix arm parenting for multi mesh
            for parent_inf in last_parented:
                bpy.context.view_layer.objects.active = amt_object
                arm = bpy.data.objects[amt_name]
  
                if parent_inf[0] == 160 or parent_inf[1] == 160:
                    pass
                else:
                    bpy.ops.object.mode_set(mode='EDIT')
                    amt.edit_bones[group_idx[ parent_inf[0] ] ].parent = amt.edit_bones[ group_idx[ parent_inf[1] ] ]                    
            bpy.ops.object.mode_set(mode='OBJECT')
        else:
            bpy.ops.object.mode_set(mode='OBJECT')        
        if debug_data == True:
            print(amt_name,current_arm_name)   
            
        return current_arm_name
    
    def create_vertex_groups(me, mesh_count, vertex_group_data1, vertex_group_data2, group_idx, w_ind_1, w_ind_2, mesh_type):
        """Creates vertex group for the mesh"""
        a = 0
        for n in me.vertices:
            if mesh_count != 1:
                break
            else:
                group1 = ome_object.vertex_groups[group_idx[w_ind_1[a]]]
                vertex_group_data1.append(a)
                group1.add(vertex_group_data1, w_val_1[a], 'ADD')
                vertex_group_data1.remove(a)

                group2 = ome_object.vertex_groups[group_idx[w_ind_2[a]]]
                vertex_group_data2.append(a)
                group2.add(vertex_group_data2, w_val_2[a], 'ADD')
                vertex_group_data2.remove(a)
                            
                a += 1

    def parent_mesh_to_armature(amt_name,objname): 
        """Parents created armature to the mesh"""
        armature_obj = bpy.data.objects[amt_name]
        mesh_obj = bpy.data.objects[objname]
            
        if armature_obj is not None and mesh_obj is not None:
            mesh_obj.select_set(True)
            armature_obj.select_set(True)
            bpy.context.view_layer.objects.active = armature_obj
            bpy.ops.object.parent_set(type='ARMATURE_NAME')
    
    def create_uv(bm,vert_uv):
        """Creates a UVmap for the mesh"""
        # FROM: https://behreajj.medium.com/shaping-models-with-bmesh-in-blender-2-9-2f4fcc889bf0       
        uv_verify = bm.loops.layers.uv.verify()
        bm_faces = bm.faces
        
        for bm_face in bm_faces:
            bm_idx = bm_face.index
            uv_idx_tup = faces[bm_idx]      
            loop_idx = 0
            face_loops = bm_face.loops
            
            for bm_loop in face_loops:
                loop_uv_layer = bm_loop[uv_verify]
                uv_idx = uv_idx_tup[loop_idx]
                # Acquire UV coordinate with UV index,
                # assign to loop's UV layer coordinate.
                loop_uv_layer.uv = vert_uv[uv_idx]
                loop_idx = loop_idx + 1
                
            bm_face.smooth = True           
            
        bm.verts.ensure_lookup_table()
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)    
        
    def parse_normals(mesh_table_row_size,me,faces1,faces2,faces3,vtx_n,ome_object):
    
        ### this normal parser is absoulutely crap, i hate it
        
        numbe_faces = []
        ff = 0
        list_count = 0
        flip = 0 
        noflip = 0
        _ihatethis = []
    
        if mesh_table_row_size == 24.0:
            pass
        else:
            
            ### to be replaced soon:
            
            for h in range(stat_true_faces):                                               # face Vector flipper , part 1

                fvx1, fvy1, fvz1 = me.vertices[faces1[ff]].normal                # gets dot product and finds inverted vectors
                fvx2, fvy2, fvz2 = me.vertices[faces2[ff]].normal                # ie anything  below 0 will be flipped
                fvx3, fvy3, fvz3 = me.vertices[faces3[ff]].normal                
     
                svx1, svy1, svz1 = vtx_n[faces1[ff]]                             
                svx2, svy2, svz2 = vtx_n[faces2[ff]]                             
                svx3, svy3, svz3 = vtx_n[faces3[ff]]
                
                face = me.polygons[h]
                
                v1 = me.vertices[face.vertices[0]].co
                v2 = me.vertices[face.vertices[1]].co
                v3 = me.vertices[face.vertices[2]].co
                    
                # Compute the two edge vectors
                edge1 = v2 - v1
                edge2 = v3 - v1
                    
                # Compute the cross product of the two edge vectors
                normal = edge1.cross(edge2)
                    
                # Normalize the normal vector
                normal.normalize()
                
                co1_1 = Vector((svx1, svy1, svz1))
                co1_2 = Vector((svx2, svy2, svz2))
                co1_3 = Vector((svx3, svy3, svz3))
                
                combined_c_vec_dot = (co1_1+co1_2+co1_3)/ 3 
                
                ### vector dot product time
                
                final_dot = combined_c_vec_dot.dot(normal)
                
                if final_dot >= 0 :
                    noflip += 1
                else: 
                    flip += 1
                    numbe_faces.append(h) 
               
                ff += 1
            
            flip = 0 
            # face Vector flipper, part 2, actually flips
            
            bpy.ops.object.mode_set(mode = 'EDIT')                           ## not a very "sustainable" code
            bpy.ops.mesh.select_mode(type="FACE")
            bpy.ops.mesh.select_all(action = 'DESELECT')
            bpy.ops.object.mode_set(mode = 'OBJECT')
            
            for lno in numbe_faces:   
                me.polygons[lno].select = True
                flip+=1
                
            bpy.ops.object.mode_set(mode = 'EDIT') 
            bpy.ops.mesh.flip_normals()
            bpy.ops.mesh.select_all(action = 'DESELECT')
            
            if debug_data == True:
                print("faces flipped:",flip)
                print("faces not flipped:",noflip)
           

            bpy.context.view_layer.objects.active = ome_object
            bpy.ops.object.mode_set(mode = 'OBJECT')

            #context = bpy.context
            #ob = context.object
            #me = ob.data

            #me.use_auto_smooth = True ## removed for 4.0 onwards
    
            #FROM: https://blender.stackexchange.com/questions/165115/how-to-set-custom-vertex-normals-for-certain-vertices-using-python            
            
            me.normals_split_custom_set([(0, 0, 0) for l in me.loops])

            normals = []
            count = 0
            for v in me.vertices:
                
                if v == me.vertices[count]:
                    normals.append(vtx_n[count])
                else:
                    normals.append(v.normal)

                count += 1
           
            me.normals_split_custom_set_from_vertices(normals)
 
    def create_vertex_colors(me, clrs, vc_group):
        """Creates vertex colors for the mesh"""
        #based from: https://medium.com/@bldevries/using-python-and-custom-data-to-vertex-color-your-blender-model-4fd0d69134a3
        for poly in me.polygons:
            for j, vertid in enumerate(poly.vertices):  
                cur_loop = poly.loop_indices[j]
                rgba = [x / 128 for x in clrs[vertid]]  
                vc_group.data[cur_loop].color = rgba
 
 
    #######################
    #
    #   File reading stuff
    #
    #######################
    
    time_start = time.time()  
    print("running OME_import...")
    
    f = open(filepath, 'rb')
    reader = BinaryReader(f.read())
    if reader.read_str(3) != 'OME':
        self.report({'ERROR'}, "Invalid file magic!")
        raise Exception("Breaking op, file has invalid magic")
    else:
        print("File is valid")
 
 
    #### OME table things
    reader.seek(4,0)
    ome_uvar1 = reader.read_uint32()                        # mesh version number
    obdp_pointer = reader.read_uint32()                     ## ODBP table loc

    reader.seek(16,0)    
    ome_uvar2_unktable_count = reader.read_uint32()         # a count for the table below the ome header table
    ome_uvar3_size = reader.read_uint32()                   # possibly ome table size, which is always gonna be 48
    ome_uvar4_pointer = reader.read_uint32()                # from experimentation, some shader value for model sheen
    ome_mesh_flag = reader.read_uint32()                    # mesh flag? 
       
    if debug_data == True:
        print(    
            "ome_uvar1",ome_uvar1,
            "obdp_pointer",obdp_pointer,  
            "ome_uvar2_unktable_count",ome_uvar2_unktable_count,
            "ome_uvar3_size",ome_uvar3_size,
            "ome_uvar4_pointer",ome_uvar4_pointer,
            "ome_mesh_flag",ome_mesh_flag,
        )
    #### reading object data
    
    entry_data = []
    for i in range(ome_uvar2_unktable_count):
        reader.seek(64 + (i*32),0)
        
        unk1 = reader.read_uint32()
        pointer = reader.read_uint32()
        unk2 = reader.read_uint32()
        const = reader.read_uint32()
        s_unk1 = reader.read_uint16()
        s_unk2 = reader.read_uint16()
        unk3 = reader.read_uint32()
        
        pad_a = reader.read_uint32()
        pad_b = reader.read_uint32()
    
        entry_data.append((unk1,pointer,unk2,const,s_unk1,s_unk2,unk3))
        if debug_data == True:
            print(entry_data[i])
    
    another_entry = []
    for k in entry_data:
        
        if k[0] == 0:
            pass
        else:
            reader.seek(16 + k[1],0)
            
            count1 = reader.read_uint32()
            pointer1 = reader.read_uint32()
            pointer2 = reader.read_uint32()
            count2 = reader.read_uint32()
            
            another_entry.append((count1,pointer1,pointer2,count2))
            if debug_data == True:
                print((count1,pointer1,pointer2,count2))
            
    coord_list = []
    for j in another_entry:
        reader.seek(16 + j[2],0)
        if debug_data == True:
            print(j[2])
        temp = []        
        for n in range(j[3]):
            x_coord = reader.read_float()
            y_coord = reader.read_float()
            z_coord = reader.read_float()
            unkfloat = reader.read_float()
            temp.append((x_coord,y_coord,z_coord,unkfloat))
        if debug_data == True:    
            print(temp)
        coord_list.append(temp)       
    print("\n")
    
    ### obdp struct
    reader.seek(obdp_pointer,0)
    if (reader.read_str(4)) != "ODBP":
    
        ### this will be implemented quite soon!
        if (reader.read_str(4)) != "MDBP":
            self.report({'ERROR'}, "Unsupported file subtype!")
            raise Exception("File is invalid, Unsupported version (expected ODBP, not MDBP)!")
            
        else:
            self.report({'ERROR'}, "Invalid file subtype!")
            raise Exception("File is invalid, Invalid subfile magic!")
    
    
    reader.seek(obdp_pointer+4,0)
    obdp_size_or_pointer = reader.read_uint32()         ### dunno if its a pointer or a size
    obdp_unk = reader.read_uint32()                     ### unknown
    obdp_filesize = reader.read_uint32()                ### filesize
    
    reader.seek(obdp_pointer+32,0)
    struct_size = reader.read_uint32()                  ### points to armature
    mesh_count = reader.read_uint32()                   ### counts the number of meshes in the file
    arm_pointer = reader.read_uint32()                  ### points to armature
    armature_count = reader.read_uint32()               ### retrives the armature bone count
    
    reader.seek(obdp_pointer+60,0)
    physpointer = reader.read_uint32() 
    
    reader.seek(obdp_pointer+80,0)
    mat_pointer = reader.read_uint32() 

    if debug_data == True:
        print(    
            "obdp_size_or_pointer",obdp_size_or_pointer,"\n",
            "obdp_unk",obdp_unk,"\n",  
            "obdp_filesize",obdp_filesize,"\n",
            "struct_size",struct_size,"\n",
            "mesh_count",mesh_count,"\n",
            "arm_pointer",arm_pointer,"\n",
            "armature_count",armature_count,"\n",
            "physpointer",physpointer,"\n",
            "mat_pointer",mat_pointer,"\n"
        )


    skip = 0
    vtx_pointers=[]
    material_indices = []
    orginpoints = []
    unkpoint = []
    
    for i in range(mesh_count):                                             ### this reads vertex pointers
        reader.seek(obdp_pointer + 128 + skip ,0)
        vtx_inf_pointer = reader.read_uint32()
        vtx_pointers.append(vtx_inf_pointer)
        
        reader.seek(obdp_pointer + 136 + skip ,0)
        material_id = reader.read_uint32()
        material_indices.append(material_id)  
        
        reader.seek(obdp_pointer + 160 + skip ,0)
        orginx = reader.read_float()
        orginy = reader.read_float()
        orginz = reader.read_float()
        orgin_unk = reader.read_float()
        if orient == True:
            orginpoints.append([(orginx,orginz,orginy),(orginx,orgin_unk,orginy)])
        else:
            orginpoints.append([(orginx,orginy,orginz),(orginx,orginz,orgin_unk)]) 
        skip += 64
        
    if debug_data == True:
        print(material_indices)
    
    matids,imagenames = [],[]
    if  len(TXB_filename) == 0 or len(TXB_filepaths) == 0 or len(txbfilepath) == 0:
        pass
    else:
        matids,imagenames = read_txb_info(txbfilepath,TXB_filename,TXB_fileformat)
    
    
    if debug_data == True:
        print("armature count",armature_count)
  
    a = 0
    arm = []
    s_parent_to = []
    sibling_pointer =[]
    
    p_sbiling_of =  []
    parent_pointer =[]
    
    parent_to = []
    sibling_parent = []
    not_the_first = False
    last_parented = [] 
    qarm = []
    
    simple_arm_list=[]
    
    for j in range(armature_count):
        
        reader.seek (obdp_pointer + arm_pointer + 48 + a, 0)
        pos_x = reader.read_float()
        pos_y = reader.read_float()
        pos_z = reader.read_float()
        
        
        reader.seek (obdp_pointer + arm_pointer + 32 + a , 0)
        s_pointer = reader.read_uint32()
        p_pointer = reader.read_uint32()
        #print(s_pointer,p_pointer)
        
        sibling_pointer.append(s_pointer) ## for debug purposes only are we recording this
        parent_pointer.append(p_pointer)       
        
        reader.seek (obdp_pointer + s_pointer + 40, 0)
        bone_a = reader.read_uint16()
        s_parent_to.append(bone_a)
        
        reader.seek (obdp_pointer + p_pointer + 40, 0)
        bone_b = reader.read_uint16()
        p_sbiling_of.append(bone_b)        
        
        ### bone parenting rules
        ### if i = 0, maybe skip the first rule        
        ### otherwise:
        ### 1)do i have a parent? yes, check the buffer        
        ### 2_do i parent anyone, yes, please put that in the buffer
        ### 3)any siblings? if so, go thru the last_parented
        ### the code works but it does not work the way i expected
        
        if j == 0:        
            last_parented.append([s_parent_to[0],j])
            #simple_arm_list.append([j,"empty"])

        else:            
            for something in last_parented:
                if j == something[1]:
                    #simple_arm_list.append([something[1],something[0]])
                    break
                    
            if s_parent_to[j] != 160 or s_parent_to[j] != 0:
                last_parented.append([s_parent_to[j],j])                
            else:
                pass
            
            if p_sbiling_of[j] != 160 or p_sbiling_of[j] != 0:                
                for something_parent in last_parented:                   
                    if j == something_parent[0]:
                        last_parented.append([p_sbiling_of[j],something_parent[1]])
                        break 
            else:                
                pass
                
        if orient == True:
            arm.append((pos_x,pos_z,pos_y))
            qarm.append((pos_x ,pos_z+0.5 ,pos_y))
        else:
            arm.append((pos_x,pos_y,pos_z))
            qarm.append((pos_x ,pos_y ,pos_z+0.5))      
        a += 80
    
    mesh_name=[]   
    for number in range(mesh_count):  # just gives names really   
        endno = str(number)
        meshnamereal = "mesh"+endno
        mesh_name.append(meshnamereal)
    
    ### material groups
    matgroups = []
    if ome_uvar1 != 0:        
        reader.seek (obdp_pointer + 32 +mat_pointer)
        mat_table_pointer = reader.read_uint32()
        mat_table_count = reader.read_uint32()       
        matpointersandcounts = []
        reader.seek (obdp_pointer + 32 +mat_pointer + 32)
        
        skip_bytes = 0
        for w in range(mat_table_count):
            reader.seek (obdp_pointer + 32 +mat_pointer + 32 + skip_bytes )
            table_pointer = reader.read_uint32()
            table_count = reader.read_uint32()
            matpointersandcounts.append((table_pointer,table_count))           
            skip_bytes += 32
        
        if debug_data == True:
            print(matpointersandcounts)
                
        for pointer,count in matpointersandcounts:
            reader.seek (obdp_pointer + 32 + pointer)            
            templist = []
            for h in range(count):
                meshid = reader.read_uint16()
                templist.append(meshid)
            matgroups.append(templist) 
        print(matgroups)
    else:
        pass
           
    subpoints = []
    mainpoints = []
    if physpointer == 0:
        pass
    else:
        reader.seek(obdp_pointer + 32 + physpointer,0)
        
        unkcount1 = reader.read_uint32()
        pointer1 = reader.read_uint32()
        reader.seek(obdp_pointer + 32 + pointer1,0)
        
        pointer2 = reader.read_uint32()
        pad = reader.read_uint32()
        unkcount1 = reader.read_uint32()
        unkcount2 = reader.read_uint32()
        subphyspointpointer = reader.read_uint32()
        reader.seek(obdp_pointer + 32 + pointer2,0)
        
        pad1 = reader.read_uint32()
        pad2 = reader.read_uint32()
        unkcount_a = reader.read_uint32()
        pointcounts = reader.read_uint32()
        phyvertspointer = reader.read_uint32()
        
        reader.seek(obdp_pointer + 32 + subphyspointpointer,0)
        for n in range(unkcount2):
            phyx_pos_x = reader.read_float()
            phyx_pos_y = reader.read_float()
            phyx_pos_z = reader.read_float()     
            phyx_pad = reader.read_float()  
            if orient == True:
                subpoints.append((phyx_pos_x,phyx_pos_z,phyx_pos_y))
            else:
                subpoints.append((phyx_pos_x,phyx_pos_y,phyx_pos_z)) 
        
        reader.seek(obdp_pointer + 32 + phyvertspointer,0)
        for n in range(pointcounts):
            phyx_pos_x = reader.read_float()
            phyx_pos_y = reader.read_float()
            phyx_pos_z = reader.read_float()     
            phyx_pad = reader.read_float()  
            if orient == True:
                mainpoints.append((phyx_pos_x,phyx_pos_z,phyx_pos_y))
            else:
                mainpoints.append((phyx_pos_x,phyx_pos_y,phyx_pos_z))         


 
    ### BEWARE: a long line of code
    #######################
    #
    #   File reading stuff with now some blender funcs yay
    #
    #######################
        
    new_collection = bpy.data.collections.new('OME_collection')
    bpy.context.scene.collection.children.link(new_collection)
    
    ### sub collections
    origin_collection = bpy.data.collections.new('OME_Origin')
    new_collection.children.link(origin_collection)
    phys_collection = bpy.data.collections.new('OME_Physics')
    new_collection.children.link(phys_collection)
   
    has_created_arm = False
    increase = 0    
    if debug_data == True:
        print("all vertex pointers: ",vtx_pointers)
    
    mesh_table_row_size = 0
    verttime = []    
    for vtx_inf_pointer in vtx_pointers:                    ### this loop is wayyy too long, gotta fix that    
        reader.seek(obdp_pointer + vtx_inf_pointer + 44 ,0)
        vertex_count = reader.read_uint32() 
        face_pointer = reader.read_uint32() 
        face_count = reader.read_uint16() 

        reader.seek (obdp_pointer + face_pointer + 32 , 0)       
        if debug_data == True:
            print("current pos",reader.pos())
        
        mesh_table_row_size = ((face_pointer + 32)-(vtx_inf_pointer + 64)) / vertex_count ## determines what table reading algorithim must be used      
        if debug_data == True:
            print("vertex count =",vertex_count)
            print("face inx pointer=",face_pointer)
            print("face count =",face_count)
            print(mesh_table_row_size)
 
        vert_uv = []
        verts = []
        vtx_n = []    
        w_ind_1 = []
        w_ind_2 = []    
        w_val_1 = []
        w_val_2 = []        
        vertexcolors = []
    
        b = 0 
        a_time_start = time.time()
        
        ### this could have been handled a bit better
        ### put the loops in a if else block instead of the other way around
        for k in range(vertex_count): 
            ##this is to initiate the values
            pos_x = 0
            pos_y = 0
            pos_z = 0        
            weight_grp_1_val = 0
            weight_grp_2_val = 0
            weight_grp_1 = 0
            weight_grp_2 = 0      
            normals_pos_x = 0
            normals_pos_y = 0
            normals_pos_z = 0
            uv_pos_x = 0
            uv_pos_y = 0
        
            if mesh_table_row_size == 40.0: ## THIS ONE IS STANDARD, FOR CHARA MESHES
         
                reader.seek (obdp_pointer + vtx_inf_pointer + 64 + 0 + b, 0)
                pos_x = reader.read_float()
                pos_y = reader.read_float()
                pos_z = reader.read_float()
        
                weight_grp_1_val = reader.read_float()
                weight_grp_2_val = 1 - weight_grp_1_val

                weight_grp_1 = reader.read_uint8()
                weight_grp_2 = reader.read_uint8()
                
                reader.seek (obdp_pointer + vtx_inf_pointer + 64 + 20 + b, 0)               
                normals_pos_x = reader.read_float()
                normals_pos_y = reader.read_float()
                normals_pos_z = reader.read_float()

                uv_pos_x = reader.read_float()
                uv_pos_y = reader.read_float() 
                
                b += 40
                
            elif mesh_table_row_size == 36.0 : ## FOR WDR MESHES IN STAGE           
                reader.seek (obdp_pointer + vtx_inf_pointer + 64 + 0 + b, 0)                
                pos_x = reader.read_float()
                pos_y = reader.read_float()
                pos_z = reader.read_float()
                
                weight_grp_1 = reader.read_uint8()
                weight_grp_2 = reader.read_uint8()
                
                weight_grp_1_val = 1
                weight_grp_2_val = 0               
                
                reader.seek (obdp_pointer + vtx_inf_pointer + 64 + 16 + b, 0)
                normals_pos_x = reader.read_float()
                normals_pos_y = reader.read_float()
                normals_pos_z = reader.read_float()
   
                uv_pos_x = reader.read_float()
                uv_pos_y = reader.read_float()
                
                b += 36
                
            elif mesh_table_row_size == 32.0 : ## FOR MULTI MESH            
                reader.seek (obdp_pointer + vtx_inf_pointer + 64 + 0 + b, 0)                
                pos_x = reader.read_float()
                pos_y = reader.read_float()
                pos_z = reader.read_float()

                normals_pos_x = reader.read_float()
                normals_pos_y = reader.read_float()
                normals_pos_z = reader.read_float()
   
                uv_pos_x = reader.read_float()
                uv_pos_y = reader.read_float()
                
                weight_grp_1_val = 0
                weight_grp_2_val = 1 - weight_grp_1_val
                weight_grp_1 = 0
                weight_grp_2 = 0
                
                b += 32
                
            elif mesh_table_row_size == 24.0: ## FOR STAGE MODELS                 
                reader.seek (obdp_pointer + vtx_inf_pointer + 64 + 0 + b, 0)                
                pos_x = reader.read_float()
                pos_y = reader.read_float()
                pos_z = reader.read_float()
  
                ## this is apparently colors, what
                vert_color_b = (reader.read_uint8()+1)//2
                vert_color_g = (reader.read_uint8()+1)//2
                vert_color_r = (reader.read_uint8()+1)//2
                vert_color_a = (reader.read_uint8()+1)//2
                vertexcolors.append([vert_color_r,vert_color_g,vert_color_b,vert_color_a])
                
                reader.seek (obdp_pointer + vtx_inf_pointer + 64 + 16 + b, 0)                                
                uv_pos_x = reader.read_float()
                uv_pos_y = reader.read_float()

                weight_grp_1_val = 0
                weight_grp_2_val = 1 - weight_grp_1_val
                weight_grp_1 = 0
                weight_grp_2 = 0 
                
                b += 24
                
            else:                 
                self.report({'ERROR'}, "Unknown mesh table type!")
                raise Exception("Breaking op, unsupported mesh row size({})".format(mesh_table_row_size))   
                
            if orient == True:  ## y will be z, z will be y, and x is x                
                verts.append((pos_x,pos_z,pos_y))
                vtx_n.append((normals_pos_x,normals_pos_z,normals_pos_y))
                vert_uv.append((uv_pos_x,uv_pos_y*-1))               
            else:            
                verts.append((pos_x,pos_y,pos_z))
                vtx_n.append((normals_pos_x,normals_pos_y,normals_pos_z))
                vert_uv.append((uv_pos_x,uv_pos_y))
                
            w_ind_1.append(weight_grp_1)
            w_ind_2.append(weight_grp_2)            
            w_val_1.append(weight_grp_1_val)
            w_val_2.append(weight_grp_2_val)            
        vtime = time.time() - a_time_start
        verttime.append(vtime)
        
        d = 3                           ## gets true face sequence from face index table
        for l in range(face_count):     ## ie 12345 has (1,2,3), (2,3,3) etc
            d += 1
            if d == face_count:
                if debug_data == True:
                    print("variable l",l)
                break
        actual_face_count = l+2

        ##this invalidates face tuples like (1,1,0) etc   
        faces1 = [] ## for my bad normal parser.
        faces2 = [] #
        faces3 = [] #
        faces = []       
        c = 0
        stat_bad_faces = 0
        stat_true_faces = 0            
        face_time=[]
        f_time_start = time.time()
        for i in range(actual_face_count): 
            reader.seek (obdp_pointer + face_pointer + 32 + c, 0)
            face_1 = reader.read_uint16()
            face_2 = reader.read_uint16()
            face_3 = reader.read_uint16()
        
            if  face_1 == face_2 or face_2 == face_3 or face_2 == face_3 or face_1 == face_3:
                stat_bad_faces += 1                
            else:                
                faces1.append(face_1)
                faces2.append(face_2)
                faces3.append(face_3)
                faces.append((face_1,face_2,face_3))
                stat_true_faces += 1                
            c += 2
        ftime = time.time() - f_time_start
        face_time.append(ftime)                  
        if debug_data == True:
            print("count of non_faces is:",stat_bad_faces)
        
        
        # mesh parser
        newmesh_name = mesh_name[increase]       
        me = bpy.data.meshes.new(newmesh_name)
        me.from_pydata(verts, [], faces,)
        me.update()

        objname = newmesh_name + 'object'
        ome_object = bpy.data.objects.new(objname, me)
        
        me.color_attributes.new(name="OME vertex color", type = 'BYTE_COLOR', domain='CORNER')
        OMEcolor = me.color_attributes["OME vertex color"]       
        if mesh_table_row_size == 24.0:
            create_vertex_colors(me, vertexcolors, OMEcolor)
        
        if create_mats == True:        
            ome_mat = bpy.data.materials.new("OME_MAT")
            ome_mat.use_nodes = True
            ome_object.data.materials.append(ome_mat)
            ome_object.active_material_index = len(ome_object.data.materials) - 1 
            
            ### create the ps2/ps3 yakuza "shader"
            nodes = ome_mat.node_tree.nodes          
            existing_BSDFshader_node = nodes.get("Principled BSDF")             ## sets IOR to 1
            existing_BSDFshader_node.inputs.get("IOR").default_value = 1 
            ome_mat.blend_method = 'CLIP'
            
            node_img = nodes.new("ShaderNodeTexImage")                          ## create image node
            node_img.location = (-600,300)            
            node_color_ramp = nodes.new("ShaderNodeValToRGB")                   ## create color ramp
            node_color_ramp.location = (-300,200)
            node_color_vert = nodes.new("ShaderNodeVertexColor")                ## create color attribute
            node_color_vert.location = (-350,500) 
            node_color_mix = nodes.new("ShaderNodeMixRGB")                      ## create mix node
            node_color_mix.location = (-150,500) 
            
            ## setup color ramp             
            node_color_ramp = nodes.get("Color Ramp")
            node_color_ramp.color_ramp.interpolation = 'CONSTANT'           
            stops = node_color_ramp.color_ramp.elements
            stops[1].position = 0.000625#0.1
            stops[0].position = 0.0
            
            ## setup the multiply node
            clrmix = nodes.get("Mix (Legacy)")
            clrmix.blend_type = 'MULTIPLY'
            
            ## setup the vertex color node
            vertclr = nodes.get("Color Attribute")
            vertclr.layer_name = "OME vertex color"
 
            ## link nodes to each other
            imagenode = nodes.get("Image Texture")
            clrrampnode = nodes.get("Color Ramp")            
            node_tree = ome_mat.node_tree            
            node_tree.links.new(imagenode.outputs['Alpha'], clrrampnode.inputs['Fac'])
            node_tree.links.new(clrrampnode.outputs['Color'], existing_BSDFshader_node.inputs['Alpha'])
            node_tree.links.new(imagenode.outputs['Color'], existing_BSDFshader_node.inputs['Base Color'])
            node_tree.links.new(imagenode.outputs['Alpha'], existing_BSDFshader_node.inputs['Roughness'])            
            node_tree.links.new(vertclr.outputs['Color'], clrmix.inputs['Color2'])
            node_tree.links.new(vertclr.outputs['Alpha'], clrmix.inputs['Fac'])

     
            if len(TXB_filename) == 0 or len(TXB_filepaths) == 0 or ome_uvar1 == 0:
                ## based off turnip's code for making a temp image            
                temp_image = bpy.data.images.new("image", 128, 128, alpha=True)
                temp_image.source = 'GENERATED'
                temp_image.generated_type = 'BLANK'
                temp_image.generated_color = (1.0, 1.0, 1.0, 1.0)
                temp_image.generated_width = 128
                temp_image.generated_height = 128
                imagenode.image = temp_image
                if mesh_table_row_size == 24.0:
                    node_tree.links.new(imagenode.outputs['Color'], clrmix.inputs['Color1'])
                    node_tree.links.new(clrmix.outputs['Color'], existing_BSDFshader_node.inputs['Base Color'])
                else:
                    node_tree.links.new(imagenode.outputs['Color'], existing_BSDFshader_node.inputs['Base Color'])
            else:               
                try:
                    matidinx = matids.index(material_indices[increase])
                    finalpath = TXB_filepaths+imagenames[matidinx]                            
                    if not os.path.exists(finalpath):
                        print(f"Error: The file at '{finalpath}' does not exist.")
                    else:
                        print(f"The file at '{finalpath}' exists. Proceeding.")                  
                    image = bpy.data.images.load(bpy.path.abspath(finalpath))
                    imagenode.image = image
                    if mesh_table_row_size == 24.0:
                        node_tree.links.new(imagenode.outputs['Color'], clrmix.inputs['Color1'])
                        node_tree.links.new(clrmix.outputs['Color'], existing_BSDFshader_node.inputs['Base Color'])    
                    else:
                        node_tree.links.new(imagenode.outputs['Color'], existing_BSDFshader_node.inputs['Base Color'])                    
                except:
                    temp_image = bpy.data.images.new("image", 128, 128, alpha=True)
                    temp_image.source = 'GENERATED'
                    temp_image.generated_type = 'BLANK'
                    temp_image.generated_color = (1.0, 1.0, 1.0, 1.0)
                    temp_image.generated_width = 128
                    temp_image.generated_height = 128
                    imagenode.image = temp_image
                    if mesh_table_row_size == 24.0:
                        node_tree.links.new(imagenode.outputs['Color'], clrmix.inputs['Color1'])
                        node_tree.links.new(clrmix.outputs['Color'], existing_BSDFshader_node.inputs['Base Color'])
                    else:
                        node_tree.links.new(imagenode.outputs['Color'], existing_BSDFshader_node.inputs['Base Color'])
        else:
            pass
        
        new_collection.objects.link(ome_object)
        bpy.context.view_layer.objects.active = ome_object 
        current_mesh_name = ome_object.name
        
        if debug_data == True:
            print(objname,current_mesh_name)          
        obj_uv = bpy.context.active_object.data.uv_layers.new(name='OME_UV')
        
        m = 0
        group_idx = []
        
        for deez in range(armature_count):       
            group = str(m)
            ome_object.vertex_groups.new(name = group)
            group_idx.append(group)           
            m += 1
   
        vertex_group_data1 = []
        vertex_group_data2 = []
        create_vertex_groups(me, mesh_count, vertex_group_data1, vertex_group_data2, group_idx, w_ind_1, w_ind_2, mesh_table_row_size)
        
        bm = bmesh.new()   
        bm.from_mesh(me)   
        me.validate()
        if use_uv == True:
            create_uv(bm,vert_uv)
        else:
            bm_faces = bm.faces   
            bm.verts.ensure_lookup_table()
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)                   
        bm.to_mesh(me)
        bm.free()
        
        nor_time = []
        n_time_start = time.time()        
        parse_normals(mesh_table_row_size,me,faces1,faces2,faces3,vtx_n,ome_object)        
        ntime = time.time() - n_time_start
        nor_time.append(ntime)
        
        increase += 1
            
        if has_created_arm == False and use_armature == True:
            arm_name = create_armature(new_collection ,armature_count ,arm ,qarm ,group_idx ,last_parented)
            has_created_arm =True
        else:
            pass
        if use_armature == True:
            parent_mesh_to_armature(arm_name,current_mesh_name)
    
    if use_origin == True:
        ### creating orgin points:
        for k in range(len(orginpoints)):
            newmesh_name = str(k)              
            me = bpy.data.meshes.new(newmesh_name)
            me.from_pydata(orginpoints[k], [], [],)
            me.update()

            objname = newmesh_name + '_orgin_point'
            ome_object = bpy.data.objects.new(objname, me)
            origin_collection.objects.link(ome_object)
        
        
    if use_phys == True:
        ### creating sub phys points:        
        newmesh_name = str(0)               
        me = bpy.data.meshes.new(newmesh_name)
        me.from_pydata(subpoints, [], [],)
        me.update()

        objname = newmesh_name + '_phys_sub_point'
        ome_object = bpy.data.objects.new(objname, me)
        phys_collection.objects.link(ome_object)
            
        ### creating main points:            
        newmesh_name = str(0)               
        me = bpy.data.meshes.new(newmesh_name)
        me.from_pydata(mainpoints, [], [],)
        me.update()

        objname = newmesh_name + '_main_phys_point'
        ome_object = bpy.data.objects.new(objname, me)
        phys_collection.objects.link(ome_object)
        
    print("Total time taken to parse vertex tables%.4f sec" % (sum(verttime)))
    print("Total time taken to parse faces%.4f sec" % (sum(face_time)))
    print("Total time taken to parse normals%.4f sec" % (sum(nor_time)))
    self.report({'INFO'}, "OME Import Finished in %.4f sec" % (time.time() - time_start))
    
    f.close()
    return {'FINISHED'} 