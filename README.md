# CityU Curriculum Scraper & Visualization System

[中文文档](README_CN.md) | English

This project scrapes City University (CityU) undergraduate curriculum major pages and course detail pages, then outputs structured JSON/CSV and a relational SQLite database of courses and their prerequisite/exclusion relations, with visualization support for course dependency graphs.

## Environment Setup (Windows - Beginner-Friendly)

Follow these step-by-step instructions (no programming experience required):

### Step 0: Install Python (One-Time Setup)

- Download and install Python 3.11 or higher from <https://www.python.org/downloads/>
- During installation, check "Add python.exe to PATH" (if shown)

After installation, open a new PowerShell window and verify:

```powershell
py -3 --version
```

If `py` command is not found, try:

```powershell
python --version
```

### Step 1: Open Project Folder in PowerShell

- Method A: In File Explorer, type `powershell` in the address bar and press Enter
- Method B: In VS Code, go to Terminal → New Terminal (it opens in the project directory automatically)

Verify you're in the correct directory by checking for README.md:

```powershell
dir
```

### Step 2: Install Dependencies (First Time Only)

```powershell
py -3 -m pip install -U pip
py -3 -m pip install -r requirements.txt
```

If you get "py not found" error, replace `py -3` with `python`:

```powershell
python -m pip install -U pip
python -m pip install -r requirements.txt
```

### Common Beginner Issues (Instant Fixes)

- "py is not recognized as a command" → Use `python` instead of `py -3`, or restart PowerShell
- "pip is not recognized" → Use `python -m pip ...` instead of `pip ...`
- "requirements.txt not found" → Run `dir` to confirm you're in the project root directory
- Network/certificate errors → Try again later or switch networks; first-time downloads may be slow

### Advanced (Optional): Use Virtual Environment for Clean Isolation

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -U pip
pip install -r requirements.txt
python orchestrator.py run-all --verbose
```

To exit the virtual environment:

```powershell
deactivate
```

---

## 🚀 Beginner Quick Start (Super Simple)

**After completing the environment setup above, just 2 steps** to see the course dependency graph:

### Step 1: Run the Command in PowerShell

```powershell
py -3 orchestrator.py run-all --verbose
```

### Step 2: View the Generated Images

Open the latest `outputs/vNNN/` directory (e.g., `v001/`), which contains:

- `dependency_vNNN.png` - Full course dependency graph
- `roots_vNNN.png` - Roots-only graph (courses with no prerequisites)

The database file is located at `outputs/courses.db`.

---

### If the Run Fails (404 or Network Error): Edit Config File

The default URL may be outdated. Here's how to replace it:

**Step A: Find a Valid Course Page URL**

1. Open <https://www.cityu.edu.hk/catalogue/> in your browser
2. Navigate to the major you're interested in (e.g., Computer Science)
3. Copy the full URL from the browser address bar (example: `https://www.cityu.edu.hk/catalogue/ug/202425/Major/BSC1_CSC-1.htm`)

**Step B: Edit the Configuration File**

1. Right-click `config/scraper.toml` → "Open with" → Notepad (or VS Code)
2. Find these lines:

   ```toml
   urls = [
       "https://www.cityu.edu.hk/catalogue/ug/202425/Major/BSC1_CSC-1.htm",
   ]
   ```

3. **Delete** the old URL inside quotes and paste your new URL
4. Save the file (`Ctrl + S`)
5. Re-run Step 1 command

---

### Common Issues & Quick Fixes

| Problem | Solution |
|---------|----------|
| "py is not recognized" | Use `python` instead of `py -3`, or restart PowerShell |
| No images generated | Check network connection; verify `outputs/courses.db` exists; re-run |
| Nodes overlapping | Open `config/visualize_dependency.toml`, reduce `max_per_layer` (e.g., set to 3) |
| Missing prerequisites | Some pages use "Precursors" instead of "Prerequisites" (not currently parsed) |

---


## Architecture

