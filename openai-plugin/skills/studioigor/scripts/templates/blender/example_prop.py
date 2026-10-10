"""Example pattern: a procedural stylized low-poly prop — a lantern on a post.

Adapt it to your asset: change PALETTE (from ART_BIBLE), the sizes in meters and
the build() function. Techniques that carry over to any prop:
  - real scale: 1 unit = 1 m, the model faces -Y (Front), bottom at z=0;
  - one mesh and ONE material: a 16x16 palette atlas (Closest), each part
    is colored by moving its UVs to the center of its cell — like Kenney/KayKit/Quaternius;
    glow is a second atlas in Emission Color (still one material, one draw call);
  - bevel (angle limit, harden normals) + Weighted Normal: big bevels catch the light;
  - origin at bottom center; rotation/scale applied; names SM_<Name>, M_, T_;
  - optional collision for Godot: SM_<Name>-convcolonly (a simple convex proxy).

Run:
  Blender -b --factory-startup --python-exit-code 1 -P example_prop.py -- \
      --out-dir DIR [--name SM_Lantern] [--collision]
Result: DIR/<name>.blend (palette packed inside) and DIR/<name>.glb.
Preview: Blender -b -P preview.py -- --glb DIR/<name>.glb --out DIR/preview
"""
import argparse
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

# Palette: role → hex. Take it from ART_BIBLE.md; order = atlas cell index.
PALETTE = {
    "stone": "#6f6a64",
    "stone_dark": "#4a4643",
    "wood": "#6b4a2f",
    "metal": "#2b2f36",
    "metal_edge": "#4d5560",
    "glass": "#ffcf6b",   # glows
}
EMISSIVE = {"glass": 3.0}  # role → glow strength (Emission Strength in glTF)
GRID = 4                   # 4x4 cells = up to 16 colors
CELL_PX = 4                # pixels per cell → 16x16 atlas


# ------------------------------------------------------------------ scene

def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.unit_settings.system = "METRIC"
    s.unit_settings.scale_length = 1.0


def hex_rgba(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)] + [1.0]


# ------------------------------------------------------------------ material

def palette_material(name="M_Palette"):
    """One material for all props: a color atlas + a glow atlas (both Closest)."""
    size = GRID * CELL_PX
    base = bpy.data.images.new("T_Palette", size, size, alpha=False)
    emit = bpy.data.images.new("T_Palette_Emit", size, size, alpha=False)
    bpx = [0.0] * (size * size * 4)
    epx = [0.0] * (size * size * 4)
    for k, (role, hx) in enumerate(PALETTE.items()):
        cx, cy = k % GRID, k // GRID
        col = hex_rgba(hx)
        ecol = col if role in EMISSIVE else [0, 0, 0, 1]
        for y in range(cy * CELL_PX, (cy + 1) * CELL_PX):
            for x in range(cx * CELL_PX, (cx + 1) * CELL_PX):
                i = (y * size + x) * 4
                bpx[i:i + 4] = col   # byte image: values in sRGB, like hex
                epx[i:i + 4] = ecol
    base.pixels = bpx
    emit.pixels = epx
    base.pack()
    emit.pack()

    mat = bpy.data.materials.new(name)
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.85
    bsdf.inputs["Metallic"].default_value = 0.0
    texs = []
    for img, socket, y in ((emit, "Emission Color", -200), (base, "Base Color", 300)):
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = img
        tex.interpolation = "Closest"   # no blurring between cells
        tex.location = (-420, y)
        nt.links.new(tex.outputs["Color"], bsdf.inputs[socket])
        texs.append(tex)
    nt.nodes.active = texs[-1]          # the viewport (Solid → Texture) shows the palette colors
    bsdf.inputs["Emission Strength"].default_value = max(EMISSIVE.values(), default=0.0)
    return mat


