"""Fusion script: writes the part's faces as meshes, which is the model every check here reads.

Run it with the part's document active, through Scripts and Add-Ins or the Fusion MCP (readOnly works,
since it changes nothing in the document). Set BODY_NAME and OUTPUT_PATH first. Pasted code has no
__file__, so the path has to be written out. Face numbers in the checks are this file's `index`.
"""
import json

import adsk.core
import adsk.fusion

BODY_NAME = "Knight"
OUTPUT_PATH = "/Users/don.payne/src/cnc/haas_knight/knight_faces.json"
MM_PER_CM = 10


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeDocument.products.itemByProductType("DesignProductType"))
    body = next(body for body in design.rootComponent.bRepBodies if body.name == BODY_NAME)
    faces = []
    for index, face in enumerate(body.faces):
        calculator = face.meshManager.createMeshCalculator()
        calculator.setQuality(adsk.fusion.TriangleMeshQualityOptions.HighQualityTriangleMesh)
        mesh = calculator.calculate()
        faces.append(
            {
                "index": index,
                "area_mm2": face.area * MM_PER_CM ** 2,
                "nodes_mm": [coordinate * MM_PER_CM for coordinate in mesh.nodeCoordinatesAsDouble],
                "tris": list(mesh.nodeIndices),
            }
        )
    with open(OUTPUT_PATH, "w") as output:
        json.dump(faces, output)
    print("faces exported", len(faces), "triangles", sum(len(face["tris"]) // 3 for face in faces))
