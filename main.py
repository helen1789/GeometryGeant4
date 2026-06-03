import xml.etree.ElementTree as ET
import json, math

def parse_gdml(path):
    tree = ET.parse(path) if isinstance(path, str) else ET.ElementTree(ET.fromstring(path.read()))
    root = tree.getroot()

    # pega os sólidos definidos
    solids = {}
    for solid in root.find("solids"):
        solids[solid.get("name")] = solid

    # pega posições definidas
    positions = {}
    defines = root.find("define")
    if defines:
        for pos in defines.findall("position"):
            positions[pos.get("name")] = (
                float(pos.get("x", 0)),
                float(pos.get("y", 0)),
                float(pos.get("z", 0))
            )

    volumes = []
    for vol in root.find("structure").findall("volume"):
        solid_ref = vol.find("solidref").get("ref")
        solid = solids.get(solid_ref)
        if solid is None:
            continue

        mesh = tessellate(solid)
        if mesh is None:
            continue

        for pv in vol.findall("physvol"):
            pos_ref = pv.find("position")
            pos = (0, 0, 0)
            if pos_ref is not None:
                name = pos_ref.get("ref", "")
                pos = positions.get(name, (
                    float(pos_ref.get("x", 0)),
                    float(pos_ref.get("y", 0)),
                    float(pos_ref.get("z", 0))
                ))
            volumes.append({
                "name": solid_ref,
                "vertices": mesh["vertices"],
                "indices": mesh["indices"],
                "position": list(pos)
            })

    return {"volumes": volumes}


def tessellate(solid):
    tag = solid.tag
    if tag == "box":
        return tessellate_box(solid)
    elif tag == "tube":
        return tessellate_tube(solid)
    elif tag == "sphere":
        return tessellate_sphere(solid)
    return None  # sólido não suportado ainda


def tessellate_box(solid):
    dx = float(solid.get("x", 100)) / 2
    dy = float(solid.get("y", 100)) / 2
    dz = float(solid.get("z", 100)) / 2

    v = [
        [-dx,-dy,-dz], [ dx,-dy,-dz], [ dx, dy,-dz], [-dx, dy,-dz],
        [-dx,-dy, dz], [ dx,-dy, dz], [ dx, dy, dz], [-dx, dy, dz],
    ]
    faces = [
        [0,1,2,3], [4,7,6,5],
        [0,4,5,1], [2,6,7,3],
        [0,3,7,4], [1,5,6,2]
    ]
    verts, idxs = [], []
    for face in faces:
        base = len(verts) // 3
        for i in face:
            verts += v[i]
        idxs += [base, base+1, base+2, base, base+2, base+3]
    return {"vertices": verts, "indices": idxs}


def tessellate_tube(solid):
    rmax = float(solid.get("rmax", 50))
    rmin = float(solid.get("rmin", 0))
    hz   = float(solid.get("z", 100)) / 2
    segs = 64

    verts, idxs = [], []

    for s in range(segs):
        a0 = 2 * math.pi * s / segs
        a1 = 2 * math.pi * (s + 1) / segs
        # face lateral externa
        base = len(verts) // 3
        verts += [
            math.cos(a0)*rmax, math.sin(a0)*rmax, -hz,
            math.cos(a1)*rmax, math.sin(a1)*rmax, -hz,
            math.cos(a1)*rmax, math.sin(a1)*rmax,  hz,
            math.cos(a0)*rmax, math.sin(a0)*rmax,  hz,
        ]
        idxs += [base, base+1, base+2, base, base+2, base+3]

        if rmin > 0:
            # face lateral interna
            base = len(verts) // 3
            verts += [
                math.cos(a0)*rmin, math.sin(a0)*rmin, -hz,
                math.cos(a1)*rmin, math.sin(a1)*rmin, -hz,
                math.cos(a1)*rmin, math.sin(a1)*rmin,  hz,
                math.cos(a0)*rmin, math.sin(a0)*rmin,  hz,
            ]
            idxs += [base, base+2, base+1, base, base+3, base+2]

        # tampas (top e bottom)
        for z, sign in [(-hz, -1), (hz, 1)]:
            base = len(verts) // 3
            verts += [
                math.cos(a0)*rmin, math.sin(a0)*rmin, z,
                math.cos(a0)*rmax, math.sin(a0)*rmax, z,
                math.cos(a1)*rmax, math.sin(a1)*rmax, z,
                math.cos(a1)*rmin, math.sin(a1)*rmin, z,
            ]
            if sign > 0:
                idxs += [base, base+1, base+2, base, base+2, base+3]
            else:
                idxs += [base, base+2, base+1, base, base+3, base+2]

    return {"vertices": verts, "indices": idxs}


