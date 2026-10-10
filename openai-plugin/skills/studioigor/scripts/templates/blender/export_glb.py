"""Export an asset from .blend to GLB (or FBX) with per-engine presets.

Run (headless, safe in parallel — the .blend is not saved):
  Blender -b file.blend --python-exit-code 1 -P export_glb.py -- --out path.glb
      [--collection NAME] [--engine godot|unity|web] [--apply-modifiers | --no-apply-modifiers]
      [--draco] [--meshopt] [--webp] [--no-apply-transforms] [--max-tris N] [--max-kb N]

  --collection   export only this collection (with nested ones); otherwise the whole scene
  --engine       godot (default) | unity | web — settings preset, see PRESETS
  --out *.fbx    writes FBX instead of GLB with axes/scale for Unity (no 100x and -90°)
  --draco/--meshopt  geometry compression — web only (Godot/Unity convert the mesh
                 on import; compression does not shrink the build there and may fail to import)
  --webp         textures as WebP (web). Not for Closest palettes: lossy ruins the colors.
  --max-tris/--max-kb  budget: exceeding it → exit code 3

Prints objects, triangles, materials, textures, dimensions, file size and a
`RESULT {json}` line for machine reading. Exit code: 0 — ok, 1 — error,
3 — budget exceeded.
"""
import argparse
import json
import os
import sys
import time

import bpy

EXPORT_TYPES = {"MESH", "ARMATURE", "EMPTY", "CURVE", "SURFACE", "META", "FONT"}
# Godot import suffixes: collision/navmesh are not rendered, their triangles are counted separately
HINTS = ("-colonly", "-convcolonly", "-col", "-convcol", "-navmesh", "-occ", "-occonly")


def is_hint(o):
    return any(h in o.name for h in HINTS)

# Common glTF base: +Y up (converted from Blender Z-up), modifiers by flag,
# animations as separate actions (separate clips in the engine).
GLTF_BASE = dict(
    export_format="GLB",
    export_yup=True,
    export_texcoords=True,
    export_normals=True,
    export_materials="EXPORT",
    export_image_format="AUTO",
    export_animations=True,
    export_animation_mode="ACTIONS",
    export_skins=True,
    export_morph=True,
    export_extras=True,        # custom properties → extras (Godot puts them into metadata)
    export_cameras=False,
    export_lights=False,
)

PRESETS = {
    # Godot 4: generates LODs, tangents and compression on import itself; -col/-colonly suffixes
    # in object names become collisions. Geometry compression is not needed.
    "godot": dict(),
    # Unity: GLB via the glTFast package (com.unity.cloud.gltfast). Let Unity compute tangents.
    "unity": dict(),
    # three.js / Babylon: the GLB ships in the build as is — size matters.
    "web": dict(export_shared_accessors=True),
}

FBX_UNITY = dict(
    apply_scale_options="FBX_SCALE_ALL",
    apply_unit_scale=True,
    axis_forward="-Z",
    axis_up="Y",
    bake_space_transform=True,
    object_types={"MESH", "ARMATURE", "EMPTY"},
    mesh_smooth_type="FACE",
    add_leaf_bones=False,
    use_armature_deform_only=True,
    bake_anim=True,
    path_mode="COPY",
    embed_textures=True,
)


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser(prog="export_glb.py")
    ap.add_argument("--out", required=True)
    ap.add_argument("--collection", default="")
    ap.add_argument("--engine", choices=sorted(PRESETS), default="godot")
    ap.add_argument("--apply-modifiers", action=argparse.BooleanOptionalAction, default=True,
                    help="apply modifiers on export (default yes; the .blend is not changed)")
    ap.add_argument("--apply-transforms", action=argparse.BooleanOptionalAction, default=True,
                    help="apply rotation/scale where it is safe (default yes)")
    ap.add_argument("--draco", action="store_true")
    ap.add_argument("--meshopt", action="store_true")
    ap.add_argument("--webp", action="store_true")
    ap.add_argument("--max-tris", type=int, default=0)
    ap.add_argument("--max-kb", type=int, default=0)
    return ap.parse_args(argv)


