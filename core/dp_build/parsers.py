import re
import os
from typing import Optional, List, Dict, Any, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
import requests

from .models import MajorPage, StructureTable
from core.scraper.http import fetch_html


def normalize_space(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def text_or_none(el) -> Optional[str]:
    if not el:
        return None
    return normalize_space(el.get_text(" "))


def parse_course_page(code: str, url: str, html: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")
    title_el = soup.select_one("#div_course_code_and_title")
    full_title = normalize_space(title_el.get_text(" ")) if title_el else code
    course_title = full_title.split(" - ", 1)[1] if " - " in full_title else full_title
    offering_unit = text_or_none(soup.select_one("#div_offering_dept"))
    credit_units = text_or_none(soup.select_one("#div_course_credits"))
    duration = text_or_none(soup.select_one("#div_course_duration"))
    
    # Extract semester from course offering term (e.g., "Semester A 2025/26" -> "A")
    semester_raw = text_or_none(soup.select_one("#div_course_offering_term"))
    semester = None
    if semester_raw:
        # Extract semester letter (A, B, or both)
        if 'Semester A' in semester_raw and 'Semester B' in semester_raw:
            semester = 'A, B'
        elif 'Semester A' in semester_raw:
            semester = 'A'
        elif 'Semester B' in semester_raw:
            semester = 'B'
    
    prerequisites_raw = text_or_none(soup.select_one("#div_prerequisites"))
    prerequisites = prerequisites_raw.replace("\n", " ") if prerequisites_raw else None
    exclusive_raw = text_or_none(soup.select_one("#div_exclusive_courses"))
    exclusive_courses = None
    if exclusive_raw:
        exclusive_courses = ", ".join(sorted(set(re.findall(r"[A-Z]{2,}\d{3,4}", exclusive_raw))))
    aims = text_or_none(soup.select_one("#div_course_aims"))
    assessment = {
        "coursework_pct": text_or_none(soup.select_one("#div_assessment_coursework_pct")),
        "exam_pct": text_or_none(soup.select_one("#div_assessment_exam_pct")),
        "exam_duration": text_or_none(soup.select_one("#div_exam_duration")),
        "min_exam_pass_pct": text_or_none(soup.select_one("#div_min_exam_pass_pct")),
        "min_cont_pass_pct": text_or_none(soup.select_one("#div_min_cont_pass_pct")),
        "assessment_notes": text_or_none(soup.select_one("#div_assessment_supp")),
    }
    pdf_url_el = soup.select_one("#pdf_url")
    pdf_relative = pdf_url_el.get_text(strip=True) if pdf_url_el else None
    pdf_url = None
    if pdf_relative and pdf_relative.lower().endswith('.pdf'):
        a_parent = pdf_url_el.find_parent('a')
        if a_parent and a_parent.get('href'):
            pdf_url = a_parent.get('href')
    return {
        "course_code": code,
        "url": url,
        "course_title": course_title,
        "offering_unit": offering_unit,
        "credit_units": credit_units,
        "duration": duration,
        "semester": semester,
        "prerequisites": prerequisites,
        "exclusive_courses": exclusive_courses,
        "aims": aims,
        "assessment": assessment,
        "pdf_url": pdf_url,
    }


def parse_major_page(
    url: str,
    html: str,
    *,
    include_courses: bool = False,
    session: Optional[requests.Session] = None,
    delay: float = 0.0,
    timeout: float = 15.0,
    retries: int = 3,
    verbose: bool = False,
    concurrency: int = 1,
    cache_dir: Optional[str] = None,
) -> MajorPage:
    soup = BeautifulSoup(html, "lxml")

    header_title = soup.select_one("#div_prog_title_header")
    alt_title = soup.select_one("#div_prog_title")
    program_title = None
    if header_title:
        program_title = normalize_space(header_title.get_text(" "))
    elif alt_title:
        program_title = normalize_space(alt_title.get_text(" "))
    else:
        program_title = text_or_none(soup.title)

    program_code = None
    m_url = re.search(r"/([A-Z0-9]+_[A-Z0-9]+)-\d+\.htm", url, re.I)
    if m_url:
        program_code = m_url.group(1).upper()

    aims = None
    il_outcomes: List[str] = []

    structure_tables: List[StructureTable] = []
    content_root = soup.select_one("#cityu-content") or soup
    tables = content_root.find_all("table", attrs={"border": True})

    def infer_caption(tbl) -> Optional[str]:
        for prev in tbl.find_all_previous(limit=25):
            if prev is tbl:
                continue
            if prev.name == "table":
                return None
            txt = normalize_space(prev.get_text(" ")) if prev.get_text(strip=True) else ""
            if not txt:
                continue
            if len(txt) > 300:
                continue
            classes = " ".join(prev.get("class", []))
            if any(key in classes for key in ["formText", "colorTitle", "formTitle"]) or prev.name in ["strong", "p", "div"]:
                return txt[:120]
        return None

    for tbl in tables:
        tbl_text = tbl.get_text(" ")
        if not re.search(r"Course Code|Credit Units|GE|SDSC", tbl_text, re.I):
            continue
        caption = infer_caption(tbl)
        headers: List[str] = []
        thead = tbl.find("thead")
        if thead:
            headers = [normalize_space(th.get_text(" ")) for th in thead.find_all(["th", "td"])]
        else:
            first_row = tbl.find("tr")
            if first_row:
                headers = [normalize_space(c.get_text(" ")) for c in first_row.find_all(["th", "td"])]
        rows: List[List[str]] = []
        for tr in tbl.find_all("tr"):
            cells = tr.find_all(["td", "th"])
            if not cells:
                continue
            row = [normalize_space(c.get_text(" ")) for c in cells]
            if row and row != headers:
                rows.append(row)
        structure_tables.append(StructureTable(caption=caption, headers=headers, rows=rows))

    remarks = None
    notes_block = soup.find(string=re.compile(r"Notes?:|\*Remark", re.I))
    if notes_block:
        parent = notes_block.parent
        rem_parts: List[str] = []
        for sib in parent.find_all_next():
            if sib.name == "table":
                break
            if sib.get_text(strip=True):
                txt = normalize_space(sib.get_text(" "))
                if txt and not re.match(r"Notes?:", txt, re.I):
                    rem_parts.append(txt)
            if len(rem_parts) > 10:
                break
        if rem_parts:
            remarks = "\n".join(rem_parts)

    courses: List[Dict[str, Any]] = []
    if include_courses:
        codes: Set[str] = set()
        code_pattern = re.compile(r"\b([A-Z]{2,}\d{3,4})\b")
        for t in structure_tables:
            for row in t.rows:
                for cell in row:
                    for m in code_pattern.finditer(cell):
                        codes.add(m.group(1))
        base_course_url = "https://www.cityu.edu.hk/catalogue/ug/current/course/"

        # Fetch function (separate session per thread for safety)
        def fetch_one(code: str) -> Dict[str, Any]:
            course_url = f"{base_course_url}{code}.htm"
            key = course_url.replace("https://", "").replace("http://", "").replace("/", "_")
            try:
                # Try cache first when available
                html_c: Optional[str] = None
                if cache_dir:
                    try:
                        path = os.path.join(cache_dir, key + ".html")
                        if os.path.isfile(path):
                            with open(path, "r", encoding="utf-8") as f:
                                html_c = f.read()
                    except Exception:
                        html_c = None
                if html_c is None:
                    html_c = fetch_html(course_url, session=None, delay=delay, timeout=timeout, retries=retries)
                    if cache_dir:
                        try:
                            os.makedirs(cache_dir, exist_ok=True)
                            with open(os.path.join(cache_dir, key + ".html"), "w", encoding="utf-8") as f:
                                f.write(html_c)
                        except Exception:
                            pass
                info = parse_course_page(code, course_url, html_c)
                return info
            except Exception as e:
                return {"course_code": code, "url": course_url, "error": str(e)}

        code_list = sorted(codes)
        if concurrency <= 1:
            # Serial
            for idx, code in enumerate(code_list, 1):
                if verbose:
                    print(f"  [courses] {idx}/{len(code_list)} {code}")
                courses.append(fetch_one(code))
        else:
            # Concurrent
            if verbose:
                print(f"  [courses] fetching {len(code_list)} courses with {concurrency} workers...")
            with ThreadPoolExecutor(max_workers=max(1, concurrency)) as ex:
                future_map = {ex.submit(fetch_one, code): code for code in code_list}
                done = 0
                for fut in as_completed(future_map):
                    res = fut.result()
                    courses.append(res)
                    done += 1
                    if verbose and (done % 5 == 0 or done == len(code_list)):
                        print(f"    progress: {done}/{len(code_list)}")

    return MajorPage(
        url=url,
        program_title=program_title,
        program_code=program_code,
        aims=aims,
        il_outcomes=il_outcomes,
        structure_tables=structure_tables,
        remarks=remarks,
        courses=courses,
    )