```text
core/
  scraper/        # Networking & HTTP fetch layer
    http.py
    major_scraper.py
  dp_build/       # Parsing & data processing layer
    models.py
    parsers.py
    db_builder.py
  filter/         # Data filtering layer
    check.py
  vis/            # Visualization layer
    common.py
    dependency.py
    roots.py
config/           # Configuration files
  scraper.toml    # Scraper config (URLs, database reset, etc.)
  visualize_dependency.toml  # Dependency graph visualization config
  visualize_roots.toml       # Roots-only graph visualization config
orchestrator.py   # Single entrypoint CLI (subcommands)
outputs/          # All generated artifacts (JSON, CSV, DB, images)
  vNNN/           # Versioned output directories
README.md         # English documentation
README_CN.md      # Chinese documentation
requirements.txt
```

Key components:

- `core.scraper.http.fetch_html` handles HTTP with retries, timeouts, optional delay.
- `core.dp_build.parsers.parse_major_page` parses a major curriculum page and, when requested, follows course links to parse course detail pages.
- `core.dp_build.parsers.parse_course_page` parses each course detail page (title, units, offering unit, prerequisites, exclusions, assessment, PDF link, etc.).
- `orchestrator.py` offers two subcommands:
  - `scrape-major` to export JSON/CSV of one or multiple major pages.
  - `build-db` to produce a SQLite database of all courses and relations for a major.

  - Visualization utilities are included under the `visualize` subcommand to render dependency graphs from the SQLite DB.

## Quick Start

### Configuration File

## Environment Setup (Windows - Beginner-Friendly)

Follow these step-by-step instructions (no programming experience required):

### Step 0: Install Python (One-Time Setup)

- Download and install Python 3.11 or higher from <https://www.python.org/downloads/>
- During installation, check "Add python.exe to PATH" (if shown)

After installation, open a new PowerShell window and verify:

```powershell
py -3 --version
```

If `py` command is not found, try:

```powershell
python --version
```

### Step 1: Open Project Folder in PowerShell

- Method A: In File Explorer, type `powershell` in the address bar and press Enter
- Method B: In VS Code, go to Terminal → New Terminal (it opens in the project directory automatically)

Verify you're in the correct directory by checking for README.md:

```powershell
dir
```

### Step 2: Install Dependencies (First Time Only)

```powershell
py -3 -m pip install -U pip
py -3 -m pip install -r requirements.txt
```

If you get "py not found" error, replace `py -3` with `python`:

```powershell
python -m pip install -U pip
python -m pip install -r requirements.txt
```

### Step 3: One-Click Run to Generate Images

```powershell
py -3 orchestrator.py run-all --verbose
```

After successful execution, you'll find a new version directory in `outputs/` (e.g., `v043/`) containing the dependency graph `dependency_v043.png`. The database file is at `outputs/courses.db`.

### Common Beginner Issues (Instant Fixes)

- "py is not recognized as a command" → Use `python` instead of `py -3`, or restart PowerShell
- "pip is not recognized" → Use `python -m pip ...` instead of `pip ...`
- "requirements.txt not found" → Run `dir` to confirm you're in the project root directory
- Network/certificate errors → Try again later or switch networks; first-time downloads may be slow
- No images generated → Check if `outputs/` has a new `vNNN/` folder and verify `dependency_vNNN.png` exists inside

### Advanced (Optional): Use Virtual Environment for Clean Isolation

```powershell
python -m venv .venv
.\.venv\Scriptsctivate
python -m pip install -U pip
pip install -r requirements.txt
python orchestrator.py run-all --verbose
```

To exit the virtual environment:

```powershell
deactivate
```

## Quick Start

### Configuration File

Edit `config/scraper.toml` to set the URLs to scrape and database options:

```toml
[scraper]
# List of major curriculum URLs to scrape
urls = [
    "https://www.cityu.edu.hk/catalogue/ug/202425/Major/BSC1_CSC-1.htm",
]

[database]
# Whether to drop existing tables before building (true=reset, false=keep existing data)
reset = true

[cache]
cache_dir = "cache"
use_cache = false  # true=use cache, false=re-download every time
```

### Environment Setup (Windows)

Two options, pick one:

Option A) Use system Python (easiest)

```powershell
py -3 -m pip install -U pip
py -3 -m pip install -r requirements.txt
```

Then run with the same interpreter path:

```powershell
py -3 orchestrator.py run-all --verbose
```

Option B) Use a virtual environment (clean isolation)

```powershell
python -m venv .venv
. .venv\Scripts\activate
pip install -r requirements.txt
```

Then run:

```powershell
python orchestrator.py run-all --verbose
```

