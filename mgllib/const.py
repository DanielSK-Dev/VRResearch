# ---------------------------------------------------------------------------------
# Engine Constants and Tuning Parameters
# ---------------------------------------------------------------------------------
# Centralized configuration file for runtime constants.
# Includes graphics, physics, audio, input thresholds, and gameplay tuning values.
# ---------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# Rendering and Color
# ------------------------------------------------------------------------------
# Some OpenXR runtimes can cause color mismatches when using RGB instead of sRGB.
# For reference: https://communityforums.atmeta.com/t5/OpenXR-Development/sRGB-RGB-giving-washed-out-bright-image/td-p/957475
# Setting FORCE_SRGB to True forces conversion and avoids overly bright or washed-out visuals.
FORCE_SRGB = True

# Cube map texture face ordering used when loading skyboxes.
# Order: east, west, up, down, north, south
SKYBOX_DIRECTIONS = ['e', 'w', 'u', 'd', 'n', 's']

# ------------------------------------------------------------------------------
# Input and Interaction
# ------------------------------------------------------------------------------
# Minimum trigger value to register as an "activated" input
TRIGGER_THRESHOLD = 0.5

# Time window (in seconds) used when calculating smoothed hand velocity
HAND_VELOCITY_TIMEFRAME = 0.1

# ------------------------------------------------------------------------------
# Physics and Precision
# ------------------------------------------------------------------------------
# Small epsilon value used to avoid division by zero or rounding instability
PHYSICS_EPSILON = 0.00001

# ------------------------------------------------------------------------------
# Audio System
# ------------------------------------------------------------------------------
# Scale factor for distance-based audio attenuation
# (larger values make sound falloff more gradual)
SOUND_DISTANCE_SCALE = 0.75

# ------------------------------------------------------------------------------
# User Interface and Feedback
# ------------------------------------------------------------------------------
# Cooldown time between hover interactions (prevents flicker/double-trigger)
HOVER_COOLDOWN = 0.25

# ------------------------------------------------------------------------------
# Weapon Recoil Patterns
# ------------------------------------------------------------------------------
# Defines directional recoil per shot, in degrees (x offset, y offset).
# The pattern alternates between a 'start' burst and looping recoil behavior.
RECOIL_PATTERNS = {
    'default': {
        'start': [
            (-1, 2),
            (-1, 1.5),
            (-0.2, 1.5),
            (0, 1.1),
            (2.5, 1.7),
            (-1.1, -0.2),
            (-2.1, 1.5),
            (-1, 0.7),
            (0.2, 2.1),
        ],
        'loop': [
            (0.9, 1.5),
            (2.2, 1.5),
            (2.2, 1.5),
            (0.9, 1.5),
            (0.2, 1.5),
            (-0.9, 1.5),
            (-1.8, 1.5),
            (-2.2, 1.5),
            (-1.5, 1.5),
            (-0.5, 1.5),
        ],
    }
}

# ------------------------------------------------------------------------------
# Ballistics and Damage Models
# ------------------------------------------------------------------------------
# Damage modifiers and penetration coefficients per weapon type.
# Values can be expanded for additional weapon categories.
BULLET_STATS = {
    'm4': {
        'helmet_pen': 0.75,  # Helmet penetration multiplier
        'helmet_dmg': 1,     # Damage dealt to helmeted targets
        'damage': 20,        # Base body damage per hit
    }
}
