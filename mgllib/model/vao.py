import moderngl

# -------------------------------------------------------------------------------
# Texture categories recognized by the engine.
# Each corresponds to a different texture input a shader might expect.
# Example: diffuse color map, normal map, or metallic map.
# -------------------------------------------------------------------------------
TEXTURE_CATEGORIES = ['texture', 'normal', 'metallic']


# -------------------------------------------------------------------------------
# VAOs Class
# -------------------------------------------------------------------------------
# A lightweight container for one or more ModernGL Vertex Array Objects (VAOs).
# Responsible for updating shader uniforms and rendering associated geometry.
# -------------------------------------------------------------------------------
class VAOs:
    def __init__(self, program, vaos):
        """
        :param program: ModernGL shader program used for rendering
        :param vaos: list of ModernGL VertexArray objects to be drawn
        """
        self.program = program
        self.vaos = vaos

    def update(self, uniforms={}):
        """
        Updates the shader's uniform variables before rendering.
        Handles both normal uniforms (floats, vectors, matrices)
        and ModernGL textures (which must be bound to texture units).
        """
        tex_id = 0  # Current texture unit index
        uniform_list = list(self.program)  # All available uniform names in shader

        for uniform in uniforms:
            if uniform in uniform_list:
                value = uniforms[uniform]

                # If the uniform is a texture, bind it to the next available slot
                if isinstance(value, moderngl.Texture):
                    value.use(tex_id)  # Bind to texture unit tex_id
                    self.program[uniform].value = tex_id  # Pass texture ID to shader
                    tex_id += 1
                else:
                    # Assign numeric, vector, or matrix uniform value directly
                    self.program[uniform].value = value

    def render(self, uniforms={}, mode=moderngl.TRIANGLES):
        """
        Renders all VAOs stored in this object using the specified draw mode.
        Before rendering, updates uniforms so the shader has current data.
        """
        # Update uniforms and bind textures as needed
        self.update(uniforms=uniforms)

        # Draw each VAO (geometry) using the selected render mode
        for vao in self.vaos:
            vao.render(mode=mode)


# -------------------------------------------------------------------------------
# TexturedVAOs Class
# -------------------------------------------------------------------------------
# Extends VAOs to support automatic texture binding for multi-texture materials.
# Manages texture flags (bitmask) to tell shaders which textures are active.
# -------------------------------------------------------------------------------
class TexturedVAOs(VAOs):
    def __init__(self, program, vaos, simple=False):
        """
        :param program: ModernGL shader program
        :param vaos: list of ModernGL VAOs for this model/material
        :param simple: if True, disables texture_flags (used for simpler shaders)
        """
        super().__init__(program, vaos)

        self.simple = simple

        # Holds all bound textures by category (e.g., {'texture': tex1, 'normal': tex2})
        self.textures = {}

        # Bitmask for active textures; starts at 1 so 0 means "no texture"
        self.texture_flags = 1

    def bind_texture(self, texture, category):
        """
        Bind a texture to a given material category (e.g. 'normal', 'metallic').
        Sets a bit flag for that category so shaders can test which maps exist.
        """
        if category in TEXTURE_CATEGORIES:
            # Use bit position to mark active texture types
            # e.g., texture_flags |= 2^index
            self.texture_flags |= (2 ** TEXTURE_CATEGORIES.index(category))

            # Store the texture reference
            self.textures[category] = texture

    def render(self, uniforms={}, mode=moderngl.TRIANGLES):
        """
        Prepares all textures as uniforms, then calls parent render method.
        Automatically adds entries to the uniforms dict for each texture.
        """
        # Add texture objects to uniform dictionary
        for category in self.textures:
            tex = self.textures[category]

            # Match shader variable naming convention:
            # 'texture' → 'tex', 'normal' → 'normal_tex', etc.
            if category == 'texture':
                uniform_name = 'tex'
            else:
                uniform_name = category + '_tex'

            # Add texture to uniforms dictionary under correct shader name
            uniforms[uniform_name] = tex

        # If not in simple mode, send texture bitmask to shader
        if not self.simple:
            uniforms['texture_flags'] = self.texture_flags

        # Call base VAO renderer to actually draw geometry
        super().render(uniforms=uniforms, mode=mode)