### One-Click Full Pipeline

Use the `run-all` command to execute the complete workflow: scrape → build database → ask if generate visualizations → interactive course query

```powershell
py -3 orchestrator.py run-all --verbose
```

This will:

1. Read URL from `config/scraper.toml`
2. Scrape all course information including semester data
3. Build SQLite database (`outputs/courses.db`)
4. **Ask if you want to generate visualizations** (enter yes/y to generate, no/n to skip)
5. Optional: Generate dependency and roots graphs in `outputs/vNNN/` directory
6. **Launch interactive course query system**

### Interactive Course Query Feature 🆕

After running `run-all`, the system automatically starts an interactive Q&A session where you can:

1. **Enter completed course codes** (separate multiple courses with spaces or commas)
   
   ```text
   > CS1315 SDSC1001
   ```

2. **Select semester to query**
   
   ```text
   Enter semester to query (A/B, or press Enter for all semesters):
   > A
   ```
   
   - Enter `A` - Show only Semester A courses
   - Enter `B` - Show only Semester B courses  
   - Press Enter - Show courses from all semesters

3. **View intelligent recommendations** organized into categories:
   - ✅ **Available Courses** - All prerequisites satisfied
   - 🌱 **Root Courses** - No prerequisites required (entry-level courses)
   - ⚠️ **Special Requirements** - Courses needing special approval or conditions (e.g., year level, CEC approval)
   - 💼 **Internship Programs** - Various internship courses
   - 📖 **Related Follow-up Courses** - Some prerequisites met, shows what's still needed

4. Enter `q` to exit the query

**Example Output**:

```text
✅ Available Courses (3 courses)
   • SDSC2003     Human Contexts and Ethics in Data Science
   • CS2334       Data Structures for Data Science

🌱 Root Courses (15 courses)
   • CS1315       Introduction to Computer Programming
   • GE1501       Chinese Civilisation - History and Philosophy
   ...

⚠️ Special Requirements (2 courses)
   • SDSC3026     International Professional Development
     Requirement: (1) Year 3 completed (2) CEC approval required

💼 Internship Programs (6 courses)
   • SDSC0001     Internship
   • SDSC0002     Internship
   ...
```

## Usage

### Individual Subcommands

#### 1. Scrape a single major page (JSON)

```powershell
python orchestrator.py scrape-major --url "https://www.cityu.edu.hk/catalogue/ug/2022/course/A_BScDS.htm" --out data_science.json --courses --verbose
```

### Scrape multiple major pages (URLs in a file)

`majors.txt` contains one URL per line (lines starting with `#` are skipped).

```powershell
python orchestrator.py scrape-major --file majors.txt --out majors.csv --format csv --courses --verbose
```

### Build course database for one major

```powershell
python orchestrator.py build-db --major-url "https://www.cityu.edu.hk/catalogue/ug/2022/course/A_BScDS.htm" --db courses.db --reset --verbose
```

Produces `outputs/courses.db` with tables:

- `courses(course_code PRIMARY KEY, course_title, offering_unit, credit_units, duration, semester, aims, assessment_json, pdf_url, url)` 🆕 Added `semester` field
- `prerequisites(course_code, prereq_code)` composite PK
- `exclusions(course_code, excluded_code)` composite PK
- `special_requirements(course_code PRIMARY KEY, requirement_text)` 🆕 Text-based special requirements

### Visualize course graphs (from SQLite DB)

You can render two views: a full dependency graph and a roots-only graph (courses without prerequisites). To avoid passing many flags, use the provided config presets.

Presets (editable):

- `config/visualize_dependency.toml`
- `config/visualize_roots.toml`

Run with a profile (auto-loads the matching config file):

```powershell
# Dependency graph + roots-only bundle into next outputs/vNNN
python orchestrator.py visualize --profile dependency --verbose

# Roots-only graph (also bundles, keeping version parity)
python orchestrator.py visualize --profile roots --verbose
```

Or run with an explicit config path:

```powershell
python orchestrator.py visualize --config config/visualize_dependency.toml --verbose
python orchestrator.py visualize --config config/visualize_roots.toml --verbose
```

Notes:

- All visualize options are read from the config file; you typically do not need to pass flags.
- The presets enable `bundle_version = true`, which auto-creates `outputs/vNNN/` and writes both images per version:
  - `dependency_vNNN.png`
  - `roots_only_vNNN.png`
