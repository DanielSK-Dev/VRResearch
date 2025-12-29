import os

import pywavefront
import moderngl

from .geometry import Geometry
from .vao import TexturedVAOs, TEXTURE_CATEGORIES
from .entity3d import Entity3D
from ..elements import Element

# Maps short identifiers used by pywavefront format strings to internal attribute names
FORMAT_NAMES = {
    'T': 'uv',  # Texture coordinates
    'N': 'normal',  # Normal vector
    'V': 'vert',  # Vertex position
}


class VertexFormat:
    """
    Parses the vertex format string provided by pywavefront (e.g., 'V3_N3_T2')
    into a structured mapping of attributes and their float offsets.
    This determines how many floats are in each vertex and what they represent.
    """

    def __init__(self, string):
        # Stores attribute names with index ranges inside the flat vertex array
        self.group_map = []
        # Maps attribute names to ModernGL-compatible data type strings (e.g., '3f', '2f')
        self.datatypes = {}

        offset = 0
        for part in string.split('_'):
            part_id = 'unknown'
            # Each part ends with two characters that define size (e.g. '3f')
            # and may start with a letter that identifies the attribute
            if part[:-2] in FORMAT_NAMES:
                part_id = FORMAT_NAMES[part[:-2]]
            size = int(part[-2])  # e.g., 3 in '3f'
            # Add this attribute with its offset range in the vertex data
            self.group_map.append((part_id, offset, offset + size))
            # Map the attribute name to the ModernGL-friendly string (like '3f', '2f')
            self.datatypes[part_id] = part[-2:].lower()
            offset += size

        # Total number of floats per vertex
        self.length = offset


class OBJ(Element):
    """
    Loads a Wavefront OBJ file using pywavefront, converts it to engine Geometry,
    uploads it to GPU as ModernGL VAOs, and links textures automatically.

    Parameters:
        path (str): Path to .obj file
        program: ModernGL shader program
        centered (bool): Whether to recenter and rescale geometry to [-1,1]
        pixelated (bool): Use NEAREST filtering for pixel-art style textures
        simple (bool): Simplified rendering path (for faster shaders)
        save_geometry (bool): Keep CPU-side geometry (for re-use/debug)
        no_build (bool): Load model but skip GPU upload
    """

    def __init__(self, path, program, centered=True, pixelated=True, simple=False, save_geometry=False, no_build=False):
        super().__init__()

        self.vao = None  # ModernGL vertex array object(s)
        self.bounds = None  # Axis-aligned bounding box of model
        self.save_geometry = save_geometry
        self.geometry = None  # Stored Geometry object (optional)

        self.simple = simple
        self.pixelated = pixelated
        self.no_build = no_build

        # Extract model name (without path/extension)
        self.name = path.split('/')[-1].split('.')[0]

        # Begin loading and building the OBJ model
        self.load(path, program, centered=centered)

    def parse_format(self, fmt):
        """
        Legacy helper to parse format strings manually (unused but kept for reference).
        Converts format strings (like 'V3_N3_T2') to attribute labels per float component.
        """
        parsed_format = []
        for part in fmt.split('_'):
            part_id = 'unknown'
            if part[:-2] in FORMAT_NAMES:
                part_id = FORMAT_NAMES[part[:-2]]
            # Append each float component’s semantic label (e.g. 'vert', 'normal', etc.)
            for i in range(int(part[-2])):
                parsed_format.append(part_id)

    def load(self, path, program, centered=True):
        """
        Core method to load and process an OBJ file.
        Steps:
          1. Load OBJ file using pywavefront
          2. Convert materials to Geometry (per-material vertex lists)
          3. Build GPU VAOs
          4. Auto-detect and bind textures in the same directory
        """
        # Step 1: Load Wavefront OBJ scene data
        scene = pywavefront.Wavefront(path)

        # Material → list of vertex attribute dictionaries
        matwise_verts = {}

        fmt = None
        # Step 2: Iterate through materials in the OBJ scene
        for name, material in scene.materials.items():
            points = []

            # Some materials might not have vertex data (skip them)
            if not len(material.vertex_format):
                continue

            # Parse pywavefront’s vertex format string (e.g. 'V3_N3_T2')
            fmt = VertexFormat(material.vertex_format)

            # Convert flat vertex list into structured dictionaries for each vertex
            for i in range(len(material.vertices) // fmt.length):
                # Build a dictionary like {'vert': (x,y,z), 'normal': (nx,ny,nz), 'uv': (u,v)}
                points.append({
                    group[0]: tuple(material.vertices[i * fmt.length + group[1]: i * fmt.length + group[2]])
                    for group in fmt.group_map
                })

            # Store per-material vertex data
            matwise_verts[name] = points

        # Step 3: Create a Geometry object from parsed materials
        geometry = Geometry(matwise_verts)

        # Optionally recenter and normalize the geometry scale
        if centered:
            geometry.center(rescale=True)
        else:
            geometry.get_bounds()

        # Step 4: Upload to GPU (unless no_build is set)
        if fmt:
            if self.no_build:
                # Create an empty placeholder VAO (no GPU upload)
                self.vao = TexturedVAOs(program, [], simple=self.simple)
            else:
                # Build GPU buffers and VAOs
                self.vao = TexturedVAOs(
                    program,
                    geometry.build(self.e['MGL'].ctx, program, fmt),
                    simple=self.simple
                )

            # Step 5: Locate textures in the model folder
            base_path = '/'.join(path.split('/')[:-1])
            folder_contents = os.listdir(base_path)

            for file in folder_contents:
                # Only consider PNG textures
                if file.split('.')[-1] == 'png':
                    file_suffix = file.split('_')[-1].split('.')[0]

                    # Match texture category (e.g. _normal, _roughness)
                    if file_suffix in TEXTURE_CATEGORIES:
                        tex = self.e['MGL'].load_texture(base_path + '/' + file)
                        if self.pixelated:
                            tex.filter = moderngl.NEAREST, moderngl.NEAREST
                        self.vao.bind_texture(tex, file_suffix)

                    # Base texture (same name as the OBJ)
                    if file.split('.')[0] == path.split('/')[-1].split('.')[0]:
                        tex = self.e['MGL'].load_texture(base_path + '/' + file)
                        if self.pixelated:
                            tex.filter = moderngl.NEAREST, moderngl.NEAREST
                        self.vao.bind_texture(tex, 'texture')

        # Store bounding box and optionally keep CPU geometry
        self.bounds = geometry.bounds
        if self.save_geometry:
            self.geometry = geometry

    def new_entity(self):
        """
        Create a new 3D entity instance that uses this model's VAO.
        This allows one loaded model to be reused for multiple world entities.
        """
        return Entity3D(self.vao)