def fail(msg, code=1):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.stdout.flush()
    sys.exit(code)


def collect_objects(coll_name):
    scene = bpy.context.scene
    if coll_name:
        coll = bpy.data.collections.get(coll_name)
        if coll is None:
            names = ", ".join(c.name for c in bpy.data.collections) or "none"
            fail(f"collection \"{coll_name}\" not found. Available: {names}")
        objs = list(coll.all_objects)
    else:
        objs = list(scene.objects)
    vl = bpy.context.view_layer
    return [o for o in objs if o.type in EXPORT_TYPES and o.name in vl.objects
            and not o.hide_render]


def is_identity_rs(o):
    m = o.matrix_basis.to_3x3()
    return all(abs(m[i][j] - (1.0 if i == j else 0.0)) < 1e-6 for i in range(3) for j in range(3))


def apply_transforms_safely(objs):
    """rotation+scale → into the mesh. Skip where it breaks data: animated
    objects and armatures (clips would break), armature children (skinning), shared meshes
    (instancing). Location is left alone — the scene layout is preserved."""
    skipped, applied = [], []
    for o in objs:
        if is_identity_rs(o):
            continue
        reason = None
        if o.type != "MESH":
            reason = o.type.lower()
        elif o.animation_data and o.animation_data.action:
            reason = "animated"
        elif o.parent and o.parent.type == "ARMATURE":
            reason = "skinning"
        elif o.data.users > 1:
            reason = "shared mesh (instances)"
        if reason:
            skipped.append(f"{o.name} ({reason})")
            continue
        bpy.ops.object.select_all(action="DESELECT")
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        applied.append(o.name)
    if applied:
        print(f"  transforms applied: {len(applied)} objects")
    if skipped:
        print(f"  transforms NOT applied (the exporter handles them itself): {', '.join(skipped)}")


def stats(objs, apply_mods):
    dg = bpy.context.evaluated_depsgraph_get()
    tris = verts = col_tris = 0
    mats, images = set(), set()
    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    warnings = []
    for o in objs:
        if o.type != "MESH":
            continue
        src = o.evaluated_get(dg) if apply_mods else o
        me = src.to_mesh()
        me.calc_loop_triangles()
        if "colonly" in o.name:          # -colonly / -convcolonly: invisible collision
            col_tris += len(me.loop_triangles)
            src.to_mesh_clear()
            continue
        tris += len(me.loop_triangles)
        verts += len(me.vertices)
        mw = o.matrix_world
        for v in me.vertices:
            w = mw @ v.co
            for i in range(3):
                lo[i] = min(lo[i], w[i])
                hi[i] = max(hi[i], w[i])
        src.to_mesh_clear()
        used = [s.material for s in o.material_slots if s.material]
        if not used:
            warnings.append(f"{o.name}: no material")
        if len(o.data.uv_layers) == 0 and used:
            warnings.append(f"{o.name}: no UV")
        for m in used:
            mats.add(m.name)
            if m.node_tree:
                for n in m.node_tree.nodes:
                    if n.type == "TEX_IMAGE" and n.image:
                        images.add((n.image.name, n.image.size[0], n.image.size[1]))
        if any(abs(s - o.scale[0]) > 1e-4 for s in o.scale):
            warnings.append(f"{o.name}: non-uniform scale {tuple(round(s, 3) for s in o.scale)}")
    if tris == 0:
        dims = [0, 0, 0]
    else:
        dims = [round(hi[i] - lo[i], 3) for i in range(3)]
    return dict(tris=tris, verts=verts, collision_tris=col_tris, materials=sorted(mats),
                textures=[f"{n} {w}x{h}" for n, w, h in sorted(images)],
                size_m=dims, min_z=round(lo[2], 4) if tris else 0.0), warnings


