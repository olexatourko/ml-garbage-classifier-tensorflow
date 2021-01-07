import bpy, os
from math import sin, cos, pi
import numpy as np
import json
import sys

"""
Add scripts folder to Blender's Python interpreter and reload all scripts.
http://web.purplefrog.com/~thoth/blender/python-cookbook/import-python.html
"""
dir = os.path.dirname(bpy.data.filepath)
if not dir in sys.path:
    sys.path.append(dir)

import boundingbox
import importlib
importlib.reload(boundingbox)

def render(scene, camera_object, mesh_objects, camera_steps, file_prefix="render"):
    """
    Renders the scene at different camera angles to a file, and returns a list of label data
    """

    radians_in_circle = 2.0 * pi
    original_position = np.matrix([
        [8],
        [0],
        [2]
    ])

    """ This will store the bonding boxes """
    labels = []

    for i in range(0, camera_steps + 1):
        for j in range(0, camera_steps + 1):
            yaw = radians_in_circle * (i / camera_steps)
            pitch = -1.0 * radians_in_circle / 16.0 * (j / camera_steps)
            # Blender uses a Z-up coordinate system instead of the standard Y-up system, therefor:
            # yaw = rotate around z-axis
            # pitch = rotate around y-axis
            yaw_rotation_matrix = np.matrix([
                [cos(yaw), -sin(yaw), 0],
                [sin(yaw), cos(yaw), 0],
                [0, 0, 1]
            ])
            pitch_rotation_matrix = np.matrix([
                [cos(pitch), 0, sin(pitch)],
                [0, 1, 0],
                [-sin(pitch), 0, cos(pitch)]
            ])

            new_position = yaw_rotation_matrix * pitch_rotation_matrix * original_position
            camera_object.location.x = new_position[0][0]
            camera_object.location.y = new_position[1][0]
            camera_object.location.z = new_position[2][0]

            # Rendering
            # https://blender.stackexchange.com/questions/1101/blender-rendering-automation-build-script
            filename = '{}-{}y-{}p.png'.format(str(file_prefix), str(i), str(j))
            bpy.context.scene.render.filepath = os.path.join('./renders/', filename)
            bpy.ops.render.render(write_still=True)

            scene = bpy.data.scenes['Scene']
            label_entry = {
                'image': filename,
                'meshes': {}
            }
            textfilename = filename.split(sep, 1)[0]
            #change the following line to include your desired output directory for .txt YOLO annotations
            file = open(r'write here annotations output directory' + textfilename + '.txt','w+')
            """ Get the bounding box coordinates for each mesh """
            for object in mesh_objects:
                bounding_box = boundingbox.camera_view_bounds_2d(scene, camera_object, object)
                #this will enable the script to work when the object is out of the scene
                if bounding_box and object.is_visible(scene): 
                    label_entry['meshes']["object.name"] = {
                        'x1': bounding_box[0][0],
                        'y1': bounding_box[0][1],
                        'x2': bounding_box[1][0],
                        'y2': bounding_box[1][1]
                    }
                else:
                    bounding_box =  [[0,0], [0,0]]
                #Formating the bounding boxes to match YOLO darknet annotations and writing them into the txt file
                y = object.name, bounding_box[0][0], bounding_box[0][1], bounding_box[1][0], bounding_box[1][1]
                width = bounding_box[1][0] - bounding_box[0][0] 
                height = bounding_box[1][1] - bounding_box[0][1]
                xC = bounding_box[0][0] + (width / 2)
                yC = 1 - (bounding_box[0][1] + (height / 2))
                objname = object.name    
                z = object.name, xC, yC, width, height
                if bounding_box != [[0,0], [0,0]] and object.is_visible(scene):
                    for item in z:                    
                        file.write("%s" % item)
                        file.write(' ')
                    file.write('\n')
                
                    print(label_entry)
            labels.append(label_entry)
            file.close()
            labels.append(label_entry)

    return labels


def batch_render(scene, camera_object, mesh_objects):
    import scene_setup
    camera_steps = 10
    scene_setup_steps = 10
    spawn_range = [
        (-10, 10),
        (-10, 10),
        (5, 10)
    ]
    labels = []

    for i in range(0, scene_setup_steps):
        scene_setup.simulate(scene, mesh_objects, spawn_range, 0.75)
        scene_labels = render(scene, camera_object, mesh_objects, camera_steps, file_prefix=i)
        labels += scene_labels # Merge lists

    with open('./renders/labels.json', 'w+') as f:
        json.dump(labels, f, sort_keys=True, indent=4, separators=(',', ': '))


if __name__ == '__main__':
    scene = bpy.data.scenes['Scene']
    camera_object = bpy.data.objects['Camera']
    mesh_names = ['Cube', 'Sphere']
    mesh_objects = [bpy.data.objects[name] for name in mesh_names]
    batch_render(scene, camera_object, mesh_objects)
