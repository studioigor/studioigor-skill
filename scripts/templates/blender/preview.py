"""Asset previews for boards: frames the object(s), sets up studio lighting, renders a PNG.

Run (headless, safe in parallel — nothing is saved to the .blend):
  Blender -b file.blend -P preview.py -- --out DIR [options]        # asset from a .blend
  Blender -b -P preview.py -- --glb model.glb --out DIR [options]   # GLB/glTF/FBX/OBJ
  Blender -b -P preview.py -- --glb a.glb --glb b.glb --out DIR     # several models in a row

Options:
  --turntable N      N angles around the model (8 → every 45°), files <name>_00.png…
  --size PX          side of the square frame (768)
  --engine E         workbench (fast, for contact sheets) | eevee (materials, shadows;
                     default) | cycles
  --collection NAME  frame only this collection
  --elev/--azim DEG  camera elevation (22) and azimuth (-35: three-quarter front-right)
  --ortho            orthographic camera (icons, isometric, 3D→2D sprites)
  --transparent      transparent background without a floor (icons, sprites)
  --bg HEX           background color (#2b2e35)
  --keep-scene       render with the camera and lights from the file (a look-dev scene in Blender)
  --name NAME        file prefix (default: the model/.blend file name)

Prints PNG paths, render time and a `RESULT {json}` line. Exit code ≠0 on error.
"""
import argparse
import json
import math
import os
import sys
import time

import bpy
from mathutils import Vector

HELPER = "PV_"   # prefix for the preview's helper objects


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser(prog="preview.py")
    ap.add_argument("--out", required=True)
    ap.add_argument("--glb", action="append", default=[])
    ap.add_argument("--turntable", type=int, default=0)
    ap.add_argument("--size", type=int, default=768)
    ap.add_argument("--engine", choices=["workbench", "eevee", "cycles"], default="eevee")
    ap.add_argument("--collection", default="")
    ap.add_argument("--elev", type=float, default=22.0)
    ap.add_argument("--azim", type=float, default=-35.0)
    ap.add_argument("--ortho", action="store_true")
    ap.add_argument("--transparent", action="store_true")
    ap.add_argument("--bg", default="#2b2e35")
    ap.add_argument("--keep-scene", action="store_true")
    ap.add_argument("--name", default="")
    return ap.parse_args(argv)


def fail(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.stdout.flush()
    sys.exit(1)


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_linear(h):
    h = h.lstrip("#")
    return [srgb_to_linear(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4)]


def setp(obj, attr, value):
    """Sets a property if it exists in this Blender version (the API changes between versions)."""
    if hasattr(obj, attr):
        try:
            setattr(obj, attr, value)
        except (TypeError, AttributeError, ValueError):
            pass


# ------------------------------------------------------------------ loading

def import_model(path):
    ext = os.path.splitext(path)[1].lower()
    before = set(bpy.data.objects)
    if ext in {".glb", ".gltf"}:
        bpy.ops.import_scene.gltf(filepath=path)
    elif ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=path)
    elif ext == ".obj":
        bpy.ops.wm.obj_import(filepath=path)
    else:
        fail(f"cannot import {ext}: {path}")
    new = [o for o in bpy.data.objects if o not in before]
    if not new:
        fail(f"no objects in {path}")
    return new


def target_objects(a, imported):
    if imported:
        objs = imported
    elif a.collection:
        coll = bpy.data.collections.get(a.collection)
        if coll is None:
            fail(f"collection \"{a.collection}\" not found")
        objs = list(coll.all_objects)
    else:
        objs = list(bpy.context.scene.objects)
    vl = bpy.context.view_layer
    objs = [o for o in objs if o.type in {"MESH", "CURVE", "FONT", "META", "SURFACE"}
            and o.name in vl.objects and not o.hide_render and not o.name.startswith(HELPER)
            and not any(s in o.name for s in ("-col", "-colonly", "-convcolonly", "-navmesh"))]
    if not objs:
        fail("nothing to render: no visible meshes")
    if not a.keep_scene:   # only the target in frame: no collisions, proxies or scene neighbors
        keep = set(objs)
        for o in bpy.context.scene.objects:
            if o not in keep and o.type in {"MESH", "CURVE", "FONT", "META", "SURFACE"}:
                o.hide_render = True
    return objs


