from .mat3d import prep_mat, perspective_matrix, lookat_matrix


# -------------------------------------------------------------------------------
# Camera Class
# -------------------------------------------------------------------------------
# Provides a basic perspective camera for 3D rendering.
# Handles position, target (look direction), up vector, and matrix generation.
# -------------------------------------------------------------------------------

class Camera:
    def __init__(self, pos=[0, 0, 1], target=[0, 0, 0], up=[0, 1, 0]):
        """
        Initialize a new camera with position, target, and up direction.

        :param pos:    Starting position of the camera in world space.
        :param target: The point the camera is looking at.
        :param up:     The up vector defining the camera's orientation.
        """
        # Camera position and orientation vectors
        self.pos = list(pos)
        self.target = list(target)
        self.up = list(up)

        # Initialize camera matrices
        self.update_matrix()

        # Default global light position (used by shaders)
        self.light_pos = [0, 1, 0]

    def lookat(self, target):
        """
        Reorient the camera to look at a new target point.
        Automatically updates the internal view-projection matrix.
        """
        # Ensure we only use the first three coordinates of target
        self.target = list(target[:3])
        self.update_matrix()

    def move(self, movement):
        """
        Move the camera by a delta vector in world coordinates.
        Useful for simple free-fly or first-person movement.
        """
        for i in range(3):
            self.pos[i] += movement[i]
        self.update_matrix()

    def set_pos(self, pos):
        """
        Set the camera to a new absolute position in world space.
        """
        self.pos = list(pos)
        self.update_matrix()

    def update_matrix(self):
        """
        Recalculate the combined projection-view matrix based on
        the current position, target, and up vectors.

        This produces a matrix that can be passed directly to shaders
        for transforming world coordinates into clip space.
        """
        # Build a view matrix from position, target, and up direction
        view_matrix = lookat_matrix(self.pos, self.target, self.up)

        # Perspective projection (FOV 80°, aspect ratio 1.0, near/far clip planes)
        projection_matrix = perspective_matrix(80, 1.0, 0.001, 200)

        # Combine into one matrix: projection * view
        self.matrix = projection_matrix * view_matrix

        # Pre-flattened tuple form for sending as a shader uniform
        self.prepped_matrix = prep_mat(self.matrix)
