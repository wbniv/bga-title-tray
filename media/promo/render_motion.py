"""Render the transparent motion layer for the BGA Title Tray promo.

Run with Blender 5: blender -b --python render_motion.py -- --output-dir DIR
The output is a numbered 30 fps PNG sequence consumed by render-motion.sh.
"""

import argparse
import math
import sys
from pathlib import Path

import bpy


def arguments():
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--frames", help="Comma-separated frames for visual inspection")
    return parser.parse_args(args)


def linear_channel(value):
    value /= 255
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def material(name, color):
    color = color.lstrip("#")
    rgb = tuple(linear_channel(int(color[i : i + 2], 16)) for i in (0, 2, 4))
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*rgb, 1)
    return mat


def rectangle(name, x, y, width, height, mat, depth=0):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], [], [(0, 1, 2, 3)])
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = (x, 720 - y - height, depth)
    obj.scale = (width, height, 1)
    return obj


def ring(name, x, y, mat):
    segments = 96
    vertices = []
    faces = []
    for index in range(segments):
        angle = 2 * math.pi * index / segments
        vertices.extend(
            [(math.cos(angle), math.sin(angle), 0),
             (0.91 * math.cos(angle), 0.91 * math.sin(angle), 0)]
        )
        following = (index + 1) % segments
        faces.append((2 * index, 2 * following, 2 * following + 1, 2 * index + 1))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = (x, 720 - y, 1)
    return obj


def scale_keys(obj, values):
    for frame, sx, sy in values:
        obj.scale = (sx, sy, 1)
        obj.keyframe_insert(data_path="scale", frame=frame)


def main():
    args = arguments()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 50
    scene.render.fps = 30
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.render.image_settings.compression = 20
    scene.render.filepath = str(output_dir / "frame_")
    scene.render.use_file_extension = True
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    scene.render.image_settings.color_management = "FOLLOW_SCENE"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.light = "FLAT"
    scene.display.shading.show_shadows = False
    scene.display.shading.show_cavity = False

    camera_data = bpy.data.cameras.new("Motion camera")
    camera_data.type = "ORTHO"
    # Workbench narrows the camera frame at 50% render resolution. This scale
    # restores the intended 1280 x 720 design area in the 640 x 360 output.
    camera_data.ortho_scale = 1280
    camera = bpy.data.objects.new("Motion camera", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = (640, 360, 100)
    scene.camera = camera

    lime = material("Indri lime #b8ef00", "b8ef00")
    muted = material("Panel track #77716a", "77716a")

    # Opening: a restrained underline enters below the introductory copy.
    intro = rectangle("Opening underline", 90, 386, 0, 5, lime, 1)
    scale_keys(intro, [(1, 0, 5), (12, 0, 5), (42, 645, 5),
                       (84, 645, 5), (90, 0, 5)])

    # Queue: each increment lands just after the matching search count appears.
    track = rectangle("Queue track", 168, 332, 0, 5, muted, 1)
    scale_keys(track, [(1, 0, 5), (90, 0, 5), (91, 944, 5),
                       (180, 944, 5), (181, 0, 5)])
    progress = rectangle("Queue progress", 168, 332, 0, 5, lime, 2)
    scale_keys(progress, [(1, 0, 5), (91, 0, 5), (97, 236, 5),
                          (113, 236, 5), (119, 472, 5), (136, 472, 5),
                          (142, 708, 5), (158, 708, 5), (164, 944, 5),
                          (180, 944, 5), (181, 0, 5)])

    # Play: brackets frame the installed panel as its title begins to flash.
    for name, x, y, width, height, grow_x in [
        ("Play top left", 130, 346, 90, 4, True),
        ("Play left", 130, 346, 4, 46, False),
        ("Play top right", 1060, 346, 90, 4, True),
        ("Play right", 1146, 346, 4, 46, False),
    ]:
        obj = rectangle(name, x, y, 0 if grow_x else width,
                        height if grow_x else 0, lime, 3)
        if grow_x:
            scale_keys(obj, [(1, 0, height), (181, 0, height),
                             (193, width, height), (300, width, height),
                             (301, 0, height)])
        else:
            scale_keys(obj, [(1, width, 0), (181, width, 0),
                             (193, width, height), (300, width, height),
                             (301, width, 0)])

    # Click: an expanding ring follows the composited pointer impact.
    ripple = ring("Click ripple", 404, 430, lime)
    scale_keys(ripple, [(1, 0, 0), (558, 0, 0), (559, 17, 17),
                        (575, 74, 74), (576, 0, 0)])

    # Browser cut: a thin line carries the Indri accent into the final frame.
    browser_line = rectangle("Browser cut underline", 0, 27, 0, 4, lime, 4)
    scale_keys(browser_line, [(1, 0, 4), (576, 0, 4),
                              (594, 1280, 4), (660, 1280, 4)])

    if args.frames:
        for frame in [int(part) for part in args.frames.split(",")]:
            scene.frame_set(frame)
            scene.render.filepath = str(output_dir / f"frame_{frame:04d}.png")
            bpy.ops.render.render(write_still=True)
    else:
        scene.frame_start = 1
        scene.frame_end = 660
        bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    main()
