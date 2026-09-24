"""Reproducible, self-contained soup asset. Run with Blender 4.5+:
blender --background --python assets/blender/create_soup.py
Optional: SOUP_RENDER=/tmp/soup.png to render the source scene.
All geometry and texture maps are authored here; no external assets are used.
"""
import bpy
import math
import os
import random
from pathlib import Path

import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
random.seed(24)
rng = np.random.default_rng(24)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 48
scene.cycles.use_denoising = True
scene.world.color = (0.22, 0.22, 0.22)
model = bpy.data.collections.new('SOUP — export geometry')
scene.collection.children.link(model)


def image(name, rgb, data=False):
    h, w = rgb.shape[:2]
    img = bpy.data.images.new(name, width=w, height=h, alpha=False)
    if data:
        img.colorspace_settings.name = 'Non-Color'
    rgba = np.ones((h, w, 4), dtype=np.float32)
    rgba[:, :, :3] = np.clip(rgb, 0, 1)
    img.pixels.foreach_set(rgba.ravel())
    img.pack()
    return img


def texture_material(name, colors, roughness, style='food', coat=0.0, size=512):
    # Seamless multiscale variation, exported as actual glTF texture maps.
    y, x = np.mgrid[0:size, 0:size] / size
    n = np.zeros((size, size))
    for frequency, strength in [(2, .20), (5, .12), (11, .06), (29, .025), (71, .015)]:
        for _ in range(4):
            a, b = rng.integers(1, frequency + 1, 2)
            n += strength * np.sin(2 * math.pi * (a*x + b*y) + rng.uniform(0, 6.28)) / 4
    grain = rng.random((size, size))
    t = np.clip(.5 + n, 0, 1)
    height = n * .2 + (grain - .5) * .012
    if style == 'ceramic':
        speckle = np.clip((grain - .975) * 32, 0, .78)
        t -= speckle
        t += .028 * np.sin(y * 2 * math.pi * 90 + n * 2)
        height = n * .1 + speckle * .03
    elif style == 'broth':
        flow = np.sin(x * 20 + np.sin(y * 17) + n * 30) * np.cos(y * 13 + n * 18)
        t += .10 * flow
        height = n * .035 + .005 * flow
    elif style == 'mushroom':
        t += .09 * np.sin(x * 150 + n * 30)
        height += .015 * np.sin(x * 150 + n * 30)
    elif style == 'yolk':
        t += (grain - .5) * .18
        height += (grain - .5) * .12
    rgb = np.array(colors[0])[None, None, :] * (1-t[:, :, None]) + np.array(colors[1])[None, None, :] * t[:, :, None]
    # Blender image pixels are linear; our authored palette is sRGB.
    rgb = np.where(rgb <= .04045, rgb / 12.92, ((rgb + .055) / 1.055) ** 2.4)
    color_map = image(name + ' • base color', rgb)
    dx = np.roll(height, -1, 1) - np.roll(height, 1, 1)
    dy = np.roll(height, -1, 0) - np.roll(height, 1, 0)
    normal = np.stack((-dx * 5, -dy * 5, np.ones_like(dx)), -1)
    normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
    normal_map = image(name + ' • micro normal', normal*.5+.5, True)
    rough = np.clip(roughness + n * .15, .08, .95)
    rough_map = image(name + ' • roughness', np.stack((rough, rough, rough), -1), True)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes.get('Principled BSDF')
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Coat Weight'].default_value = coat
    bsdf.inputs['Coat Roughness'].default_value = .18
    for label, img, socket in [('Color', color_map, 'Base Color'), ('Roughness', rough_map, 'Roughness')]:
        node = nodes.new('ShaderNodeTexImage')
        node.image = img
        node.label = label
        links.new(node.outputs['Color'], bsdf.inputs[socket])
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = normal_map
    normal_node = nodes.new('ShaderNodeNormalMap')
    links.new(tex.outputs['Color'], normal_node.inputs['Color'])
    links.new(normal_node.outputs['Normal'], bsdf.inputs['Normal'])
    mat.diffuse_color = (*np.mean(colors, axis=0), 1)
    return mat


