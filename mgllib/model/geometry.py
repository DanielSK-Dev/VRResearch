from array import array


class VertexBuffer:
    """
    Represents a single vertex buffer stored on the GPU.
    Holds vertex data and format info for linking to shaders.
    """

    def __init__(self, ctx, data, fmt):
        # ctx: ModernGL context
        # data: list of float vertex values (flattened)
        # fmt: list of attribute names for the shader (e.g. ['vert', 'norm', 'texcoord'])
        self.ctx = ctx

        # Upload vertex data to GPU as a ModernGL buffer
        # array('f', data) ensures float32 format
        self.buffer = ctx.buffer(data=array('f', data))

        # Store the data layout format for later use
        self.fmt = fmt


class FrozenGeometry:
    """
    Represents finalized, GPU-ready geometry.
    Holds vertex buffers and bounding information.
    Once frozen, geometry data should not be modified on CPU.
    """

    def __init__(self, src, buffers):
        # src: Geometry source that this frozen geometry is built from
        # buffers: dict mapping material names -> VertexBuffer objects
        self.bounds = src.bounds
        self.buffers = buffers

    def generate_vaos(self, program, fmt):
        """
        Creates a list of Vertex Array Objects (VAOs) using the shader program and buffer format.
        This links each buffer's vertex attributes to the GPU shader pipeline.
        """
        ctx = None
        vaos = []

        # Iterate through all buffers (per material, typically)
        for buffer in self.buffers:
            # Access ModernGL context from each buffer
            ctx = self.buffers[buffer].ctx

            # Build the datatype string used by ModernGL (e.g. '3f 3f 2f' for vert/norm/uv)
            datatypes = ' '.join([fmt.datatypes[group] for group in self.buffers[buffer].fmt])

            # Combine buffer object and attribute info for vertex_array creation
            # ModernGL expects (buffer, datatypes, *attribute_names)
            params = [(self.buffers[buffer].buffer, datatypes, *self.buffers[buffer].fmt)]

            # Create a VAO that binds this buffer to the given shader program
            vaos.append(ctx.vertex_array(program, params))

        # Return the full list of VAOs built for all materials/buffers
        return vaos


class Geometry:
    """
    Represents CPU-side vertex data for one or more materials.
    Can calculate bounds, recenter geometry, and build GPU buffers.
    """

    def __init__(self, materials):
        # materials: dict of { material_name: [ {attr_name: tuple}, {...}, ... ] }
        super().__init__()
        self.materials = materials

    def get_bounds(self):
        """
        Calculates the axis-aligned bounding box (AABB) of the geometry.
        Sets self.bounds to a list of (min, max) tuples for each dimension.
        """
        self.bounds = None
        if len(self.materials):
            # Grab first material for dimension reference
            first_material = self.materials[list(self.materials)[0]]
            if len(first_material):
                dimensions = len(first_material[0]['vert'])

                # Initialize extreme bounds for each axis
                bounds = [(9999999, -9999999)] * dimensions

                # Traverse every vertex in every material
                for vertices in self.materials.values():
                    for vert in vertices:
                        for i in range(dimensions):
                            # Update min and max per coordinate
                            bounds[i] = (
                                min(bounds[i][0], vert['vert'][i]),
                                max(bounds[i][1], vert['vert'][i])
                            )

                self.bounds = bounds

    def get_center(self):
        """
        Returns the geometric center of the geometry (average of bounds).
        """
        self.get_bounds()
        if self.bounds:
            # Compute midpoint between min and max for each axis
            center = tuple((dim[1] - dim[0]) * 0.5 + dim[0] for dim in self.bounds)
            return center

    def center(self, rescale=False):
        """
        Moves geometry so its center is at the origin.
        Optionally rescales geometry so its largest dimension spans roughly [-1, 1].
        """
        old_center = self.get_center()
        if old_center:
            # Find the longest axis (used if rescaling)
            largest_span = max(dim[1] - dim[0] for dim in self.bounds)

            # Shift (and possibly scale) each vertex
            for vertices in self.materials.values():
                for i in range(len(vertices)):
                    if rescale:
                        # Shift to center and normalize by largest span
                        vertices[i]['vert'] = tuple(
                            (vertices[i]['vert'][j] - old_center[j]) / largest_span * 2
                            for j in range(len(old_center))
                        )
                    else:
                        # Just shift to center without scaling
                        vertices[i]['vert'] = tuple(
                            vertices[i]['vert'][j] - old_center[j]
                            for j in range(len(old_center))
                        )

            # Update bounds to reflect new vertex positions
            self.get_bounds()

    def build(self, ctx, program, fmt):
        """
        Converts CPU-side vertex data into GPU-side buffers.
        Builds a FrozenGeometry object and generates VAOs.
        """
        buffers = {}

        # Iterate through each material and build vertex buffer
        for material in self.materials:
            if len(self.materials[material]):
                # Get the format from the first vertex (keys like 'vert', 'norm', etc.)
                material_fmt = list(self.materials[material][0])
                material_data = []

                # Flatten vertex data: [x,y,z,nx,ny,nz,u,v, ...]
                for vertex in self.materials[material]:
                    for group in material_fmt:
                        for v in vertex[group]:
                            material_data.append(v)

                # Create GPU buffer for this material
                buffers[material] = VertexBuffer(ctx, material_data, material_fmt)

        # Build VAOs and return list of them
        return FrozenGeometry(self, buffers).generate_vaos(program, fmt)