def swatch_uv(role):
    k = list(PALETTE).index(role)
    return Vector(((k % GRID + 0.5) / GRID, (k // GRID + 0.5) / GRID))


# ------------------------------------------------------------------ geometry

class Builder:
    """Builds all parts into one bmesh; each part has its own palette color."""

    def __init__(self):
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new("UVMap")

    def _paint(self, faces, role):
        uv = swatch_uv(role)
        for f in faces:
            for loop in f.loops:
                loop[self.uv].uv = uv

    def box(self, role, size, loc, taper=1.0):
        """Box size=(x,y,z) m, bottom at loc. taper<1 narrows the top (posts, pedestals)."""
        before = set(self.bm.faces)
        m = Matrix.Translation(Vector(loc) + Vector((0, 0, size[2] / 2))) @ Matrix.Diagonal(
            Vector((*size, 1.0)))
        geom = bmesh.ops.create_cube(self.bm, size=1.0, matrix=m)
        if taper != 1.0:
            top = max(v.co.z for v in geom["verts"])
            c = Vector(loc)
            for v in geom["verts"]:
                if abs(v.co.z - top) < 1e-6:
                    v.co.x = c.x + (v.co.x - c.x) * taper
                    v.co.y = c.y + (v.co.y - c.y) * taper
        self._paint(set(self.bm.faces) - before, role)

    def pyramid(self, role, radius, height, loc, sides=4):
        before = set(self.bm.faces)
        m = Matrix.Translation(Vector(loc) + Vector((0, 0, height / 2))) @ Matrix.Rotation(
            math.pi / sides, 4, "Z")
        bmesh.ops.create_cone(self.bm, cap_ends=True, segments=sides, radius1=radius,
                              radius2=0.0, depth=height, matrix=m)
        self._paint(set(self.bm.faces) - before, role)

    def to_object(self, name):
        me = bpy.data.meshes.new(name)
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        self.bm.to_mesh(me)
        self.bm.free()
        obj = bpy.data.objects.new(name, me)
        bpy.context.collection.objects.link(obj)
        return obj


def build(b):
    """Lantern ~2.9 m: pedestal, tapering post, cage with glass, roof."""
    b.box("stone_dark", (0.56, 0.56, 0.12), (0, 0, 0))
    b.box("stone", (0.42, 0.42, 0.22), (0, 0, 0.12), taper=0.8)
    b.box("wood", (0.16, 0.16, 2.0), (0, 0, 0.34), taper=0.75)
    b.box("metal", (0.34, 0.34, 0.06), (0, 0, 2.34))            # tray
    for sx in (-1, 1):                                          # 4 cage posts
        for sy in (-1, 1):
            b.box("metal_edge", (0.045, 0.045, 0.40), (sx * 0.145, sy * 0.145, 2.40))
    b.box("glass", (0.25, 0.25, 0.38), (0, 0, 2.41))            # glowing glass
    b.box("metal", (0.36, 0.36, 0.05), (0, 0, 2.80))            # top frame
    b.pyramid("metal", 0.30, 0.22, (0, 0, 2.85))                # roof
    b.box("metal_edge", (0.05, 0.05, 0.08), (0, 0, 3.05))       # finial


# ------------------------------------------------------------------ finishing

def finish(obj, bevel_width=0.012):
    """Bevels + weighted normals; smooth shading so the custom normals work."""
    obj.data.shade_smooth()
    bev = obj.modifiers.new("Bevel", "BEVEL")
    bev.width = bevel_width          # ~2–5% of the thickness of small parts
    bev.segments = 1
    bev.limit_method = "ANGLE"
    bev.angle_limit = math.radians(40)
    bev.harden_normals = True
    wn = obj.modifiers.new("WeightedNormal", "WEIGHTED_NORMAL")
    wn.keep_sharp = True


def origin_to_base(obj):
    """Origin at the bbox bottom center: in the engine the prop stands on the floor at (x, 0, z)."""
    xs = [v.co.x for v in obj.data.vertices]
    ys = [v.co.y for v in obj.data.vertices]
    zmin = min(v.co.z for v in obj.data.vertices)
    off = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, zmin))
    obj.data.transform(Matrix.Translation(-off))
    obj.location = (0, 0, 0)


def collision_box(name, size, parent):
    """Godot: -convcolonly → StaticBody3D + ConvexPolygonShape3D, the proxy is not rendered.
    (-colonly would give ConcavePolygonShape3D — more expensive and static only.)"""
    b = Builder()
    b.box(list(PALETTE)[0], size, (0, 0, 0))
    col = b.to_object(f"{name}-convcolonly")
    col.parent = parent
    col.display_type = "WIRE"
    return col


def tri_count(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    me = obj.evaluated_get(dg).to_mesh()
    me.calc_loop_triangles()
    n = len(me.loop_triangles)
    obj.evaluated_get(dg).to_mesh_clear()
    return n


# ------------------------------------------------------------------ main

def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser(prog="example_prop.py")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--name", default="SM_Lantern")
    ap.add_argument("--collision", action="store_true", help="add SM_<name>-convcolonly for Godot")
    a = ap.parse_args(argv)
    out_dir = os.path.abspath(os.path.expanduser(a.out_dir))
    os.makedirs(out_dir, exist_ok=True)

    reset_scene()
    coll = bpy.data.collections.new("Props")
    bpy.context.scene.collection.children.link(coll)
    bpy.context.view_layer.active_layer_collection = \
        bpy.context.view_layer.layer_collection.children["Props"]

    b = Builder()
    build(b)
    obj = b.to_object(a.name)
    obj.data.materials.append(palette_material())
    origin_to_base(obj)
    finish(obj)
    if a.collision:
        collision_box(a.name, (0.56, 0.56, 3.13), obj)

    blend = os.path.join(out_dir, f"{a.name}.blend")
    glb = os.path.join(out_dir, f"{a.name}.glb")
    bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True)

    bpy.ops.object.select_all(action="DESELECT")
    for o in coll.all_objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=glb, export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True, export_materials="EXPORT",
                              export_image_format="AUTO", export_extras=True)

    dims = obj.dimensions
    print(f"DONE: {a.name} · triangles {tri_count(obj)} · materials {len(obj.data.materials)}"
          f" · {dims.x:.2f}x{dims.y:.2f}x{dims.z:.2f} m")
    print(f"  {blend} ({os.path.getsize(blend) / 1024:.1f} KB)")
    print(f"  {glb} ({os.path.getsize(glb) / 1024:.1f} KB)")


main()
