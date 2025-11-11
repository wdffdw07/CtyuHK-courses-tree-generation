"""Course availability finder based on completed prerequisites.

This module provides functions to query the course database and find:
- Courses that can be taken (all prerequisites met)
- Related follow-up courses (partial prerequisites met)
- Root courses (no prerequisites required)
"""

import sqlite3
from typing import List, Dict, Tuple


def find_available_courses(db_path: str, completed_courses: List[str], semester_filter: str = None) -> Dict[str, list]:
    """Find courses that can be taken based on completed courses.
    
    Args:
        db_path: Path to SQLite database
        completed_courses: List of completed course codes
        semester_filter: Semester to filter ('A', 'B', or None for all)
        
    Returns:
        Dictionary with:
        - 'available': courses with all prerequisites met
        - 'no_prereq': courses with no prerequisites (root courses)
        - 'completed_children': direct children of completed courses
        
    Example:
        >>> results = find_available_courses('courses.db', ['CS1315', 'SDSC1001'], 'A')
        >>> print(results['available'])
        [('SDSC2003', 'Human Contexts and Ethics in Data Science')]
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Normalize completed courses to uppercase
    completed = set(c.strip().upper() for c in completed_courses)
    
    # Get all courses, optionally filtered by semester
    if semester_filter and semester_filter.upper() in ['A', 'B']:
        cursor.execute("SELECT course_code, course_title, semester FROM courses WHERE semester LIKE ?", 
                      (f'%{semester_filter.upper()}%',))
    else:
        cursor.execute("SELECT course_code, course_title, semester FROM courses")
    
    all_courses = {row[0]: row[1] for row in cursor.fetchall()}
    
    # Get all prerequisite relationships
    cursor.execute("SELECT course_code, prereq_code FROM prerequisites")
    prereqs = {}
    for course, prereq in cursor.fetchall():
        if course not in prereqs:
            prereqs[course] = []
        prereqs[course].append(prereq)
    
    # Find root courses (no prerequisites)
    no_prereq = []
    for course in all_courses:
        if course not in prereqs and course not in completed:
            no_prereq.append((course, all_courses[course]))
    
    # Find available courses (all prerequisites met)
    available = []
    for course in all_courses:
        if course in completed:
            continue
        if course in prereqs:
            # Check if all prerequisites are in completed
            if all(p in completed for p in prereqs[course]):
                available.append((course, all_courses[course]))
        else:
            # No prerequisites, already in no_prereq
            pass
    
    # Find children of completed courses (courses that have completed courses as prerequisites)
    completed_children = []
    for course in all_courses:
        if course in completed:
            continue
        if course in prereqs:
            # Check if any prerequisite is in completed (direct children)
            if any(p in completed for p in prereqs[course]):
                completed_children.append((course, all_courses[course], prereqs[course]))
    
    conn.close()
    
    return {
        'available': sorted(available),
        'no_prereq': sorted(no_prereq),
        'completed_children': sorted(completed_children, key=lambda x: x[0])
    }


def get_course_info(db_path: str, course_code: str) -> Dict[str, any]:
    """Get detailed information about a specific course.
    
    Args:
        db_path: Path to SQLite database
        course_code: Course code to query
        
    Returns:
        Dictionary with course information or None if not found
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    course_code = course_code.strip().upper()
    
    cursor.execute(
        "SELECT course_code, course_title, offering_unit, credit_units FROM courses WHERE course_code = ?",
        (course_code,)
    )
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return None
    
    # Get prerequisites
    cursor.execute("SELECT prereq_code FROM prerequisites WHERE course_code = ?", (course_code,))
    prereqs = [r[0] for r in cursor.fetchall()]
    
    # Get exclusions
    cursor.execute("SELECT excluded_code FROM exclusions WHERE course_code = ?", (course_code,))
    exclusions = [r[0] for r in cursor.fetchall()]
    
    conn.close()
    
    return {
        'code': row[0],
        'title': row[1],
        'unit': row[2],
        'credits': row[3],
        'prerequisites': prereqs,
        'exclusions': exclusions,
    }


def get_special_requirements(db_path: str) -> Dict[str, str]:
    """Get all courses with special (text-based) requirements.
    
    Args:
        db_path: Path to SQLite database
        
    Returns:
        Dictionary mapping course codes to their special requirement text
        
    Example:
        >>> reqs = get_special_requirements('courses.db')
        >>> print(reqs.get('CS3001'))
        'Instructor's approval required'
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT course_code, requirement_text FROM special_requirements")
    requirements = {row[0]: row[1] for row in cursor.fetchall()}
    
    conn.close()
    
    return requirements