ceramic = texture_material('01 • speckled ivory stoneware', [(.72,.66,.54),(.96,.94,.87)], .29, 'ceramic', .32, 1024)
rim = texture_material('02 • toasted clay rim and foot', [(.15,.08,.035),(.39,.27,.12)], .42, 'ceramic', .2, 256)
broth = texture_material('03 • golden miso broth', [(.49,.21,.06),(.85,.57,.22)], .28, 'broth', .18, 1024)
noodle = texture_material('04 • fresh wheat noodles', [(.87,.69,.39),(.99,.89,.64)], .39, coat=.18, size=256)
white = texture_material('05 • marinated egg white', [(.94,.91,.82),(.99,.98,.93)], .32, coat=.18, size=256)
yolk = texture_material('06 • jammy egg yolk', [(1,.60,.01),(1,.79,.08)], .26, 'yolk', .23, 256)
cap = texture_material('07 • shiitake caps', [(.19,.075,.026),(.48,.28,.12)], .56, 'mushroom', .08)
gill = texture_material('08 • mushroom flesh', [(.39,.25,.12),(.78,.63,.37)], .48, 'mushroom', size=256)
green = texture_material('09 • scallion greens', [(.08,.26,.019),(.35,.58,.08)], .36, coat=.1, size=256)
lightgreen = texture_material('10 • scallion hearts', [(.37,.53,.12),(.71,.78,.35)], .39, size=256)
chili = texture_material('11 • chili and aromatic oil', [(.18,.019,.002),(.62,.085,.008)], .23, coat=.3, size=256)
sesame = texture_material('12 • toasted sesame', [(.48,.27,.07),(.90,.74,.40)], .51, size=128)


def finish(obj, name, mat):
    obj.name = name
    for collection in list(obj.users_collection):
        collection.objects.unlink(obj)
    model.objects.link(obj)
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj


def mesh(name, verts, faces, mat, uv=None):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    model.objects.link(obj)
    data.materials.append(mat)
    layer = data.uv_layers.new(name='UVMap')
    for poly in data.polygons:
        poly.use_smooth = True
        for i in poly.loop_indices:
            vi = data.loops[i].vertex_index
            layer.data[i].uv = uv[vi] if uv else (verts[vi][0]*.5+.5, verts[vi][1]*.5+.5)
    return obj


def lathe(name, profile, mat, segments=112):
    verts, faces, uv = [], [], []
    for k, (r, z) in enumerate(profile):
        for j in range(segments+1):
            a = j/segments * math.tau
            # Subtle throwing irregularities; continuous across the UV seam.
            wobble = 1 + .0018*math.sin(a*7+z*12) + .001*math.cos(a*11)
            verts.append((r*math.cos(a)*wobble,r*math.sin(a)*wobble,z))
            uv.append((j/segments, k/(len(profile)-1)))
            if k and j:
                b = k*(segments+1)+j
                faces.append((b-1,b,b-segments-1,b-segments-2))
    return mesh(name, verts, faces, mat, uv)


# A closed wall: underside -> thrown outer body -> rounded lip -> inner well.
profile = [(.001,.055),(.35,.055),(.43,.065),(.47,.085),(.49,.11),(.52,.13),(.58,.16),(.66,.20),(.75,.265),(.83,.33),(.90,.40),(.96,.475),(1.015,.55),(1.055,.615),(1.087,.674),(1.101,.710),(1.096,.729),(1.079,.738),(1.061,.732),(1.045,.714),(1.030,.680),(.999,.616),(.958,.548),(.907,.477),(.848,.407),(.774,.34),(.690,.283),(.594,.239),(.50,.211),(.40,.194),(.25,.186),(.001,.186)]
lathe('Hand-thrown bowl', profile, ceramic)
lathe('Exposed clay foot',[(.35,.057),(.35,.01),(.37,.0),(.425,.0),(.449,.016),(.453,.070)],rim,96)
lathe('Fine iron glazed lip',[(1.086,.726),(1.090,.732),(1.080,.739),(1.068,.736)],rim,112)

# Gently rippled, opaque rich broth; the outside meniscus touches the inner bowl.
verts, faces = [(0,0,.626)], []
N, R = 128, 22
for k in range(1,R+1):
    r = .992*k/R
    for j in range(N):
        a = math.tau*j/N
        z = .626 + .0015*math.sin(r*38+a*3)*math.sin(r*19-a*5)
        z += .007*(r/.992)**30
        verts.append((r*math.cos(a),r*math.sin(a),z))
        if k == 1:
            faces.append((0,1+j,1+(j+1)%N))
        else:
            b = 1+(k-1)*N
            p = b-N
            faces.append((p+j,b+j,b+(j+1)%N,p+(j+1)%N))
mesh('Broth with raised meniscus',verts,faces,broth)


