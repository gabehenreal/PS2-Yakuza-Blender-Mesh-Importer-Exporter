import bpy
from mathutils import *
from .binary_reader import BinaryReader 
import time
import bmesh 

def import_ome(context, filepath, use_armature, use_uv , use_normals, create_mats, orient, debug_data ):
    
    if debug_data == True:
        print("import_ome func debug:")
        print(context, filepath, use_armature, use_uv , use_normals, create_mats, orient,sep = "\n")

    def create_armature(new_collection ,armature_count ,arm ,qarm ,group_idx ,last_parented):
        
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
    
    def create_vertex_groups(me, mesh_count, vertex_group_data1, vertex_group_data2, group_idx, w_ind_1, w_ind_2):
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
            ### parent mesh:
            armature_obj = bpy.data.objects[amt_name]
            mesh_obj = bpy.data.objects[objname]
            
            if armature_obj is not None and mesh_obj is not None:

                mesh_obj.select_set(True)
                armature_obj.select_set(True)
                bpy.context.view_layer.objects.active = armature_obj
                bpy.ops.object.parent_set(type='ARMATURE_NAME')
    
    def create_uv(bm,vert_uv):
        
        # FROM: https://behreajj.medium.com/shaping-models-with-bmesh-in-blender-2-9-2f4fcc889bf0    
    
        uv_verify = bm.loops.layers.uv.verify()
        bm_faces = bm.faces
        
        ff = 0 
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
            for lno in numbe_faces:                                               # face Vector flipper, part 2, actually flips
         

                bpy.ops.object.mode_set(mode = 'EDIT')                           ## not a very "sustainable" code
                bpy.ops.mesh.select_mode(type="FACE")
                bpy.ops.mesh.select_all(action = 'DESELECT')
                bpy.ops.object.mode_set(mode = 'OBJECT')
                me.polygons[lno].select = True
                bpy.ops.object.mode_set(mode = 'EDIT') 
                bpy.ops.mesh.flip_normals()
                
                flip+=1
            
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

    time_start = time.time()
    
    print("running OME_import...")
    f = open(filepath, 'rb')

    reader = BinaryReader(f.read())

    if reader.read_str(3) != 'OME':
        print("File is invalid")
        raise Exception("Breaking op, file has invalid header")
    else:
        print("File is valid")
        
    
    #### OME table things
    
    reader.seek(4,0)
    ome_uvar1 = reader.read_uint16() # possible mesh version number, mostly 6 but ver 5s do exist
    
    reader.seek(8,0)
    obdp_pointer = reader.read_uint16() ## ODBP table loc
    
    reader.seek(16,0)
    ome_uvar2_unktable_count = reader.read_uint16() # a count for the table below the ome header table
    
    reader.seek(20,0)
    ome_uvar3_size = reader.read_uint16()  #possibly ome table size, which is always gonna be 48
    
    reader.seek(24,0)
    ome_uvar4_pointer = reader.read_uint16() # from experimentation, some shader value for model sheen
    
    reader.seek(28,0)
    ome_mesh_flag = reader.read_uint16() # mesh flag 
    
    reader.seek(obdp_pointer,0)

    if (reader.read_str(4)) != "ODBP":
    
        ### this will be implemented quite soon!
        if (reader.read_str(4)) != "MDBP":
            print("File is invalid")
            raise Exception("File is invalid, Unsupported version (expected ODBP, not MDBP)!!!")
            
        else:
            print("File is invalid")
            raise Exception("File is invalid, Invalid sub header!!!")


    reader.seek(obdp_pointer + 40,0)
    arm_pointer = reader.read_uint16()                                      ### points to armature

    reader.seek(obdp_pointer + 36 ,0)
    mesh_count = reader.read_uint16()                                       ### counts the number of meshes in the file

    skip = 0
    vtx_pointers=[]
    
    for i in range(mesh_count):                                             ### this reads vertex pointers
        reader.seek(obdp_pointer + 128 + skip ,0)
        vtx_inf_pointer = reader.read_uint32()
        vtx_pointers.append(vtx_inf_pointer)
        
        skip += 64
        
    armature_count = 0
    
    reader.seek (obdp_pointer + 44, 0)
    armature_count = reader.read_uint16()                                   ### retrives the armature bone count
    
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


    ### BEWARE: a long line of code
   
    new_collection = bpy.data.collections.new('OME_collection')
    bpy.context.scene.collection.children.link(new_collection)

    has_created_arm = False
    
    increase = 0
    
    if debug_data == True:
        print("all vertex pointers: ",vtx_pointers)
    
    mesh_table_row_size = 0
    
    for vtx_inf_pointer in vtx_pointers:
    
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
    
        b = 0 

        for k in range(vertex_count): ## timo suggests rel seeks than abs

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

                normals_pos_x = 0 ##absloute trash data if read
                normals_pos_y = 0
                normals_pos_z = 0
                
                reader.seek (obdp_pointer + vtx_inf_pointer + 64 + 16 + b, 0)                
                
                uv_pos_x = reader.read_float()
                uv_pos_y = reader.read_float()

                weight_grp_1_val = 0
                weight_grp_2_val = 1 - weight_grp_1_val
                weight_grp_1 = 0
                weight_grp_2 = 0
                
                b += 24
                
            else: 
            
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

        d = 3                           ## gets true face sequence from face index table
        for l in range(face_count):     ## ie 12345 has (1,2,3), (3,4,5)
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
        
        if debug_data == True:
            print("count of non_faces is:",stat_bad_faces)
        
        ###
        # mesh parser
     
        edges = []
        
        newmesh_name = mesh_name[increase]
        
        me = bpy.data.meshes.new(newmesh_name)
        me.from_pydata(verts, edges, faces,)
        me.update()

        objname = newmesh_name + 'object'
        ome_object = bpy.data.objects.new(objname, me)
        
        if create_mats == True:
            ome_mat = bpy.data.materials.new("OME_MAT")
            ome_object.data.materials.append(ome_mat)
            ome_object.active_material_index = len(ome_object.data.materials) - 1 
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
            
            m_up_count = 1
            m += m_up_count
            
            
        vertex_group_data1 = []
        vertex_group_data2 = []
        create_vertex_groups(me, mesh_count, vertex_group_data1, vertex_group_data2, group_idx, w_ind_1, w_ind_2)
        

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

        parse_normals(mesh_table_row_size,me,faces1,faces2,faces3,vtx_n,ome_object)
        
        increase += 1
            
        if has_created_arm == False and use_armature == True:
            arm_name = create_armature(new_collection ,armature_count ,arm ,qarm ,group_idx ,last_parented)
            has_created_arm =True
        else:
            pass
        if use_armature == True:
            parent_mesh_to_armature(arm_name,current_mesh_name)


    
    print("OME Import Finished: %.4f sec" % (time.time() - time_start))
    
    f.close()
    return {'FINISHED'} 