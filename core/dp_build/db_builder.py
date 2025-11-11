"""Database builder for course data."""
import json
import os
import re
import sqlite3
import sys
from typing import Optional

from core.scraper.http import fetch_html
from core.scraper.cache import maybe_read_cache, write_cache
from core.dp_build.parsers import parse_major_page


def build_course_db(
    major_url: str,
    db_path: str,
    *,
    delay: float = 0.2,
    timeout: float = 15.0,
    retries: int = 3,
    verbose: bool = False,
    concurrency: int = 4,
    reset: bool = False,
    cache_dir: Optional[str] = None,
    out_dir: Optional[str] = None
) -> dict:
    """Build SQLite database from a major curriculum page.
    
    Args:
        major_url: URL of the major curriculum page
        db_path: path to SQLite database file
        delay: delay between requests
        timeout: request timeout
        retries: number of retries for failed requests
        verbose: print progress messages
        concurrency: number of concurrent workers for course fetching
        reset: drop existing tables before creating
        cache_dir: directory for HTML cache
        out_dir: output directory for failed courses log
        
    Returns:
        dict with statistics: courses, prerequisites, exclusions counts
    """
    # Fetch major page HTML
    html = maybe_read_cache(cache_dir, major_url)
    if html is None:
        html = fetch_html(major_url, timeout=timeout, retries=retries, delay=delay)
        write_cache(cache_dir, major_url, html)
    
    # Parse major page and fetch course details
    mp = parse_major_page(
        major_url,
        html,
        include_courses=True,
        delay=delay,
        timeout=timeout,
        retries=retries,
        verbose=verbose,
        concurrency=concurrency,
        cache_dir=cache_dir,
    )
    
    # Ensure db directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Create/connect to database
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    if reset:
        cur.execute("DROP TABLE IF EXISTS courses")
        cur.execute("DROP TABLE IF EXISTS prerequisites")
        cur.execute("DROP TABLE IF EXISTS exclusions")
        cur.execute("DROP TABLE IF EXISTS special_requirements")
    
    # Create tables
    cur.execute(
        "CREATE TABLE IF NOT EXISTS courses ("
        "course_code TEXT PRIMARY KEY, "
        "course_title TEXT, "
        "offering_unit TEXT, "
        "credit_units TEXT, "
        "duration TEXT, "
        "semester TEXT, "
        "aims TEXT, "
        "assessment_json TEXT, "
        "pdf_url TEXT, "
        "url TEXT)"
    )
    cur.execute(
        "CREATE TABLE IF NOT EXISTS prerequisites ("
        "course_code TEXT, "
        "prereq_code TEXT, "
        "PRIMARY KEY(course_code, prereq_code))"
    )
    cur.execute(
        "CREATE TABLE IF NOT EXISTS exclusions ("
        "course_code TEXT, "
        "excluded_code TEXT, "
        "PRIMARY KEY(course_code, excluded_code))"
    )
    cur.execute(
        "CREATE TABLE IF NOT EXISTS special_requirements ("
        "course_code TEXT PRIMARY KEY, "
        "requirement_text TEXT)"
    )
    
    # Insert course data
    for c in mp.courses:
        code = c.get("course_code")
        if not code:
            continue
        
        cur.execute(
            "INSERT OR REPLACE INTO courses VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                code,
                c.get("course_title"),
                c.get("offering_unit"),
                c.get("credit_units"),
                c.get("duration"),
                c.get("semester"),
                c.get("aims"),
                json.dumps(c.get("assessment") or {}, ensure_ascii=False),
                c.get("pdf_url"),
                c.get("url"),
            )
        )
        
        # Extract and insert prerequisites
        prereq_text = c.get("prerequisites") or ""
        prereq_codes = set(re.findall(r"[A-Z]{2,}\d{3,4}", prereq_text))
        
        # Check if there are no prerequisite codes but there is text content
        # This indicates special text requirements
        if not prereq_codes and prereq_text and prereq_text.strip():
            # Clean up the text (remove extra whitespace)
            cleaned_text = re.sub(r'\s+', ' ', prereq_text).strip()
            # Skip if it's just "Nil" or "None" or similar, or contains only HKDSE requirements
            lower_text = cleaned_text.lower()
            is_hkdse_only = 'hkdse' in lower_text or 'dse' in lower_text
            is_nil = lower_text in ['nil', 'none', 'n/a', 'na', '-', '']
            
            # Only store if it's not nil and not HKDSE-only requirement
            if not is_nil and not is_hkdse_only:
                cur.execute(
                    "INSERT OR REPLACE INTO special_requirements VALUES (?,?)",
                    (code, cleaned_text)
                )
        
        # Insert normal prerequisite codes
        for p in prereq_codes:
            if p != code:
                cur.execute("INSERT OR IGNORE INTO prerequisites VALUES (?,?)", (code, p))
        
        # Extract and insert exclusions
        excl_codes = set(re.findall(r"[A-Z]{2,}\d{3,4}", c.get("exclusive_courses") or ""))
        for e in excl_codes:
            if e != code:
                cur.execute("INSERT OR IGNORE INTO exclusions VALUES (?,?)", (code, e))
        
        # Log failed courses
        if c.get("error") and verbose and out_dir:
            try:
                os.makedirs(out_dir, exist_ok=True)
                with open(os.path.join(out_dir, "failed_courses.txt"), "a", encoding="utf-8") as f:
                    f.write(f"{code}\t{c.get('url')}\t{c.get('error')}\n")
            except Exception:
                pass
    
    conn.commit()
    
    # Get statistics
    cur.execute("SELECT COUNT(*) FROM courses")
    n_courses = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM prerequisites")
    n_prereq = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM exclusions")
    n_excl = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM special_requirements")
    n_special = cur.fetchone()[0]
    
    conn.close()
    
    if verbose:
        print(f"DB saved -> {db_path} courses={n_courses} prereq={n_prereq} excl={n_excl} special={n_special}")
    
    return {
        "courses": n_courses,
        "prerequisites": n_prereq,
        "exclusions": n_excl,
        "special_requirements": n_special,
        "db_path": db_path
    }
