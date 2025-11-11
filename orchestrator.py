import argparse
import json
import os
import sys
from pathlib import Path
from typing import List

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # fallback for older Python

from core.scraper.major_scraper import scrape_major_pages
from core.dp_build.export import save_json, save_csv
from core.dp_build.db_builder import build_course_db
from core.filter.check import load_allowed_codes, filter_db_by_allowed
from core.vis.dependency import render_dependency_tree
from core.vis.roots import render_root_courses
from core.config import load_config as _load_config
from core.query import interactive_course_query

DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")
DEFAULT_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)


def cmd_scrape_major(args: argparse.Namespace) -> int:
    """CLI handler for scrape-major command."""
    # Read URLs from argument or file
    urls: List[str] = []
    if args.url:
        urls = [args.url]
    else:
        with open(args.file, "r", encoding="utf-8") as f:
            urls = [l.strip() for l in f if l.strip() and not l.startswith("#")]
    
    # Call core scraping logic
    results = scrape_major_pages(
        urls,
        delay=args.delay,
        timeout=args.timeout,
        retries=args.retries,
        verbose=args.verbose,
        include_courses=args.courses,
        concurrency=args.concurrency,
        cache_dir=args.cache_dir,
    )

    out_dir = args.out_dir or DEFAULT_OUTPUT_DIR
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, args.out)
    if args.format == "json":
        save_json(results, out_path)
    else:
        save_csv(results, out_path)
    if args.verbose:
        print(f"Saved {len(results)} records -> {out_path}")
    return 0


def build_db(args: argparse.Namespace) -> int:
    """CLI handler for build-db command."""
    # Load scraper config if major_url not provided
    major_url = args.major_url
    reset = args.reset
    
    scraper_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "scraper.toml")
    if os.path.exists(scraper_config_path):
        with open(scraper_config_path, "rb") as f:
            config = tomllib.load(f)
            # Load URL if not provided via command line
            if not major_url:
                urls = config.get("scraper", {}).get("urls", [])
                if urls:
                    major_url = urls[0]  # Use first URL from config
                    if args.verbose:
                        print(f"Using URL from config: {major_url}")
            # Load reset setting if not provided via command line
            if not args.reset:
                reset = config.get("database", {}).get("reset", False)
                if args.verbose and reset:
                    print(f"Database reset enabled from config")
    
    if not major_url:
        print("Error: --major-url not provided and no URLs found in config/scraper.toml", file=sys.stderr)
        return 1
    
    out_dir = args.out_dir or DEFAULT_OUTPUT_DIR
    db_path = os.path.join(out_dir, args.db)
    
    # Call core DB builder
    stats = build_course_db(
        major_url,
        db_path,
        delay=args.delay,
        timeout=args.timeout,
        retries=args.retries,
        verbose=args.verbose,
        concurrency=args.concurrency,
        reset=reset,
        cache_dir=args.cache_dir,
        out_dir=out_dir,
    )
    
    return 0


