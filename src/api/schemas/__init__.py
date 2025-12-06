"""
API Schemas Package
"""

from .animal_schemas import *
from .detection_schemas import *
from .response_schemas import *

__all__ = [
    # Animal schemas
    'AnimalBase',
    'AnimalCreate',
    'AnimalUpdate',
    'AnimalResponse',
    'AnimalListResponse',
    # Detection schemas
    'DetectionBase',
    'DetectionCreate',
    'DetectionResponse',
    'DetectionListResponse',
    'BoundingBox',
    # Response schemas
    'BaseResponse',
    'SuccessResponse',
    'ErrorResponse',
    'PaginatedResponse'
]