def ellipsoid(name, loc, scale, mat, rotation=(0,0,0), seg=24, rings=12):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, location=loc)
    obj = finish(bpy.context.object,name,mat)
    obj.scale=scale
    obj.rotation_euler=rotation
    return obj


def tube(name, points, radius, mat, sides=7):
    verts, faces, uv = [], [], []
    for i, point in enumerate(points):
        p = Vector(point)
        tangent = Vector(points[min(i+1,len(points)-1)]) - Vector(points[max(i-1,0)])
        tangent.normalize()
        right = tangent.cross(Vector((0,0,1))).normalized()
        if right.length < .1:
            right = Vector((1,0,0))
        up = right.cross(tangent).normalized()
        for j in range(sides+1):
            a=math.tau*j/sides
            v=p+radius*(math.cos(a)*right+math.sin(a)*up)
            verts.append(tuple(v)); uv.append((j/sides,i/len(points)*4))
            if i and j:
                b=i*(sides+1)+j
                faces.append((b-1,b,b-sides-1,b-sides-2))
    return mesh(name,verts,faces,mat,uv)


# Loose noodles follow varied curls, dipping under the stock instead of hovering.
for i in range(29):
    pts=[]
    phase=random.uniform(0,math.tau)
    radius=random.uniform(.12,.56)
    cx,cy=random.uniform(-.16,.16),random.uniform(-.15,.13)
    stretch=random.uniform(.55,1.0)
    turns=random.uniform(.70,1.35)
    for j in range(86):
        t=j/85
        a=phase+t*math.tau*turns
        r=radius+.06*math.sin(3*a+i)+.025*math.sin(7*a+i)
        pts.append((cx+r*math.cos(a),cy+r*stretch*math.sin(a),.628+.027*math.sin(2*a+i)+.014*math.sin(5*a+i)))
    tube('Wavy noodle %02d'%i,pts,random.uniform(.010,.014),noodle)

# Two real half-eggs: a curved underside and a softly irregular, nearly flat cut face.
for cx,cy,angle in [(-.38,-.22,-.55),(-.57,.18,-.30)]:
    ca,sa=math.cos(angle),math.sin(angle)
    def eggpoint(x,y,z):
        return (cx+x*ca-y*sa,cy+x*sa+y*ca,z+.72+y*.15)
    v,f,uv=[],[],[]
    for k in range(15):
        t=-math.pi/2+k/14*math.pi/2
        for j in range(49):
            a=j/48*math.tau
            x=.217*math.cos(t)*math.cos(a)*(1+.08*math.sin(a))
            y=.29*math.cos(t)*math.sin(a)
            v.append(eggpoint(x,y,.16*math.sin(t)))
            uv.append((j/48,k/14))
            if k and j:
                b=k*49+j
                f.append((b-1,b,b-49,b-50))
    mesh('Egg curved underside',v,f,white,uv)
    v=[eggpoint(0,0,.014)]; f=[]
    for k in range(1,9):
        r=k/8
        for j in range(64):
            a=j/64*math.tau
            v.append(eggpoint(.217*r*math.cos(a)*(1+.08*math.sin(a)),.29*r*math.sin(a),.014*(1-r*r)))
            if k==1: f.append((0,1+j,1+(j+1)%64))
            else:
                b=1+(k-1)*64; p=b-64
                f.append((p+j,b+j,b+(j+1)%64,p+(j+1)%64))
    mesh('Tender egg cut face',v,f,white)
    # Separate yolk gives the glistening recessed center a readable edge.
    loc=eggpoint(0,-.025,.018)
    ellipsoid('Soft orange yolk',loc,(.137,.16,.024),yolk,(.15*ca,.15*sa,angle),40,16)

# Shiitakes with softly lobed caps, scored tops and actual radial gills.
for cx,cy,rad,rot in [(.34,.43,.235,.3),(.62,.21,.185,-.55),(.23,.62,.16,.7)]:
    ellipsoid('Shiitake cap',(cx,cy,.70),(rad,rad*.83,.095),cap,(.06,-.10,rot),32,14)
    ellipsoid('Shiitake underside',(cx,cy,.665),(rad*.95,rad*.79,.035),gill,seg=24)
    for j in range(22):
        a=math.tau*j/22
        pts=[(cx+r*math.cos(a),cy+r*.82*math.sin(a),.647-.01*math.sin(r/rad*math.pi)) for r in [rad*.22,rad*.5,rad*.9]]
        tube('Radial mushroom gill',pts,.003,gill,5)
    for sign in [-1,1]:
        pts=[]
        for j in range(13):
            x=(j/12-.5)*rad*1.35
            y=x*sign*.65
            z=.70+.096*math.sqrt(max(.1,1-(x/rad)**2-(y/(rad*.83))**2))
            pts.append((cx+x,cy+y,z))
        tube('Shiitake scored flesh',pts,.009,gill,6)

