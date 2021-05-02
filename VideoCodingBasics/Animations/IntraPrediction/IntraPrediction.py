import bpy
from bpy.types import Operator
import bpy_extras
from mathutils import Vector

class INTRAPRED_OT_test(Operator):
    bl_idname = "intrapred.test"
    bl_label = "Add Test Object"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        verts = [
            Vector((0, 0, 0)),
            Vector((4, 0, 0)),
            Vector((4, 0, 1)),
            Vector((0, 0, 1))
        ]
        edges = []
        faces = [[0, 1, 2, 3]]
        mesh = bpy.data.meshes.new(name=f"TestPanel")
        mesh.from_pydata(verts, edges, faces)
        bpy_extras.object_utils.object_data_add(context, mesh)
        return {'FINISHED'}

class INTRAPRED_PT_panel(bpy.types.Panel):
    bl_label = "Intra Prediction"
    bl_idname = "INTRAPRED_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "NewTab"
    
    def draw(self, context):
        row = self.layout.row()
        row.operator("intrapred.test", text="Draw Test")
        
def register():
    bpy.utils.register_class(INTRAPRED_OT_test)
    bpy.utils.register_class(INTRAPRED_PT_panel)
    
def unregister():
    bpy.utils.unregister_class(INTRAPRED_OT_test)
    bpy.utils.unregister_class(INTRAPRED_PT_panel)
    
if __name__ == "__main__":
    register()