def bounds(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    lo = Vector((math.inf,) * 3)
    hi = Vector((-math.inf,) * 3)
    tris = 0
    for o in objs:
        ev = o.evaluated_get(dg)
        for c in ev.bound_box:
            w = ev.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
        if o.type == "MESH":
            me = ev.to_mesh()
            me.calc_loop_triangles()
            tris += len(me.loop_triangles)
            ev.to_mesh_clear()
    return lo, hi, tris


# ------------------------------------------------------------------ studio

def orbit_dir(azim_deg, elev_deg):
    """Unit vector from the center to the camera/light. Azimuth 0 is the front (the -Y side,
    where the model faces); negative is to the right when looking at the model."""
    az, el = math.radians(azim_deg), math.radians(elev_deg)
    return Vector((-math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))


def setup_studio(a, lo, hi):
    scene = bpy.context.scene
    center = (lo + hi) / 2
    radius = max((hi - lo).length / 2, 1e-3)

    if not a.keep_scene:
        for o in scene.objects:           # other lights and cameras do not interfere with the studio
            if o.type in {"LIGHT", "CAMERA"}:
                o.hide_render = True

    pivot = bpy.data.objects.new(HELPER + "Pivot", None)
    scene.collection.objects.link(pivot)
    pivot.location = center

    cam_data = bpy.data.cameras.new(HELPER + "Cam")
    cam = bpy.data.objects.new(HELPER + "Cam", cam_data)
    scene.collection.objects.link(cam)
    cam.parent = pivot
    direction = orbit_dir(a.azim, a.elev)
    cam.rotation_euler = (-direction).to_track_quat("-Z", "Y").to_euler()
    cam_data.clip_end = radius * 500
    scene.camera = cam
    if a.ortho:
        cam_data.type = "ORTHO"
        cam_data.ortho_scale = radius * 2.3
        dist = radius * 4
    else:
        cam_data.lens = 50
        dist = radius / math.sin(cam_data.angle / 2)
    cam.location = direction * dist
    cam_data.clip_start = max(radius / 500, 0.001)
    fit_camera(cam, pivot, lo, hi, a)

    # three suns relative to the camera: key top-left, soft fill on the right, rim behind.
    # Suns do not depend on the asset's scale (a figurine and a building are lit the same).
    for name, energy, d_az, el, soft in (("Key", 3.0, 45, 50, 3.0), ("Fill", 0.9, -70, 20, 10.0),
                                         ("Rim", 2.4, 180, 35, 2.0)):
        ld = bpy.data.lights.new(HELPER + name, "SUN")
        ld.energy = energy
        ld.use_shadow = name == "Key"     # fill/rim shadows cause dirty streaks toward the camera
        setp(ld, "angle", math.radians(soft))
        lo_ = bpy.data.objects.new(HELPER + name, ld)
        scene.collection.objects.link(lo_)
        lo_.parent = pivot
        lo_.rotation_euler = (-orbit_dir(a.azim + d_az, el)).to_track_quat("-Z", "Y").to_euler()

    world = bpy.data.worlds.new(HELPER + "World")
    scene.world = world
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (*hex_linear(a.bg), 1.0)
    bg.inputs["Strength"].default_value = 1.0
    world.color = hex_linear(a.bg)

    if not a.transparent and a.engine != "workbench":   # floor: the contact shadow grounds the asset
        t = radius * 0.02
        bpy.ops.mesh.primitive_cube_add(size=1, location=(center.x, center.y, lo.z - t / 2))
        floor = bpy.context.active_object
        floor.name = HELPER + "Floor"
        floor.scale = (radius * 400, radius * 400, t)
        m = bpy.data.materials.new(HELPER + "Floor")
        col = [c * 1.15 for c in hex_linear(a.bg)]
        p = m.node_tree.nodes["Principled BSDF"]
        p.inputs["Base Color"].default_value = (*col, 1.0)
        p.inputs["Roughness"].default_value = 1.0
        m.diffuse_color = (*col, 1.0)
        floor.data.materials.append(m)
    return pivot, center, radius


def fit_camera(cam, pivot, lo, hi, a):
    """Adjusts distance/ortho_scale so the asset fills ~88% of the frame in ALL
    turntable angles (the scale is the same across frames — they can be compared)."""
    from bpy_extras.object_utils import world_to_camera_view
    scene = bpy.context.scene
    corners = [Vector((x, y, z)) for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (lo.z, hi.z)]
    n = max(a.turntable, 1)
    for _ in range(4):
        extent = 0.0
        for i in range(n):
            pivot.rotation_euler = (0, 0, math.radians(360 * i / n))
            bpy.context.view_layer.update()
            for c in corners:
                p = world_to_camera_view(scene, cam, c)
                extent = max(extent, abs(p.x - 0.5), abs(p.y - 0.5))
        k = extent / 0.44
        if abs(k - 1) < 0.01:
            break
        if cam.data.type == "ORTHO":
            cam.data.ortho_scale *= k
        else:
            cam.location *= k
    pivot.rotation_euler = (0, 0, 0)


def workbench_colors(objs):
    """Workbench in TEXTURE mode uses the active image node and the material's viewport color:
    make the Base Color texture active; for flat materials copy their color into it."""
    for o in objs:
        for slot in o.material_slots:
            m = slot.material
            if not m or not m.node_tree:
                continue
            bsdf = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
            if not bsdf:
                continue
            sock = bsdf.inputs["Base Color"]
            if sock.is_linked and sock.links[0].from_node.type == "TEX_IMAGE":
                m.node_tree.nodes.active = sock.links[0].from_node
            else:
                m.diffuse_color = tuple(sock.default_value)


def setup_render(a):
    scene = bpy.context.scene
    r = scene.render
    r.resolution_x = r.resolution_y = a.size
    r.resolution_percentage = 100
    r.film_transparent = a.transparent
    r.image_settings.file_format = "PNG"
    r.image_settings.color_mode = "RGBA" if a.transparent else "RGB"
    vs = scene.view_settings
    setp(vs, "view_transform", "Standard")   # art bible palette without AgX washing it out
    setp(vs, "look", "None")
    if a.engine == "workbench":
        r.engine = "BLENDER_WORKBENCH"
        sh = scene.display.shading
        sh.light = "STUDIO"
        sh.color_type = "TEXTURE"
        sh.show_cavity = True
        setp(sh, "cavity_type", "BOTH")
        sh.show_shadows = False          # Workbench stencil shadows cause artifacts; cavity is enough
        sh.show_object_outline = False
        setp(scene.display, "render_aa", "16")
    elif a.engine == "eevee":
        r.engine = "BLENDER_EEVEE"
        e = scene.eevee
        setp(e, "taa_render_samples", 64)
        setp(e, "use_shadows", True)
        setp(e, "use_raytracing", True)       # reflections and AO in EEVEE 4.2+/5.x
        setp(e, "use_fast_gi", True)
    else:
        r.engine = "CYCLES"
        c = scene.cycles
        c.samples = 64
        setp(c, "use_denoising", True)
        setp(c, "device", "GPU")
        prefs = bpy.context.preferences.addons.get("cycles")
        if prefs:
            try:
                prefs.preferences.compute_device_type = "METAL"
                prefs.preferences.get_devices()
                for d in prefs.preferences.devices:
                    d.use = True
            except Exception:
                c.device = "CPU"


def render(path):
    bpy.context.scene.render.filepath = path
    t = time.time()
    bpy.ops.render.render(write_still=True)
    if not os.path.isfile(path):
        fail(f"render did not write {path}")
    return time.time() - t


def render_set(a, name, objs):
    lo, hi, tris = bounds(objs)
    shots = []
    if a.keep_scene:
        if bpy.context.scene.camera is None:
            fail("--keep-scene: no camera in the scene")
        setup_render(a)
        p = os.path.join(a.out, f"{name}.png")
        shots.append((p, render(p)))
    else:
        setup_render(a)                  # before framing: fit uses the frame resolution
        pivot, center, radius = setup_studio(a, lo, hi)
        if a.engine == "workbench":
            workbench_colors(objs)
        n = max(a.turntable, 1)
        for i in range(n):
            pivot.rotation_euler = (0, 0, math.radians(360 * i / n))
            p = os.path.join(a.out, f"{name}_{i:02d}.png" if a.turntable else f"{name}.png")
            shots.append((p, render(p)))
    size = [round(v, 3) for v in (hi - lo)]
    for p, dt in shots:
        print(f"  {p}  ({dt:.2f} s)")
    return dict(name=name, tris=tris, size_m=size, files=[p for p, _ in shots],
                seconds=round(sum(dt for _, dt in shots), 2))


def main():
    a = parse_args()
    a.out = os.path.abspath(os.path.expanduser(a.out))
    os.makedirs(a.out, exist_ok=True)
    results = []
    if a.glb:
        for path in a.glb:
            path = os.path.abspath(os.path.expanduser(path))
            if not os.path.isfile(path):
                fail(f"no such file {path}")
            bpy.ops.wm.read_factory_settings(use_empty=True)
            objs = target_objects(a, import_model(path))
            name = a.name if (a.name and len(a.glb) == 1) else os.path.splitext(os.path.basename(path))[0]
            print(f"PREVIEW {name} ({a.engine}, {a.size}px)")
            results.append(render_set(a, name, objs))
    else:
        if not bpy.data.filepath:
            fail("give a .blend before -P or --glb after --")
        objs = target_objects(a, [])
        name = a.name or os.path.splitext(os.path.basename(bpy.data.filepath))[0]
        print(f"PREVIEW {name} ({a.engine}, {a.size}px)")
        results.append(render_set(a, name, objs))
    for r in results:
        print("RESULT " + json.dumps(r, ensure_ascii=False))


try:
    main()
except SystemExit:
    raise
except Exception as e:
    import traceback
    traceback.print_exc()
    fail(f"{type(e).__name__}: {e}")
