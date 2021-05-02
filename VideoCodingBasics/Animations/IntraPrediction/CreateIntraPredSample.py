bl_info = {
    "name": "Create Intra Prediction Sample",
    "author": "Christian Feldmann",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Add > Mesh > Intra Prediction Example",
    "description": "Adds the Intra prediction Example",
    "warning": "",
    "doc_url": "",
    "category": "Add Mesh",
}

import bpy
import bpy_extras
from bpy.types import Operator
from bpy.props import FloatVectorProperty
from mathutils import Vector

from random import seed
from random import randint
import math

def add_border(xpos, ypos, context, op, index):
    bt = 0.01
    verts = [
        Vector((-bt, 0, -bt)),
        Vector((1+bt, 0, -bt)),
        Vector((1+bt, 0, 1+bt)),
        Vector((-bt, 0, 1+bt)),
        Vector((bt, 0, bt)),
        Vector((1-bt, 0, bt)),
        Vector((1-bt, 0, 1-bt)),
        Vector((bt, 0, 1-bt))
    ]
    edges = []
    faces = [[0, 1, 2, 3, 0, 4, 7, 6, 5, 4]]
    mesh = bpy.data.meshes.new(name=f"BorderMesh{index}")
    mesh.from_pydata(verts, edges, faces)

    # Get material (create if it does not exist)
    mat = bpy.data.materials.get("BlackBorderMaterial")
    if mat is None:
        mat = bpy.data.materials.new(name="BlackBorderMaterial")
    mat.diffuse_color = (0, 0, 0, 1) # Black Alpha 1

    if (len(mesh.materials) > 0):
        mesh.materials[0] = mat
    else:
        mesh.materials.append(mat)
        
    obj = bpy_extras.object_utils.object_data_add(context, mesh, operator=op)
    obj.location.z = ypos
    obj.location.x = xpos
    obj.location.y = -0.01
    
def add_value(xpos, ypos, context, op, index, value):
    verts = [
        Vector((0, 0, 0)),
        Vector((1, 0, 0)),
        Vector((1, 0, 1)),
        Vector((0, 0, 1))
    ]
    edges = []
    faces = [[0, 1, 2, 3]]
    mesh = bpy.data.meshes.new(name=f"ValuePlane{index}")
    mesh.from_pydata(verts, edges, faces)
    
    # Get material (create if it does not exist)
    mat = bpy.data.materials.get(f"Value{value}Material")
    if mat is None:
        mat = bpy.data.materials.new(name=f"Value{value}Material")
    mat.diffuse_color = (value / 255, value / 255, value / 255, 1) # Grey value "value" Alpha 1
    
    if (len(mesh.materials) > 0):
        mesh.materials[0] = mat
    else:
        mesh.materials.append(mat)
        
    obj = bpy_extras.object_utils.object_data_add(context, mesh, operator=op)
    obj.location.z = ypos
    obj.location.x = xpos
    obj.location.y = 0.00
    
    
def add_extension(xpos, ypos, context, op, index, value, depth):
    offset = 20
    sq05 = math.sqrt(1/2) / 2
    verts = [
        Vector((0, 0, 0)),
        Vector((0, 0, sq05)),
        Vector((offset, 0, sq05)),
        Vector((offset, 0, -sq05)),
        Vector((0, 0, -sq05))
    ]
    edges = []
    faces = [[0, 1, 2, 3, 4]]
    mesh = bpy.data.meshes.new(name=f"ExtensionPlane{index}")
    mesh.from_pydata(verts, edges, faces)
    
    # Get material (create if it does not exist)
    mat = bpy.data.materials.get(f"Value{value}Material")
    if mat is None:
        mat = bpy.data.materials.new(name=f"Value{value}Material")
    mat.diffuse_color = (value / 255, value / 255, value / 255, 1) # Grey value "value" Alpha 1
    
    if (len(mesh.materials) > 0):
        mesh.materials[0] = mat
    else:
        mesh.materials.append(mat)
        
    obj = bpy_extras.object_utils.object_data_add(context, mesh, operator=op)
    obj.location.z = ypos + 0.5
    obj.location.x = xpos + 0.5
    obj.location.y = depth
    obj.rotation_euler = (0, math.pi / 4, 0)
    
def add_pixel(xpos, ypos, context, op, index, value, depth):
    add_border(xpos, ypos, context, op, index)
    add_value(xpos, ypos, context, op, index, value)
    add_extension(xpos, ypos, context, op, index, value, depth)

class OBJECT_OT_add_intraPred(Operator, bpy_extras.object_utils.AddObjectHelper):
    """Create a new Mesh Object"""
    bl_idname = "mesh.add_object"
    bl_label = "Add Intra Prediction Object"
    bl_options = {'REGISTER', 'UNDO'}

    scale: FloatVectorProperty(
        name="scale",
        default=(1.0, 1.0, 1.0),
        subtype='TRANSLATION',
        description="scaling",
    )

    def execute(self, context):
        width = 4
        height = 4

        seed(22)        
        maxRandVal = 180

        idx = 0
        for y in range(height*2):
            depth = y + 2
            add_pixel(0, -1-y, context, self, idx, randint(0, maxRandVal), depth*0.05)
            idx += 1
        add_pixel(0, 0, context, self, idx, randint(0, maxRandVal), 0.05)
        idx += 1
        for x in range(width*2):
            depth = x + 2
            add_pixel(x+1, 0, context, self, idx, randint(0, maxRandVal), depth*0.05)
            idx += 1
        for y in range(height):
            for x in range(width):
                add_border(x+1, -1-y, context, self, idx)
                idx += 1
        
        return {'FINISHED'}


# Registration

def add_object_button(self, context):
    self.layout.operator(
        OBJECT_OT_add_intraPred.bl_idname,
        text="Add Intra prediction",
        icon='PLUGIN')


def register():
    bpy.utils.register_class(OBJECT_OT_add_intraPred)
    bpy.types.VIEW3D_MT_mesh_add.append(add_object_button)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_add_intraPred)
    bpy.types.VIEW3D_MT_mesh_add.remove(add_object_button)


if __name__ == "__main__":
    register()