def tessellate_sphere(solid):
    rmax  = float(solid.get("rmax", 50))
    segs  = 32
    rings = 16

    verts, idxs = [], []
    for i in range(rings + 1):
        phi = math.pi * i / rings
        for j in range(segs + 1):
            theta = 2 * math.pi * j / segs
            verts += [
                rmax * math.sin(phi) * math.cos(theta),
                rmax * math.cos(phi),
                rmax * math.sin(phi) * math.sin(theta),
            ]

    for i in range(rings):
        for j in range(segs):
            a = i * (segs + 1) + j
            b = a + segs + 1
            idxs += [a, b, a+1, b, b+1, a+1]

    return {"vertices": verts, "indices": idxs}

if __name__ == "__main__":
    import io
    gdml_content = """<?xml version="1.0"?>
<!DOCTYPE gdml>
<gdml>
  <define/>
  <materials>
    <material name="G4_AIR" Z="7">
      <D value="0.00120479"/>
      <atom value="14.01"/>
    </material>
  </materials>
  <solids>
    <box name="WorldBox" x="1000" y="1000" z="1000" lunit="mm"/>
    <tube name="Det" rmin="0" rmax="100" z="200"
          startphi="0" deltaphi="360" lunit="mm" aunit="deg"/>
  </solids>
  <structure>
    <volume name="DetLV">
      <materialref ref="G4_AIR"/>
      <solidref ref="Det"/>
    </volume>
    <volume name="WorldLV">
      <materialref ref="G4_AIR"/>
      <solidref ref="WorldBox"/>
      <physvol>
        <volumeref ref="DetLV"/>
        <position name="p1" x="0" y="0" z="0"/>
      </physvol>
    </volume>
  </structure>
  <setup name="Default" version="1.0">
    <world ref="WorldLV"/>
  </setup>
</gdml>"""
    root = ET.fromstring(gdml_content)
    solids = {}
    for solid in root.find("solids"):
        solids[solid.get("name")] = solid
    positions = {}
    defines = root.find("define")
    if defines:
        for pos in defines.findall("position"):
            positions[pos.get("name")] = (
                float(pos.get("x", 0)),
                float(pos.get("y", 0)),
                float(pos.get("z", 0))
            )
    volumes = []
    for vol in root.find("structure").findall("volume"):
        solid_ref = vol.find("solidref").get("ref")
        solid = solids.get(solid_ref)
        if solid is None:
            continue
        mesh = tessellate(solid)
        if mesh is None:
            continue
        for pv in vol.findall("physvol"):
            pos_ref = pv.find("position")
            pos = (0, 0, 0)
            if pos_ref is not None:
                name = pos_ref.get("ref", "")
                pos = positions.get(name, (
                    float(pos_ref.get("x", 0)),
                    float(pos_ref.get("y", 0)),
                    float(pos_ref.get("z", 0))
                ))
            volumes.append({
                "name": solid_ref,
                "vertices": mesh["vertices"],
                "indices": mesh["indices"],
                "position": list(pos)
            })
    data = {"volumes": volumes}
    with open("geometry.json", "w") as f:
        json.dump(data, f)
    print(f"Exportado {len(data['volumes'])} volumes")
    print(json.dumps(data, indent=2)[:500])
                