- If you prefer single-file output, set `bundle_version = false` and set an `out` path in the `[visualize]` section.

### Troubleshooting: verify config is applied

Use the built-in inspector to print the merged config and visualize settings without rendering:

```powershell
# Using a profile (loads config/visualize_dependency.toml)
python orchestrator.py show-config --profile dependency

# Or inspect an explicit config path
python orchestrator.py --config config/visualize_dependency.toml show-config
```

Run with `--verbose` on `visualize` to see effective settings echoed before rendering. If your edits aren't reflected, ensure you're invoking the intended Python interpreter (e.g., a virtualenv) and that the correct config file is being loaded.

### One-click render script (Windows PowerShell)

Use the convenience script to always run with the right interpreter and generate both images in one go:

```powershell
# Default: dependency profile + bundle version
powershell -ExecutionPolicy Bypass -File .\scripts\render.ps1 -Verbose

# Roots-only profile (still bundles both images for the next vNNN)
powershell -ExecutionPolicy Bypass -File .\scripts\render.ps1 -Profile roots -Verbose

# Explicit config file (overrides profile)
powershell -ExecutionPolicy Bypass -File .\scripts\render.ps1 -Config config/visualize_dependency.toml -Verbose
```

Notes:

- The script uses your default Windows interpreter (via `py -3`) by default. Edit `scripts/render.ps1` if your interpreter differs, or switch it to `.venv\Scripts\python.exe`.
- Add `-Verbose` to print the merged config (show-config) and the effective settings before rendering.

### Export Paths

Override output directory with `--out-dir`:

```powershell
python orchestrator.py scrape-major --url "..." --out ds.json --out-dir d:\data\cityu
```

## Data Model (Major JSON)

Each major record in JSON format:

```json
{
  "url": "https://.../A_BScDS.htm",
  "program_title": "Data Science",
  "program_code": "BScDS",
  "aims": "...",
  "il_outcomes": ["Outcome 1", "Outcome 2"],
  "structure_tables": [
    {"caption": "Year 1", "headers": ["Course", "Credit"], "rows": [["SDSC1001", "3"], ["CS1102", "3"]]},
    {"caption": "Year 2", "headers": [], "rows": [["...", "..."]]}
  ],
  "remarks": "...",
  "courses": [
    {
      "course_code": "SDSC2001",
      "course_title": "Probability and Statistics",
      "offering_unit": "Department of ...",
      "credit_units": "3",
      "duration": "One semester",
      "aims": "...",
      "prerequisites": "MA2510 or equivalent",
      "exclusive_courses": "",
      "assessment": {"Coursework": "40%", "Exam": "60%"},
      "pdf_url": "https://.../syllabus.pdf",
      "url": "https://.../course/SDSC2001.htm"
    }
  ]
}
```

## Notes & Assumptions

- Course code detection uses regex `[A-Z]{2,}\d{3,4}`.
- Network politeness: use `--delay` to throttle requests.
- Some pages may have inconsistent HTML; parser attempts to be resilient but may miss edge cases.
- Assessment breakdown stored as a JSON object in `assessment_json` column.

## Extending

- Add new parsing heuristics in `core/dp_build/parsers.py`.
- Add new output formats by extending `orchestrator.py` (e.g., Parquet, Excel) once core data model is stable.
- Consider caching downloaded HTML in a separate folder if re-running frequently.

## Next Ideas

- Add a `--cache-dir` flag to reuse stored HTML.
- Introduce basic unit tests for selectors.
- Add concurrency for course detail requests with rate limiting.

## Privacy & Publishing to GitHub

Before publishing this project to GitHub, ensure you don't leak personal information:

- Don't commit absolute local paths (already replaced with generic `py -3`)
- Remove any temporary debug output, personal emails, or names
- Add `outputs/` to `.gitignore` (unless you want to showcase sample outputs)
- If using a virtual environment, ensure `.venv/` is excluded
- Review `config/` files for any internal-only URLs before making them public

Before pushing to a public repository, run these checks:

```powershell
git grep -i "users"
git grep -i "asus"
git status
```

Ensure no sensitive paths or user-specific data appear in the results.

## License

Internal/educational use. Review CityU site terms before large-scale crawling.
