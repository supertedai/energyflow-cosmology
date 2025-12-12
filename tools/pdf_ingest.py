#!/usr/bin/env python3
"""
PDF Ingest - Extract text from PDFs and ingest to EFC system
============================================================

Uses PyPDF2 to extract text from PDF files.
Install: pip install PyPDF2

Usage:
    python tools/pdf_ingest.py --pdf path/to/file.pdf
    python tools/pdf_ingest.py --batch  # Process all PDFs from scan
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("⚠️  PyPDF2 not installed. Install with: pip install PyPDF2")

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF file."""
    if not PDF_AVAILABLE:
        raise ImportError("PyPDF2 not installed")
    
    text_parts = []
    
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            if text.strip():
                text_parts.append(f"--- Page {page_num + 1} ---\n{text}")
    
    return "\n\n".join(text_parts)


def ingest_pdf(pdf_path: str):
    """Ingest a single PDF file."""
    from orchestrator_v2 import orchestrate
    
    print(f"📄 Processing PDF: {pdf_path}")
    
    # Extract text
    try:
        text = extract_text_from_pdf(pdf_path)
        print(f"   Extracted {len(text)} characters")
    except Exception as e:
        print(f"   ❌ Failed to extract text: {e}")
        return False
    
    # Ingest via orchestrator
    try:
        result = orchestrate(
            text=text,
            source=pdf_path,
            input_type="document"
        )
        print(f"   ✅ Ingested: {result['document_id']}")
        return True
    except Exception as e:
        print(f"   ❌ Failed to ingest: {e}")
        return False


def batch_ingest_pdfs():
    """Ingest all PDFs that failed in original scan."""
    import json
    
    # Get failed PDFs from gold_ingest.log
    failed_pdfs = []
    
    if Path("gold_ingest.log").exists():
        with open("gold_ingest.log", "r") as f:
            for line in f:
                if "❌ Error:" in line and ".pdf" in line:
                    # Extract filename
                    pdf_path = line.split("❌ Error:")[1].strip()
                    if Path(pdf_path).exists():
                        failed_pdfs.append(pdf_path)
    
    if not failed_pdfs:
        print("No failed PDFs found to process")
        return
    
    print(f"🚀 Batch processing {len(failed_pdfs)} PDFs...")
    print("="*60)
    
    success_count = 0
    error_count = 0
    
    for idx, pdf_path in enumerate(failed_pdfs, 1):
        print(f"\n[{idx}/{len(failed_pdfs)}] {pdf_path}")
        if ingest_pdf(pdf_path):
            success_count += 1
        else:
            error_count += 1
    
    print("\n" + "="*60)
    print(f"📊 PDF Ingest Complete:")
    print(f"   ✅ Success: {success_count}")
    print(f"   ❌ Errors:  {error_count}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest PDFs to EFC system")
    parser.add_argument("--pdf", help="Path to single PDF file")
    parser.add_argument("--batch", action="store_true", help="Process all failed PDFs from log")
    parser.add_argument("--install", action="store_true", help="Install PyPDF2")
    
    args = parser.parse_args()
    
    if args.install:
        print("Installing PyPDF2...")
        os.system("pip install PyPDF2")
        print("✅ PyPDF2 installed")
        sys.exit(0)
    
    if not PDF_AVAILABLE:
        print("❌ PyPDF2 not installed")
        print("   Run: python tools/pdf_ingest.py --install")
        sys.exit(1)
    
    if args.pdf:
        if not Path(args.pdf).exists():
            print(f"❌ File not found: {args.pdf}")
            sys.exit(1)
        ingest_pdf(args.pdf)
    
    elif args.batch:
        batch_ingest_pdfs()
    
    else:
        parser.print_help()