def cmd_run_all(args: argparse.Namespace) -> int:
    """CLI handler for run-all command: build DB + visualize."""
    # Load scraper config if major_url not provided
    major_url = args.major_url
    reset = args.reset
    
    scraper_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "scraper.toml")
    if os.path.exists(scraper_config_path):
        with open(scraper_config_path, "rb") as f:
            config = tomllib.load(f)
            # Load URL if not provided via command line
            if not major_url:
                urls = config.get("scraper", {}).get("urls", [])
                if urls:
                    major_url = urls[0]  # Use first URL from config
                    if args.verbose:
                        print(f"Using URL from config: {major_url}")
            # Load reset setting if not provided via command line
            if not args.reset:
                reset = config.get("database", {}).get("reset", False)
                if args.verbose and reset:
                    print(f"Database reset enabled from config")
    
    if not major_url:
        print("Error: --major-url not provided and no URLs found in config/scraper.toml", file=sys.stderr)
        return 1
    
    if args.verbose:
        print("=" * 60)
        print("STEP 1/2: Building database from major URL")
        print("=" * 60)
    
    # Step 1: Build database
    out_dir = args.out_dir or DEFAULT_OUTPUT_DIR
    db_path = os.path.join(out_dir, args.db)
    
    stats = build_course_db(
        major_url,
        db_path,
        delay=args.delay,
        timeout=args.timeout,
        retries=args.retries,
        verbose=args.verbose,
        concurrency=args.concurrency,
        reset=reset,
        cache_dir=args.cache_dir,
        out_dir=out_dir,
    )
    
    # Step 2: Ask if user wants to generate visualizations
    print("\n" + "=" * 60)
    print("是否生成课程依赖关系图？")
    print("Generate course dependency visualizations?")
    print("=" * 60)
    print("输入 'yes' 或 'y' 生成图像，输入 'no' 或 'n' 跳过")
    print("Enter 'yes' or 'y' to generate, 'no' or 'n' to skip:")
    
    user_response = input("> ").strip().lower()
    
    if user_response in ['yes', 'y', '是', '好']:
        if args.verbose:
            print("\n" + "=" * 60)
            print("STEP 2/3: Generating visualizations")
            print("=" * 60)
        
        # Generate visualizations (bundle version)
        version_num = 1
        version_dir = os.path.join(out_dir, f"v{version_num:03d}")
        while os.path.exists(version_dir):
            version_num += 1
            version_dir = os.path.join(out_dir, f"v{version_num:03d}")
        os.makedirs(version_dir, exist_ok=True)
        
        # Load profile configs
        config_dir = Path(__file__).parent / "config"
        
        # Dependency graph
        dep_cfg_path = config_dir / "visualize_dependency.toml"
        dep_cfg = _load_config(str(dep_cfg_path)) if dep_cfg_path.exists() else {}
        dep_settings = dep_cfg.get("visualize", {}) if isinstance(dep_cfg, dict) else {}
        
        dep_out = os.path.join(version_dir, f"dependency_v{version_num:03d}.png")
        if args.verbose:
            print(f"\nRendering dependency graph -> {dep_out}")
        
        render_dependency_tree(
            db_path,
            dep_out,
            highlight_cycles=dep_settings.get("highlight_cycles", True),
            focus=dep_settings.get("focus"),
            layered=not dep_settings.get("no_layered", False),
            max_depth=dep_settings.get("max_depth"),
            truncate_title=dep_settings.get("truncate_title", 40),
            color_by_unit=not dep_settings.get("no_unit_colors", False),
            max_per_layer=dep_settings.get("max_per_layer", 16),
            exclude_isolated=dep_settings.get("exclude_isolated", True),
            straight_edges=dep_settings.get("straight_edges", True),
            reduce_transitive=dep_settings.get("reduce_transitive", True),
        )
        
        # Roots graph
        roots_cfg_path = config_dir / "visualize_roots.toml"
        roots_cfg = _load_config(str(roots_cfg_path)) if roots_cfg_path.exists() else {}
        roots_settings = roots_cfg.get("visualize", {}) if isinstance(roots_cfg, dict) else {}
        
        roots_out = os.path.join(version_dir, f"roots_only_v{version_num:03d}.png")
        if args.verbose:
            print(f"Rendering roots graph -> {roots_out}")
        
        render_root_courses(
            db_path,
            roots_out,
            truncate_title=roots_settings.get("truncate_title", 40),
            color_by_unit=roots_settings.get("color_by_unit", True),
            max_per_row=roots_settings.get("max_per_row", 1),
        )
        
        if args.verbose:
            print(f"\n{'=' * 60}")
            print(f"✓ 可视化完成！ / Visualization Complete!")
            print(f"  - Output directory: {version_dir}")
            print(f"  - Dependency graph: {dep_out}")
            print(f"  - Roots graph: {roots_out}")
            print(f"{'=' * 60}")
    else:
        if args.verbose:
            print("\n跳过可视化生成 / Skipping visualization")
    
    # Step 3: Interactive course query
    if args.verbose:
        print("\n" + "=" * 60)
        print("STEP 3/3: Interactive Course Query")
        print("=" * 60)
    
    # Start interactive course query session
    interactive_course_query(db_path, verbose=args.verbose)
    
    if args.verbose:
        print(f"\n{'=' * 60}")
        print(f"✓ 完成！数据库已保存 / Complete! Database saved")
        print(f"  - Database: {db_path}")
        print(f"{'=' * 60}")
    
    return 0


