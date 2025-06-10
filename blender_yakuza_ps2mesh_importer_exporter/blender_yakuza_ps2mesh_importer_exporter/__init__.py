bl_info = {
    "name": "PS2/PS3 Yakuza model importer/exporter (ome,omz)",
    "author": "Gabe hen, Hamzaxx360",
    "version": (2, 0, 0),
    "blender": (2, 81, 6),
    "location": "File > Import-Export",
    "description": "Import-Export PS2/PS3 Yakuza OME/OMZ Files",
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
    if "OME_export" in locals():
        importlib.reload(OME_export)   
    if "OMZ_import" in locals():
        importlib.reload(OMZ_import) 
    if "binaryreader" in locals():
        importlib.reload(binaryreader)
    if "OMZ_export" in locals():
        importlib.reload(OMZ_export) 
  

import bpy
from mathutils import *
from .binary_reader import BinaryReader 
from .OME_import import import_ome
from .OMZ_import import import_omz
from .OME_export import export_ome 
from .OMZ_export import export_omz
  
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator


class ImportOME(Operator, ImportHelper):
    """Import PS2/PS3 Yakuza OME File"""
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
    
    use_phys: BoolProperty(
            name="Load physics Data",
            description="Loads physics Data of the mesh if available",
            default=True,
    )

    use_origin: BoolProperty(
            name="Load origin points",
            description="Loads origin points of the mesh if available",
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
    
    TXB_filepaths: bpy.props.StringProperty(
            name="Texture Directory",
            description="Directory to where the texture are in",
            default=""
    )
    
    TXB_filename: bpy.props.StringProperty(
            name="Image name",
            description="Type the image name \nIf you have 2 images 1_0_0.png and 1_0_1.png, just typing \"1_0_\" will suffice",
            default=""
    )
    
    ### enum prop for file types, or maybe not
    #png,jpg,jpeg,dds  
    TXB_fileformat: bpy.props.StringProperty(
            name="Image format",
            description="Type the image format ('.png', '.dds', '.jpeg etc))",
            default=""
    )
    
    txbfilepath: bpy.props.StringProperty(
            name="TXB filepath",
            description= "Directory to where the texture are in",
            default=""
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
                            self.debug_data,
                            self,
                            self.TXB_filepaths,
                            self.TXB_filename,
                            self.TXB_fileformat,
                            self.txbfilepath,
                            self.use_phys,
                            self.use_origin)

class ImportOMZ(Operator, ImportHelper):
    """Import PS2/PS3 Yakuza OMZ File"""
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
    OMZPARENT: BoolProperty(
            name="Render Onto Model (Must Select Armature)",
            description="",
            default=True,
    )
    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.

    def execute(self, context):
        
        return import_omz(context, self.filepath, self.omz_orient,self.OMZPARENT)

class ExportOME(Operator, ExportHelper):

    bl_idname = "export_test.some_data"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Export Some Data"

    filename_ext = ".ome"
    filter_glob: StringProperty(
        default="*.ome",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        
        return export_ome(context, self.filepath, self)

class ExportOMZ(Operator, ExportHelper):
    """Export PS2/PS3 Yakuza OMZ File"""
    bl_idname = "export_omz.omz_data"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Export OMZ"

    # ImportHelper mixin class uses this
    filename_ext = ".dat"

    filter_glob: StringProperty(
        default="*.dat",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    FlowVal : bpy.props.FloatProperty(
        name="Flow Value",
        description="",
        default=0.0,
    )

    DampVal : bpy.props.FloatProperty(
        name="Damp Value",
        description="",
        default=0.0,
    )
    
    ParentBone: EnumProperty(
            name="Parent Bone",
            description="Where The OMZ Renders Onto The Main Model",
            default=8,
            items=[('0', "0", ""),
                    ('1', "1", ""),
                    ('2', "2", ""),
                    ('3', "3", ""),
                    ('4', "4", ""),
                    ('5', "5", ""),
                    ('6', "6", ""),
                    ('7', "7", ""),
                    ('8', "8", ""),
                    ('9', "9", ""),
                    ('10', "10", ""),
                    ('11', "11", ""),
                    ('12', "12", ""),
                    ('13', "13", ""),
                    ('14', "14", ""),
                    ('15', "15", ""),
                    ('16', "16", ""),
                    ('17', "17", ""),
                    ('18', "18", ""),
                    ('19', "19", ""),
                    ('20', "20", ""),
                    ('21', "21", ""),
                    ('22', "22", ""),
                    ('23', "23", ""),
                    ('24', "24", ""),
                    ('25', "25", ""),
                    ]
    )
    ExistingArmatures:EnumProperty(
        name="Parent Armature",
        description="",
        items = lambda self,context:[(obj.name,obj.name,"")for obj in context.scene.objects if obj.type== 'ARMATURE']
        
    )   
    ExportCollision:EnumProperty(
        name="Collision Armature",
        description="",
        items = lambda self,context:[(obj.name,obj.name,"")for obj in context.scene.objects if obj.type== 'ARMATURE']
        
    )
    UseOldConsts: BoolProperty(
        name="Use old constraints (flow and damp values)",
        description="If enabled, will reuse the old flow and damp values even if you have inputted your own.",
        default=False,
    )
    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.

    def execute(self, context):
        BodyName = self.ExistingArmatures
        BodyArmature = bpy.data.objects.get(BodyName)
        ColName = self.ExportCollision
        ColArmature = bpy.data.objects.get(ColName)
        return export_omz(context, self.filepath,self.ParentBone,self.FlowVal,self.DampVal,BodyArmature,ColArmature,self.UseOldConsts,self)
    

# Only needed if you want to add into a dynamic menu
def menu_func_importOME(self, context):
    self.layout.operator(ImportOME.bl_idname, text="PS2/PS3 .OME(chara and multimesh)")
    
def menu_func_importOMZ(self, context):
    self.layout.operator(ImportOMZ.bl_idname, text="PS2/PS3 .OMZ(cloth physics mesh)")
    
def menu_func_export(self, context):
    self.layout.operator(ExportOME.bl_idname, text="PS2/PS3 .OME")
    
def menu_func_exportOMZ(self, context):
    self.layout.operator(ExportOMZ.bl_idname, text="PS2/PS3 Yakuza .OMZ (cloth physics mesh)")


def register():
    bpy.utils.register_class(ImportOME)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_importOME)
    
    bpy.utils.register_class(ImportOMZ)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_importOMZ)
    
    bpy.utils.register_class(ExportOME)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
   
    bpy.utils.register_class(ExportOMZ)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_exportOMZ)   


def unregister():
    bpy.utils.unregister_class(ImportOME)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_importOME)
    
    bpy.utils.unregister_class(ImportOMZ)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_importOMZ)
   
    bpy.utils.unregister_class(ExportOME)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

    bpy.utils.unregister_class(ExportOMZ)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_exportOMZ)



    # test call
    #bpy.ops.import_test.some_data('INVOKE_DEFAULT')