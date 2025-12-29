import math
from array import array

import glm
import moderngl

from ..mat3d import flatten, prep_mat
from ..elements import Element

# ---------------------------------------------------------------------------------
#  Tetrahedron Definition
# ---------------------------------------------------------------------------------
#  Basic geometry for lightweight procedural rendering.
#  Used for sparks, tracers, particles, and effects.

# Define the vertex coordinates for a tetrahedron (4 points in 3D space)
TETRAHEDRON_VERTICES = [
    (math.cos(0.0) * 0.7, math.sin(0.0) * 0.7, 0.0),
    (math.cos(math.pi * 2 / 3) * 0.7, math.sin(math.pi * 2 / 3) * 0.7, 0.5),
    (math.cos(math.pi * 4 / 3) * 0.7, math.sin(math.pi * 4 / 3) * 0.7, 0.5),
    (0.0, 0.0, -0.5),
]

# Flattened list of triangles composing the tetrahedron
TETRAHEDRON = [
    # Face 1
    TETRAHEDRON_VERTICES[0],
    TETRAHEDRON_VERTICES[1],
    TETRAHEDRON_VERTICES[2],

    # Face 2
    TETRAHEDRON_VERTICES[0],
    TETRAHEDRON_VERTICES[2],
    TETRAHEDRON_VERTICES[3],

    # Face 3
    TETRAHEDRON_VERTICES[1],
    TETRAHEDRON_VERTICES[0],
    TETRAHEDRON_VERTICES[3],

    # Face 4
    TETRAHEDRON_VERTICES[2],
    TETRAHEDRON_VERTICES[1],
    TETRAHEDRON_VERTICES[3],
]


# ---------------------------------------------------------------------------------
#  Polygon Class
# ---------------------------------------------------------------------------------
#  Represents a generic 3D shape defined by a set of vertex positions.
#  Builds GPU buffers and VAO for rendering, and manages shader uniform updates.

class Polygon(Element):
    def __init__(self, points, program):
        """
        :param points: List of (x, y, z) vertex tuples defining the polygon
        :param program: ModernGL shader program used to render this polygon
        """
        super().__init__()

        # Get ModernGL context from engine singleton
        ctx = self.e['MGL'].ctx

        self.program = program

        # Upload vertex data (flattened) to GPU buffer as float32 array
        self.buffer = ctx.buffer(data=array('f', flatten(points)))

        # Create a VAO binding vertex buffer to the 'vert' attribute in the shader
        # The format '3f' means 3 floats per vertex position
        self.vao = ctx.vertex_array(program, [(self.buffer, '3f', 'vert')])

    def update_uniforms(self, uniforms={}):
        """
        Update all uniforms in the shader before rendering.
        Handles both regular values and ModernGL Texture objects.
        """
        tex_id = 0
        # Get all uniform names available in the shader program
        uniform_list = list(self.program)

        # Apply uniforms one by one
        for uniform in uniforms:
            if uniform in uniform_list:
                value = uniforms[uniform]

                # If this uniform is a texture, bind and assign texture ID
                if isinstance(value, moderngl.Texture):
                    value.use(tex_id)
                    self.program[uniform].value = tex_id
                    tex_id += 1
                else:
                    # Assign numeric/vector/matrix value directly
                    self.program[uniform].value = value


# ---------------------------------------------------------------------------------
#  PolygonOBJ Class
# ---------------------------------------------------------------------------------
#  Represents a positioned and transformable instance of a Polygon.
#  Handles transformation matrices and rendering integration with a camera.

class PolygonOBJ(Element):
    def __init__(self, shape, pos=None, rotation=None):
        """
        :param shape: Polygon object (contains GPU VAO and shader)
        :param pos: 3D position (glm.vec3 or tuple)
        :param rotation: Quaternion rotation (glm.quat or tuple)
        """
        super().__init__()

        self.polygon = shape  # Reference to Polygon geometry

        # Default transform components
        self.scale = glm.vec3(1.0, 1.0, 1.0)
        self.pos = glm.vec3(pos) if pos else glm.vec3(0.0, 0.0, 0.0)
        self.rotation = glm.quat(rotation) if rotation else glm.quat()

        # Compute initial transform matrix
        self.calculate_transform()

    def calculate_transform(self):
        """
        Compute the model transformation matrix combining:
        translation, rotation, and scaling.
        """
        scale_mat = glm.scale(self.scale)
        self.transform = glm.translate(self.pos) * glm.mat4(self.rotation) * scale_mat

    def update(self):
        """
        Update per-frame transformations if necessary.
        (Currently just recomputes matrix; could be extended for animation.)
        """
        self.calculate_transform()

    def render(self, camera, uniforms={}):
        """
        Render this polygon instance using the given camera.
        :param camera: Active camera providing projection/view matrix
        :param uniforms: Extra shader uniforms to apply
        """
        # Set standard transform uniforms expected by shaders
        uniforms['world_transform'] = prep_mat(self.transform)
        uniforms['view_projection'] = camera.prepped_matrix

        # Send all uniforms to shader
        self.polygon.update_uniforms(uniforms=uniforms)

        # Render the polygon’s VAO as filled triangles
        self.polygon.vao.render(mode=moderngl.TRIANGLES)
