bl_info = {
    "name": "PS2/PS3 Yakuza model importer/exporter (ome,omz)",
    "author": "Gabe hen, Hamzaxx360",
    "version": (1, 0, 0),
    "blender": (2, 81, 6),
    "location": "File > Import-Export",
    "description": "",
    "warning": "",
    "doc_url": "",
    "category": "Import-Export",
}

#Obviously NOT a <pep8 compliant> code

###
#Thanks to timo ,kan, violet and jhirno for their valuable contributions in reverse-engineering the ome format! 
#Thanks to Hamzaxx360 for his help in parsing omz and helping with code improvements
#Thanks to sutando for his binary reader!
###
if "bpy" in locals():
    import importlib
    if "OME_import" in locals():
        importlib.reload(OME_import)
    if "OMZ_import" in locals():
        importlib.reload(OMZ_import) 
    if "binaryreader" in locals():
        importlib.reload(binaryreader)
  

import bpy
from mathutils import *
from .binary_reader import BinaryReader 
from .OME_import import import_ome
from .OMZ_import import import_omz
  
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator


class ImportOME(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "import_ome.ome_data"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import OME"

    # ImportHelper mixin class uses this
    filename_ext = ".ome"

    filter_glob: StringProperty(
        default="*.ome",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    use_armature: BoolProperty(
            name="Load armature",
            description="Loads armature",
            default=True,
    )
    
    use_uv: BoolProperty(
            name="Load UV",
            description="Loads UV map of the mesh if available",
            default=True,
    )

    use_normals: BoolProperty(
            name="Load normals",
            description="Loads normals of the mesh if available",
            default=True,
    )
    
    create_mats: BoolProperty(
            name="Generate materials",
            description="Assigns a basic material node for the mesh",
            default=True,
    )    

    orient: BoolProperty(
            name="Fix orentation of mesh and armature",
            description="Fixes the orientation of the model as well as the uv and armature of the model",
            default=True,
    )
    
    debug_data: BoolProperty(
            name="Debug Data",
            description="Prints offsets, pointers and other techinical data for debugging purposes",
            default=False,
    ) 
    
    """
    override: EnumProperty(
        name="Override mesh table row length to:",
        items=(
            ('NONE',"none" ,"Auto-detect row length"),        
            ('a',"40" ,"Override mesh table row length to 40"),
            ('b',"36","Override mesh table row length to 36"),
            ('c',"32" ,"Override mesh table row length to 32"),
            ('d',"24" ,"Override mesh table row length to 24"),             
        ),
    )
    """
    
    def execute(self, context):
        
        return import_ome(  context,
                            self.filepath,
                            self.use_armature,
                            self.use_uv,
                            self.use_normals,
                            self.create_mats,
                            self.orient,
                            self.debug_data)

class ImportOMZ(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "import_omz.omz_data"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import OMZ"

    # ImportHelper mixin class uses this
    filename_ext = ".dat"

    filter_glob: StringProperty(
        default="*.dat",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )
    
    omz_orient: BoolProperty(
            name="Fix orentation of mesh",
            description="Fixes the orientation of the model as well as the uv of the model",
            default=True,
    )
    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.

    def execute(self, context):
        
        return import_omz(context, self.filepath, self.omz_orient)
     

# Only needed if you want to add into a dynamic menu
def menu_func_importOME(self, context):
    self.layout.operator(ImportOME.bl_idname, text="PS2/PS3 Yakuza .OME (chara and multimesh)")
    
def menu_func_importOMZ(self, context):
    self.layout.operator(ImportOMZ.bl_idname, text="PS2/PS3 Yakuza .OMZ (cloth physics mesh)")
    

def register():
    bpy.utils.register_class(ImportOME)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_importOME)
    
    bpy.utils.register_class(ImportOMZ)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_importOMZ)
    

def unregister():
    bpy.utils.unregister_class(ImportOME)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_importOME)
    
    bpy.utils.unregister_class(ImportOMZ)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_importOMZ)



    # test call
    #bpy.ops.import_test.some_data('INVOKE_DEFAULT')











