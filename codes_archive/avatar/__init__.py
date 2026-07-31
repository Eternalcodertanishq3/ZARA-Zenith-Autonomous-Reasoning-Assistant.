"""
ZARA Avatar Module
==================
VRM avatar rendering and expression management.
Supports both 2D placeholder and full 3D VRM rendering.
"""
# Legacy renderer
try:
    from .renderer import AvatarRenderer
except ImportError:
    AvatarRenderer = None

# 2D VRM renderer (placeholder)
try:
    from .vrm_renderer import (
        VRMAvatarRenderer,
        AvatarConfig,
        Expression,
        ExpressionState,
        get_avatar,
        create_face_handler
    )
except ImportError:
    VRMAvatarRenderer = None
    AvatarConfig = None
    Expression = None
    ExpressionState = None
    get_avatar = None
    create_face_handler = None

# Advanced 3D VRM renderer
try:
    from .vrm_3d_renderer import (
        VRM3DRenderer,
        VRMLoader,
        VRMModel,
        create_face_handler_3d
    )
except ImportError:
    VRM3DRenderer = None
    VRMLoader = None
    VRMModel = None
    create_face_handler_3d = None

__all__ = [
    # Legacy
    'AvatarRenderer',
    # 2D renderer
    'VRMAvatarRenderer',
    'AvatarConfig', 
    'Expression',
    'ExpressionState',
    'get_avatar',
    'create_face_handler',
    # 3D renderer
    'VRM3DRenderer',
    'VRMLoader',
    'VRMModel',
    'create_face_handler_3d'
]
