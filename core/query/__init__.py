"""Interactive course query module.

Provides interactive Q&A interface for querying available courses
based on completed prerequisites.
"""

from .course_finder import find_available_courses, get_special_requirements
from .interactive import interactive_course_query

__all__ = [
    'find_available_courses',
    'get_special_requirements',
    'interactive_course_query',
]
