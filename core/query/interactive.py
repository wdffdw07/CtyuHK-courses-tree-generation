"""Interactive course query interface.

Provides a user-friendly Q&A interface for students to query
available courses based on their completed prerequisites.
"""

from typing import List, Tuple, Dict
from .course_finder import find_available_courses, get_special_requirements


def format_prerequisite_status(prereqs: List[str], completed: List[str]) -> str:
    """Format prerequisite list with completion status indicators.
    
    Args:
        prereqs: List of prerequisite course codes
        completed: List of completed course codes
        
    Returns:
        Formatted string with ✓/✗ indicators
        
    Example:
        >>> format_prerequisite_status(['CS1315', 'CS2315'], ['CS1315'])
        '✓CS1315, ✗CS2315'
    """
    completed_upper = [c.upper() for c in completed]
    prereq_status = []
    
    for p in prereqs:
        if p.upper() in completed_upper:
            prereq_status.append(f"✓{p}")
        else:
            prereq_status.append(f"✗{p}")
    
    return ", ".join(prereq_status)


def display_results(results: dict, completed: List[str], db_path: str = None) -> None:
    """Display query results in a formatted manner.
    
    Args:
        results: Dictionary from find_available_courses()
        completed: List of completed course codes
        db_path: Path to database (optional, for special requirements)
    """
    print("=" * 70)
    
    # Get special requirements if db_path is provided
    special_reqs = {}
    if db_path:
        try:
            special_reqs = get_special_requirements(db_path)
        except Exception:
            pass
    
    # 1. Available courses (all prerequisites met)
    if results['available']:
        print(f"\n✅ 可直接选修的课程 ({len(results['available'])} 门)")
        print(f"   Available Courses (all prerequisites met):\n")
        for code, title in results['available']:
            print(f"   • {code:12s} {title}")
    else:
        print("\n✅ 可直接选修的课程: 无")
        print("   Available Courses: None")
    
    # 2. Separate root courses into different categories
    if results['no_prereq']:
        # Separate internship courses and special requirement courses
        internship_courses = []
        special_req_courses = []
        regular_courses = []
        
        for code, title in results['no_prereq']:
            if 'internship' in title.lower() or 'internship' in code.lower():
                internship_courses.append((code, title))
            elif code in special_reqs:
                special_req_courses.append((code, title, special_reqs[code]))
            else:
                regular_courses.append((code, title))
        
        # Display regular root courses (no prerequisites)
        if regular_courses:
            print(f"\n🌱 无前置要求的课程 ({len(regular_courses)} 门)")
            print(f"   Root Courses (no prerequisites required):\n")
            for code, title in regular_courses:
                print(f"   • {code:12s} {title}")
        
        # Display special requirement courses
        if special_req_courses:
            print(f"\n⚠️  特别要求课程 ({len(special_req_courses)} 门)")
            print(f"   Courses with Special Requirements:\n")
            for code, title, req_text in special_req_courses:
                print(f"   • {code:12s} {title}")
                print(f"     要求 / Requirement: {req_text}")
        
        # Display internship courses
        if internship_courses:
            print(f"\n💼 实习项目 ({len(internship_courses)} 门)")
            print(f"   Internship Programs:\n")
            for code, title in internship_courses:
                print(f"   • {code:12s} {title}")
    
    # 3. Courses that depend on completed courses (might have other prereqs)
    if results['completed_children']:
        print(f"\n📖 相关后续课程 ({len(results['completed_children'])} 门)")
        print(f"   Related Follow-up Courses (may have other prerequisites):\n")
        for code, title, prereqs in results['completed_children']:
            prereq_str = format_prerequisite_status(prereqs, completed)
            print(f"   • {code:12s} {title}")
            print(f"     前置要求 / Prerequisites: {prereq_str}")
    
    print("\n" + "=" * 70)


def parse_course_input(user_input: str) -> List[str]:
    """Parse user input into a list of course codes.
    
    Args:
        user_input: Raw user input string
        
    Returns:
        List of course codes
        
    Example:
        >>> parse_course_input("CS1315, SDSC1001 GE1401")
        ['CS1315', 'SDSC1001', 'GE1401']
    """
    completed = []
    for item in user_input.replace(',', ' ').split():
        if item.strip():
            completed.append(item.strip())
    return completed


def interactive_course_query(db_path: str, verbose: bool = False) -> None:
    """Interactive session for querying available courses based on completed courses.
    
    Args:
        db_path: Path to SQLite database
        verbose: Enable verbose error messages
        
    This function starts an interactive loop where users can:
    - Enter completed course codes
    - View available courses based on prerequisites
    - See related follow-up courses
    - Browse root courses (no prerequisites)
    """
    print("\n" + "=" * 70)
    print("📚 交互式课程查询 / Interactive Course Query")
    print("=" * 70)
    print("\n提示：")
    print("  • 你可以直接从 outputs 文件夹里查看课程树")
    print("  • 也可以直接告诉我你已经学过哪些课程，我将帮你查找可选课程")
    print("\nTips:")
    print("  • You can view the course tree directly from the outputs folder")
    print("  • Or tell me which courses you've completed, and I'll find available courses for you")
    print("\n" + "-" * 70)
    
    while True:
        print("\n请输入已完成的课程代码 (多个课程用空格或逗号分隔，输入 'q' 退出):")
        print("Enter completed course codes (separate with spaces/commas, 'q' to quit):")
        user_input = input("> ").strip()
        
        if not user_input or user_input.lower() == 'q':
            print("\n感谢使用！Goodbye! 👋\n")
            break
        
        # Parse input
        completed = parse_course_input(user_input)
        
        if not completed:
            print("⚠️  未检测到有效的课程代码 / No valid course codes detected")
            continue
        
        print(f"\n🔍 正在分析已完成课程: {', '.join(completed)}")
        print(f"   Analyzing completed courses: {', '.join(completed)}\n")
        
        # Ask for semester filter
        print("请输入要查询的学期 (A/B，或直接回车查看所有学期):")
        print("Enter semester to query (A/B, or press Enter for all semesters):")
        semester_input = input("> ").strip().upper()
        
        semester_filter = None
        if semester_input in ['A', 'B']:
            semester_filter = semester_input
            print(f"\n📅 过滤学期: Semester {semester_filter}")
            print(f"   Filtering: Semester {semester_filter}\n")
        else:
            print(f"\n📅 显示所有学期的课程")
            print(f"   Showing courses from all semesters\n")
        
        try:
            results = find_available_courses(db_path, completed, semester_filter)
            display_results(results, completed, db_path)
            
        except Exception as e:
            print(f"\n❌ 查询出错 / Error occurred: {e}")
            if verbose:
                import traceback
                traceback.print_exc()