# Wilted greens with curved blades, ruffled edges and fine pale veins.
for leaf_index,(cx,cy,angle) in enumerate([(-.18,.57,-.4),(-.06,.69,.1),(-.36,.57,-.8)]):
    ca,sa=math.cos(angle),math.sin(angle)
    def leafpoint(x,y,z):
        return (cx+x*ca-y*sa,cy+x*sa+y*ca,z)
    v,f=[],[]
    for k in range(21):
        t=k/20
        w=.105*math.sin(math.pi*t)**.65
        for j in range(9):
            s=j/4-1
            x=s*w*(1+.1*math.sin(t*37))
            y=(t-.5)*.42
            z=.66+.072*math.sin(math.pi*t)+.017*abs(s)*math.sin(t*32)+.022*s*s
            v.append(leafpoint(x,y,z))
            if k and j:
                b=k*9+j; f.append((b-1,b,b-9,b-10))
    leaf=mesh('Wilted greens',v,f,green)
    solid=leaf.modifiers.new('Thin edible leaf','SOLIDIFY'); solid.thickness=.002
    bpy.context.view_layer.objects.active=leaf
    bpy.ops.object.modifier_apply(modifier=solid.name)
    tube('Leaf central rib',[leafpoint(0,(t-.5)*.42,.664+.072*math.sin(math.pi*t)) for t in [i/20 for i in range(21)]],.004,lightgreen,5)
    for k in range(1,7):
        t=k/8
        for sign in [-1,1]:
            tube('Leaf vein',[leafpoint(sign*s*.085*math.sin(math.pi*t),(t-.5)*.42+s*.025,.665+.072*math.sin(math.pi*t)+.015*s*s) for s in [0,.4,.8]],.0018,lightgreen,4)

# Fine sliced scallions have thin walls, pale interiors and irregular oval cuts.
for i in range(39):
    a=random.uniform(0,math.tau)
    r=random.uniform(.04,.24)
    cx=.28+r*math.cos(a); cy=-.30+r*math.sin(a)
    if i>28:
        cx=random.uniform(-.65,.65); cy=random.uniform(-.5,.55)
    size=random.uniform(.022,.041)
    bpy.ops.mesh.primitive_torus_add(major_radius=size,minor_radius=.007,major_segments=14,minor_segments=5,location=(cx,cy,.662+random.uniform(0,.024)))
    obj=finish(bpy.context.object,'Scallion ring',green if i%4 else lightgreen)
    obj.scale=(1,random.uniform(.65,1.15),random.uniform(.8,1.8))
    obj.rotation_euler=(random.uniform(-.45,.45),random.uniform(-.4,.4),a)

# Chili fragments, sesame seeds, and translucent-looking warm oil lenses.
for i in range(66):
    a=random.uniform(0,math.tau); r=random.uniform(.1,.94)
    x,y=r*math.cos(a),r*math.sin(a)
    if x<-.15 and abs(y)<.52: continue
    if i<32:
        ellipsoid('Roasted chili flake',(x,y,.637),(.010,.018,.005),chili,(0,.2,a),8,5)
    else:
        ellipsoid('Toasted sesame seed',(x,y,.649),(.006,.014,.004),sesame,(.1,.2,a),8,5)
for i in range(45):
    a=random.uniform(0,math.tau); r=random.uniform(.65,.95)
    rad=random.uniform(.006,.025)
    ellipsoid('Chili oil lens',(r*math.cos(a),r*math.sin(a),.630),(rad,rad*.83,.0018),chili,seg=12,rings=6)
# Pinpoint broth bubbles along the meniscus catch the softbox reflection.
for i in range(28):
    a=random.uniform(0,math.tau); r=random.uniform(.89,.975)
    size=random.uniform(.003,.010)
    ellipsoid('Broth bubble',(r*math.cos(a),r*math.sin(a),.633),(size,size,size*.45),broth,seg=10,rings=6)

# Join by material to keep the floating field to twelve draw calls per instance.
for mat in list(bpy.data.materials):
    objects=[o for o in model.objects if o.type=='MESH' and o.data.materials[0]==mat]
    if not objects: continue
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects: obj.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.object.join()
    obj=bpy.context.object
    obj.name=mat.name.split(' • ')[-1].replace(' ','_')
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    # Recalculate normals for arbitrary handmade mesh winding before export.
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')

