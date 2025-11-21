#!/usr/bin/env python3
import os
import json
import subprocess
from pathlib import Path

REPORT = "efc_master_validation_report.txt"


def section(title):
    return f"\n=== {title} ===\n"


def run_cmd(cmd):
    try:
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True)
        return True, out
    except subprocess.CalledProcessError as e:
        return False, e.output


def write_report(text):
    with open(REPORT, "a", encoding="utf-8") as f:
        f.write(text + "\n")


# ----------------------------------------------------------
# VALIDATION MODULES
# ----------------------------------------------------------

def validate_schema_paths():
    write_report(section("SCHEMA PATH VALIDATION"))
    ok, out = run_cmd("python tools/check_schema_paths.py")
    write_report(out)
    return ok


def validate_efc_repo():
    write_report(section("FULL EFC REPO VALIDATION"))
    ok, out = run_cmd("python tools/check_repo_structure.py")
    write_report(out)
    return ok


def validate_papers():
    write_report(section("PAPER VALIDATION"))
    ok, out = run_cmd("python tools/validate_papers.py")
    write_report(out)
    return ok


def semantic_extractor():
    write_report(section("SEMANTIC EXTRACTOR"))
    ok, out = run_cmd("python tools/semantic_extract.py")
    write_report(out)
    return ok


def jsonld_validator():
    write_report(section("JSON-LD VALIDATION"))
    root = Path(".")
    for path in root.rglob("*.jsonld"):
        try:
            json.load(open(path, "r", encoding="utf-8"))
            write_report(f"[OK] {path}")
        except Exception as e:
            write_report(f"[FAIL] {path}: {e}")
    return True


def figshare_check():
    write_report(section("FIGSHARE DOI CONSISTENCY"))
    doi_map = Path("figshare/doi-map.json")
    if not doi_map.exists():
        write_report("No doi-map.json found.")
        return True

    try:
        data = json.load(open(doi_map, "r", encoding="utf-8"))
        for doi, entry in data.items():
            write_report(f"[OK] {doi}: mapped to article {entry['article_id']}")
    except Exception as e:
        write_report(f"[FAIL] Error parsing doi-map.json: {e}")

    return True


def rag_validator():
    write_report(section("RAG PROFILE VALIDATION"))
    rag = Path("rag-profile.json")
    if not rag.exists():
        write_report("No rag-profile.json found.")
        return True

    try:
        json.load(open(rag, "r", encoding="utf-8"))
        write_report("[OK] rag-profile.json")
    except Exception as e:
        write_report(f"[FAIL] rag-profile.json: {e}")
    return True


def hygiene_scan():
    write_report(section("DIRECTORY HYGIENE"))
    ignored = {"__pycache__", ".git", ".github"}
    for root, dirs, files in os.walk("."):
        if any(x in root for x in ignored):
            continue
        for f in files:
            if f.endswith("tmp") or f.endswith("~"):
                write_report(f"[WARN] orphan temp file: {os.path.join(root, f)}")
    return True


# ----------------------------------------------------------
# MASTER CONTROLLER
# ----------------------------------------------------------

def main():
    if os.path.exists(REPORT):
        os.remove(REPORT)

    write_report("EFC MASTER VALIDATION SUITE REPORT\n")

    validate_schema_paths()
    validate_efc_repo()
    validate_papers()
    semantic_extractor()
    jsonld_validator()
    figshare_check()
    rag_validator()
    hygiene_scan()

    write_report("\n=== END OF REPORT ===\n")


if __name__ == "__main__":
    main()