def cmd_visualize(args: argparse.Namespace) -> int:
    """CLI handler for visualize command."""
    # If user provided just a filename (no directory), place in outputs/. Otherwise, use as-is.
    def _abs_out(path: str) -> str:
        if not os.path.isabs(path) and os.path.dirname(path) == "":
            return os.path.join(DEFAULT_OUTPUT_DIR, path)
        return path

    # Late fallback: if db not set yet, try loading from config path or profile-specific config here
    if not getattr(args, "db", None):
        cfg_path = getattr(args, "config", None)
        profile = getattr(args, "profile", None)
        if not cfg_path and profile in {"dependency", "roots"}:
            cfg_path = str(Path(__file__).parent / "config" / f"visualize_{profile}.toml")
        if cfg_path:
            _cfg = _load_config(cfg_path)
            if isinstance(_cfg.get("visualize"), dict):
                vsec = _cfg["visualize"]
                if vsec.get("db"):
                    args.db = vsec["db"]
                # Populate other visualize settings only if not passed on CLI
                for k, v in vsec.items():
                    if k == "db":
                        continue
                    if not hasattr(args, k) or getattr(args, k) in (False, None, 0, ""):
                        setattr(args, k, v)

    # Ensure DB path is provided (typically via config). Avoid proceeding with None.
    if not getattr(args, "db", None):
        print("visualize: missing --db and no [visualize].db in config. Provide a config or --db.", file=sys.stderr)
        return 2

    # Optional pre-visualization check layer: filter DB to allowed courses if provided
    allowed_file = getattr(args, "allowed_courses_file", None)
    if allowed_file:
        allowed = load_allowed_codes(allowed_file)
        if allowed:
            in_place = getattr(args, "check_in_place", True)
            args.db = filter_db_by_allowed(args.db, allowed, in_place=in_place, verbose=getattr(args, "verbose", False))
        elif getattr(args, "verbose", False):
            print(f"[check] allowed_courses_file provided but no codes parsed: {allowed_file}")

    # Bundle mode: create next outputs/vNNN and render both dependency and roots-only images
    if getattr(args, "bundle_version", False):
        if getattr(args, "verbose", False):
            print("[visualize] settings (bundle)")
            print("  db=", args.db)
            print("  roots_only=", getattr(args, "roots_only", False))
            print("  highlight_cycles=", getattr(args, "highlight_cycles", False))
            print("  no_layered=", getattr(args, "no_layered", False))
            print("  max_depth=", getattr(args, "max_depth", None))
            print("  truncate_title=", getattr(args, "truncate_title", None))
            print("  no_unit_colors=", getattr(args, "no_unit_colors", False))
            print("  max_per_layer=", getattr(args, "max_per_layer", None))
            print("  exclude_isolated=", not getattr(args, "include_isolated", False))
            print("  straight_edges=", not getattr(args, "curved_edges", False))
            print("  reduce_transitive=", getattr(args, "reduce_transitive", True))
        base = Path(DEFAULT_OUTPUT_DIR)
        base.mkdir(parents=True, exist_ok=True)
        # find next vNNN
        existing = [p.name for p in base.iterdir() if p.is_dir() and p.name.startswith("v") and p.name[1:].isdigit()]
        nums = [int(p[1:]) for p in existing]
        next_n = (max(nums) + 1) if nums else 1
        vdir = base / f"v{next_n:03d}"
        vdir.mkdir(exist_ok=True)
        dep_path = str(vdir / f"dependency_v{next_n:03d}.png")
        roots_path = str(vdir / f"roots_only_v{next_n:03d}.png")
        if args.verbose:
            print(f"Bundle version dir: {vdir}")
        # dependency graph (config-controlled)
        render_dependency_tree(
            args.db,
            dep_path,
            highlight_cycles=args.highlight_cycles,
            focus=args.focus,
            layered=not getattr(args, "no_layered", False),
            max_depth=getattr(args, "max_depth", None),
            truncate_title=getattr(args, "truncate_title", 40),
            color_by_unit=not getattr(args, "no_unit_colors", False),
            max_per_layer=getattr(args, "max_per_layer", 16),
            exclude_isolated=not getattr(args, "include_isolated", False),
            straight_edges=not getattr(args, "curved_edges", False),
            reduce_transitive=getattr(args, "reduce_transitive", True),
        )
        # roots-only graph: load dedicated config if present (config/visualize_roots.toml)
        root_cfg_path = Path(__file__).parent / "config" / "visualize_roots.toml"
        if root_cfg_path.exists():
            _rcfg = _load_config(str(root_cfg_path))
            vsec = _rcfg.get("visualize", {}) if isinstance(_rcfg, dict) else {}
            r_db = vsec.get("db", args.db)
            r_trunc = vsec.get("truncate_title", getattr(args, "truncate_title", 40))
            r_color = not bool(vsec.get("no_unit_colors", getattr(args, "no_unit_colors", False)))
            r_mpr = vsec.get("max_per_layer", getattr(args, "max_per_layer", 16))
            if args.verbose:
                print("[visualize] roots-only override via visualize_roots.toml:")
                print("  db=", r_db)
                print("  truncate_title=", r_trunc)
                print("  color_by_unit=", r_color)
                print("  max_per_row=", r_mpr)
            render_root_courses(
                r_db,
                roots_path,
                truncate_title=r_trunc,
                color_by_unit=r_color,
                max_per_row=r_mpr,
            )
        else:
            render_root_courses(
                args.db,
                roots_path,
                truncate_title=getattr(args, "truncate_title", 40),
                color_by_unit=not getattr(args, "no_unit_colors", False),
                max_per_row=getattr(args, "max_per_layer", 16),
            )
        if args.verbose:
            print("Graph images written:", dep_path, roots_path)
        return 0

    # Single file mode
    out_path = _abs_out(args.out)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    if getattr(args, "roots_only", False):
        if args.verbose:
            print(f"Rendering roots-only graph from {args.db} -> {out_path}")
        render_root_courses(
            args.db,
            out_path,
            truncate_title=getattr(args, "truncate_title", 40),
            color_by_unit=not getattr(args, "no_unit_colors", False),
            max_per_row=getattr(args, "max_per_layer", 16),
        )
    else:
        if getattr(args, "verbose", False):
            print("[visualize] settings (single)")
            print("  db=", args.db)
            print("  roots_only=", getattr(args, "roots_only", False))
            print("  highlight_cycles=", getattr(args, "highlight_cycles", False))
            print("  no_layered=", getattr(args, "no_layered", False))
            print("  max_depth=", getattr(args, "max_depth", None))
            print("  truncate_title=", getattr(args, "truncate_title", None))
            print("  no_unit_colors=", getattr(args, "no_unit_colors", False))
            print("  max_per_layer=", getattr(args, "max_per_layer", None))
            print("  exclude_isolated=", not getattr(args, "include_isolated", False))
            print("  straight_edges=", not getattr(args, "curved_edges", False))
            print("  reduce_transitive=", getattr(args, "reduce_transitive", True))
        if args.verbose:
            print(f"Rendering graph from {args.db} -> {out_path}")
        render_dependency_tree(
            args.db,
            out_path,
            highlight_cycles=args.highlight_cycles,
            focus=args.focus,
            layered=not getattr(args, "no_layered", False),
            max_depth=getattr(args, "max_depth", None),
            truncate_title=getattr(args, "truncate_title", 40),
            color_by_unit=not getattr(args, "no_unit_colors", False),
            max_per_layer=getattr(args, "max_per_layer", 16),
            exclude_isolated=not getattr(args, "include_isolated", False),
            straight_edges=not getattr(args, "curved_edges", False),
            reduce_transitive=getattr(args, "reduce_transitive", True),
        )
    if args.verbose:
        print("Graph image written:", out_path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="CityU curriculum orchestrator")
    p.add_argument("--config", help="Path to TOML config file (defaults to config/cityu.toml if present)")
    sub = p.add_subparsers(dest="command", required=True)

    # run-all command: complete pipeline
    ra = sub.add_parser("run-all", help="Run complete pipeline: scrape + build DB + visualize")
    ra.add_argument("--major-url", help="Major curriculum URL (can be set in config/scraper.toml)")
    ra.add_argument("--db", default="courses.db", help="SQLite filename inside outputs dir")
    ra.add_argument("--delay", type=float, default=0.2)
    ra.add_argument("--retries", type=int, default=3)
    ra.add_argument("--timeout", type=float, default=15.0)
    ra.add_argument("--verbose", action="store_true")
    ra.add_argument("--concurrency", type=int, default=8, help="Workers to fetch course pages")
    ra.add_argument("--reset", action="store_true", help="Drop existing database tables first")
    ra.add_argument("--out-dir", help="Override output directory")
    ra.add_argument("--cache-dir", help="Directory for HTML cache")
    ra.set_defaults(func=cmd_run_all)

    pm = sub.add_parser("scrape-major", help="Scrape major page(s)")
    g = pm.add_mutually_exclusive_group(required=True)
    g.add_argument("--url", help="Single major URL")
    g.add_argument("--file", help="File with multiple URLs")
    pm.add_argument("--out", required=True, help="Output filename (placed in outputs dir)")
    pm.add_argument("--format", choices=["json", "csv"], default="json")
    pm.add_argument("--courses", action="store_true", help="Also fetch course detail pages")
    pm.add_argument("--delay", type=float, default=0.0)
    pm.add_argument("--retries", type=int, default=3)
    pm.add_argument("--timeout", type=float, default=15.0)
    pm.add_argument("--verbose", action="store_true")
    pm.add_argument("--concurrency", type=int, default=1, help="Number of workers to fetch course pages (when --courses)")
    pm.add_argument("--out-dir", help="Override output directory (default outputs/)")
    pm.add_argument("--cache-dir", help="Directory for HTML cache (default: none)")
    pm.set_defaults(func=cmd_scrape_major)

    db = sub.add_parser("build-db", help="Create SQLite DB of courses for a major")
    db.add_argument("--major-url", help="Major curriculum URL (can be set in config/scraper.toml)")
    db.add_argument("--db", default="courses.db", help="SQLite filename inside outputs dir")
    db.add_argument("--delay", type=float, default=0.2)
    db.add_argument("--retries", type=int, default=3)
    db.add_argument("--timeout", type=float, default=15.0)
    db.add_argument("--verbose", action="store_true")
    db.add_argument("--concurrency", type=int, default=4, help="Workers to fetch course pages")
    db.add_argument("--reset", action="store_true", help="Drop existing tables first")
    db.add_argument("--out-dir", help="Override output directory")
    db.add_argument("--cache-dir", help="Directory for HTML cache")
    db.set_defaults(func=build_db)

    viz = sub.add_parser("visualize", help="Render dependency graph from courses DB")
    # db is no longer required on CLI; can be provided via config file
    viz.add_argument("--db", required=False, help="SQLite database with courses/prerequisites (can be set in config)")
    viz.add_argument("--out", required=False, help="Output image path (PNG). Optional when --bundle-version is used")
    viz.add_argument("--focus", help="Focus on a single course's prerequisite subtree")
    viz.add_argument("--highlight-cycles", action="store_true", help="Highlight cycles in red")
    viz.add_argument("--verbose", action="store_true")
    viz.add_argument("--no-layered", action="store_true", help="Disable layered (top-down) layout")
    viz.add_argument("--max-depth", type=int, help="Limit depth (levels) from roots or focus ancestor chain")
    # defaults are provided by config; leave None here so config can override cleanly
    viz.add_argument("--truncate-title", type=int, help="Truncate course title to this length")
    viz.add_argument("--no-unit-colors", action="store_true", help="Disable coloring nodes by offering unit")
    viz.add_argument("--max-per-layer", type=int, help="Wrap wide layers into multiple rows with at most N nodes per row")
    viz.add_argument("--include-isolated", action="store_true", help="Include courses that have neither prerequisites nor dependents (default: excluded)")
    viz.add_argument("--curved-edges", action="store_true", help="Draw curved edges instead of straight lines (default: straight)")
    viz.add_argument("--roots-only", action="store_true", help="Render only courses without prerequisites (no edges)")
    viz.add_argument("--bundle-version", action="store_true", help="Auto-create next outputs/vNNN and render both dependency and roots-only images")
    # Optional check layer settings (prefer set via config)
    viz.add_argument("--allowed-courses-file", help="Path to a file listing allowed course codes for this major; non-listed courses will be removed before visualize")
    viz.add_argument("--check-in-place", action="store_true", help="Filter DB in-place (default true if set via config)")
    # Optional profile to load preset visualize config files without specifying --config
    viz.add_argument("--profile", choices=["dependency", "roots"], help="Use preset config: dependency or roots (loads config/visualize_<profile>.toml)")
    viz.set_defaults(func=cmd_visualize)

    # Utility: generate a config template
    initc = sub.add_parser("init-config", help="Generate config/cityu.toml template with all settings / 生成包含全部设置的配置模板")
    initc.add_argument("--path", default=str(Path(__file__).parent / "config" / "cityu.toml"), help="Where to write the config TOML")
    initc.add_argument("--force", action="store_true", help="Overwrite if file exists")
    def _cmd_init_config(args: argparse.Namespace) -> int:
        target = Path(args.path)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and not args.force:
            print(f"Config already exists: {target}. Use --force to overwrite.")
            return 0
        # Use current bilingual config (if exists) as template source; fallback to minimal internal snippet
        bilingual_path = Path(__file__).parent / "config" / "cityu.toml"
        if bilingual_path.exists():
            content = bilingual_path.read_text(encoding="utf-8")
        else:
            content = "[common]\nout_dir='outputs'\n"  # minimal fallback
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Config template written -> {target}")
        return 0
    initc.set_defaults(func=_cmd_init_config)

    # Utility: show effective config (merged) for a command without executing it
    sc = sub.add_parser("show-config", help="Print merged config and effective visualize settings (for troubleshooting)")
    sc.add_argument("--profile", choices=["dependency", "roots"], help="Use preset config: dependency or roots (loads config/visualize_<profile>.toml)")
    sc.add_argument("--command", choices=["visualize"], default="visualize", help="Command to inspect (currently only visualize)")
    sc.add_argument("--verbose", action="store_true")
    def _cmd_show_config(args: argparse.Namespace) -> int:
        # Resolve config path priority: explicit --config -> profile file -> default cityu.toml
        cfg_path_override = getattr(args, "config", None)
        if not cfg_path_override and getattr(args, "profile", None) in {"dependency", "roots"}:
            cfg_path_override = str(Path(__file__).parent / "config" / f"visualize_{args.profile}.toml")
        if not cfg_path_override:
            default_path = Path(__file__).parent / "config" / "cityu.toml"
            cfg_path_override = str(default_path) if default_path.exists() else None
        cfg = _load_config(cfg_path_override)
        print(json.dumps({
            "config_path": cfg_path_override,
            "sections": list(cfg.keys()) if isinstance(cfg, dict) else [],
            "common": cfg.get("common", {}) if isinstance(cfg, dict) else {},
            "visualize": cfg.get("visualize", {}) if isinstance(cfg, dict) else {},
        }, ensure_ascii=False, indent=2))
        return 0
    sc.set_defaults(func=_cmd_show_config)

    return p


def main(argv: List[str]) -> int:
    parser = build_parser()
    # First pass: parse known args to discover --config and subcommand without enforcing required
    pre_args, _ = parser.parse_known_args(argv)

    # Load config and set as defaults (common + subcommand-specific). CLI still overrides.
    # Support visualize profiles that map to preset config files when --config isn't provided.
    cfg_path_override = getattr(pre_args, "config", None)
    if not cfg_path_override and getattr(pre_args, "command", None) == "visualize":
        profile = getattr(pre_args, "profile", None)
        if profile in {"dependency", "roots"}:
            base_dir = Path(__file__).parent / "config"
            cfg_path_override = str(base_dir / f"visualize_{profile}.toml")
    cfg = _load_config(cfg_path_override)
    if cfg:
        defaults: dict = {}
        if isinstance(cfg.get("common"), dict):
            defaults.update(cfg["common"])
        cmd = getattr(pre_args, "command", None)
        if cmd:
            sect = cmd.replace("-", "_")
            if isinstance(cfg.get(sect), dict):
                defaults.update(cfg[sect])
        if defaults:
            parser.set_defaults(**defaults)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