def main():
    a = parse_args()
    t0 = time.time()
    out = os.path.abspath(os.path.expanduser(a.out))
    ext = os.path.splitext(out)[1].lower()
    if ext not in {".glb", ".gltf", ".fbx"}:
        fail("--out must end with .glb, .gltf or .fbx")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    objs = collect_objects(a.collection)
    if not any(o.type == "MESH" for o in objs):
        fail("nothing to export: no visible meshes" + (f" in \"{a.collection}\"" if a.collection else ""))

    if a.apply_transforms:
        apply_transforms_safely(objs)

    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.hide_set(False)
        o.select_set(True)
    bpy.context.view_layer.objects.active = next(o for o in objs if o.type == "MESH")

    if (a.draco or a.meshopt or a.webp) and a.engine != "web":
        print(f"  WARNING: --draco/--meshopt/--webp only make sense for web; ignoring them for {a.engine} "
              "(the engine converts meshes and textures on import)")
        a.draco = a.meshopt = a.webp = False
    if a.draco and a.meshopt:
        fail("pick one: --draco or --meshopt")

    if ext == ".fbx":
        if a.engine != "unity":
            print("  WARNING: the FBX preset targets Unity; for Godot/web use GLB")
        bpy.ops.export_scene.fbx(filepath=out, use_selection=True,
                                 use_mesh_modifiers=a.apply_modifiers, **FBX_UNITY)
    else:
        kw = dict(GLTF_BASE, **PRESETS[a.engine])
        kw.update(filepath=out, use_selection=True, export_apply=a.apply_modifiers)
        if ext == ".gltf":
            kw["export_format"] = "GLTF_SEPARATE"
        if a.draco:
            # default quantization (pos 14 bits) visibly shifts vertices only in large
            # worlds; safe for props and characters. three.js: DRACOLoader is required.
            kw.update(export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6)
        if a.meshopt:
            # three.js: GLTFLoader.setMeshoptDecoder(MeshoptDecoder)
            kw.update(export_meshopt_compression_enable=True)
        if a.webp:
            kw.update(export_image_format="WEBP", export_image_quality=90)
        bpy.ops.export_scene.gltf(**kw)

    if not os.path.isfile(out) or os.path.getsize(out) == 0:
        fail(f"export did not create the file {out}")
    if ext == ".glb":
        with open(out, "rb") as f:
            if f.read(4) != b"glTF":
                fail("the file does not look like GLB (no glTF header)")

    s, warnings = stats(objs, a.apply_modifiers)
    kb = os.path.getsize(out) / 1024
    s.update(file=out, kb=round(kb, 1), engine=a.engine, objects=len(objs),
             seconds=round(time.time() - t0, 2))
    print(f"EXPORT: {out}")
    print(f"  engine {a.engine} · objects {len(objs)} · triangles {s['tris']} · vertices {s['verts']}"
          + (f" · collision {s['collision_tris']} tris" if s["collision_tris"] else ""))
    print(f"  materials {len(s['materials'])}: {', '.join(s['materials']) or '-'}")
    print(f"  textures {len(s['textures'])}: {', '.join(s['textures']) or '-'}")
    print(f"  dimensions (m) X{s['size_m'][0]} Y{s['size_m'][1]} Z{s['size_m'][2]} · bottom z={s['min_z']}")
    print(f"  file {kb:.1f} KB · {s['seconds']} s")
    if a.engine != "godot" and any(is_hint(o) for o in objs):
        warnings.append("there are objects with Godot suffixes (-col/-colonly…): in this engine they "
                        "become visible meshes — exclude them via a collection or delete them")
    if abs(s["min_z"]) > 0.01 and len(objs) == 1:
        warnings.append(f"object bottom is at z={s['min_z']}, not 0: check the origin (props — bottom center)")
    for w in warnings:
        print(f"  WARNING: {w}")
    print("RESULT " + json.dumps(s, ensure_ascii=False))
    over = []
    if a.max_tris and s["tris"] > a.max_tris:
        over.append(f"triangles {s['tris']} > {a.max_tris}")
    if a.max_kb and kb > a.max_kb:
        over.append(f"size {kb:.0f} KB > {a.max_kb} KB")
    if over:
        fail("budget exceeded: " + "; ".join(over), code=3)


try:
    main()
except SystemExit:
    raise
except Exception as e:  # any exporter error → non-zero code, even without --python-exit-code
    import traceback
    traceback.print_exc()
    fail(f"{type(e).__name__}: {e}")