# Bake nearby contact occlusion to a second UV set. This survives GLB export,
# grounding every ingredient even in the inexpensive instanced web scene.
scene.cycles.samples = 16
scene.render.bake.margin = 4
occlusion_group = bpy.data.node_groups.new('glTF Material Output', 'ShaderNodeTree')
occlusion_group.interface.new_socket(name='Occlusion', in_out='INPUT', socket_type='NodeSocketFloat')
for obj in model.objects:
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    obj.data.uv_layers.new(name='OcclusionUV')
    obj.data.uv_layers.active_index = 1
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=.015)
    bpy.ops.object.mode_set(mode='OBJECT')
    mat = obj.data.materials[0]
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    original_uv = nodes.new('ShaderNodeUVMap'); original_uv.uv_map = 'UVMap'
    for node in list(nodes):
        if node.type == 'TEX_IMAGE':
            links.new(original_uv.outputs['UV'], node.inputs['Vector'])
    ao_image = bpy.data.images.new(obj.name+' • baked contact occlusion', width=1024, height=1024, alpha=False)
    ao_image.colorspace_settings.name = 'Non-Color'
    tex = nodes.new('ShaderNodeTexImage'); tex.image = ao_image
    nodes.active = tex
    ao = nodes.new('ShaderNodeAmbientOcclusion'); ao.inputs['Distance'].default_value = .22
    ao.samples = 16
    emission = nodes.new('ShaderNodeEmission')
    links.new(ao.outputs['Color'], emission.inputs['Color'])
    output = nodes.get('Material Output'); bsdf = nodes.get('Principled BSDF')
    links.new(emission.outputs[0], output.inputs['Surface'])
    bpy.ops.object.bake(type='EMIT', uv_layer='OcclusionUV')
    links.new(bsdf.outputs[0], output.inputs['Surface'])
    nodes.remove(emission); nodes.remove(ao)
    ao_image.pack()
    ao_uv = nodes.new('ShaderNodeUVMap'); ao_uv.uv_map = 'OcclusionUV'
    links.new(ao_uv.outputs['UV'], tex.inputs['Vector'])
    settings = nodes.new('ShaderNodeGroup'); settings.node_tree = occlusion_group
    links.new(tex.outputs['Color'], settings.inputs['Occlusion'])
    obj.data.uv_layers.active_index = 0
    obj.data.uv_layers[0].active_render = True
scene.cycles.samples = 48

bpy.ops.object.select_all(action='DESELECT')
for obj in model.objects: obj.select_set(True)
(ROOT/'public/models').mkdir(parents=True,exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/models/realistic-soup.glb'),export_format='GLB',use_selection=True,export_image_format='JPEG',export_jpeg_quality=88,export_texcoords=True,export_normals=True,export_tangents=True,export_materials='EXPORT',export_yup=True,export_extras=True)

# A separate, non-exported studio is retained in the editable .blend file.
def aim(obj,at): obj.rotation_euler=(Vector(at)-obj.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power,size in [('Key',(-3,-4,6),550,4),('Rim',(2,3,4),420,3),('Fill',(4,-1,3),180,2.5)]:
    bpy.ops.object.light_add(type='AREA',location=loc)
    light=bpy.context.object; light.name=name
    light.data.energy=power; light.data.shape='DISK'; light.data.size=size
    aim(light,(0,0,.35))
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.008))
plane=bpy.context.object; plane.name='Studio floor (not exported)'
mat=bpy.data.materials.new('Studio warm parchment'); mat.diffuse_color=(.23,.17,.10,1)
plane.data.materials.append(mat)
bpy.ops.object.camera_add(location=(2.45,-3.6,3.25))
camera=bpy.context.object; aim(camera,(0,0,.42)); camera.data.type='ORTHO'; camera.data.ortho_scale=3.35
scene.camera=camera
scene.render.resolution_x=1200; scene.render.resolution_y=1100; scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets/blender/realistic-soup.blend'),compress=True)
if os.environ.get('SOUP_RENDER'):
    scene.render.filepath=os.environ['SOUP_RENDER']
    bpy.ops.render.render(write_still=True)
print('SOUP_EXPORT_COMPLETE',len(model.objects),'meshes',sum(len(o.data.polygons) for o in model.objects),'faces')
