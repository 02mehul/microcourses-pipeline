#!/usr/bin/env python3
"""
Test script for Chart Extractor.

This script tests the chart extraction functionality on a sample DOCX file
and outputs the enhanced markdown.

Usage:
    cd backend
    python scripts/test_chart_extractor.py
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.chart_extractor import ChartExtractor


def main():
    # Path to test document
    docx_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "docs",
        "dwr-25-45-1.docx"
    )
    
    if not os.path.exists(docx_path):
        print(f"❌ Test document not found: {docx_path}")
        sys.exit(1)
    
    print(f"📄 Testing with document: {docx_path}")
    print("=" * 60)
    
    # Initialize chart extractor
    try:
        extractor = ChartExtractor()
        print("✅ ChartExtractor initialized successfully")
    except ValueError as e:
        print(f"❌ Failed to initialize ChartExtractor: {e}")
        print("   Make sure GEMINI_API_KEY is set in environment")
        sys.exit(1)
    
    # Step 1: Extract images from DOCX
    print("\n📦 Step 1: Extracting images from DOCX...")
    images = extractor.extract_images_from_docx(docx_path)
    print(f"   Found {len(images)} images")
    for img in images:
        print(f"   - {img.filename}: {img.size_bytes:,} bytes")
    
    # Step 2: Filter chart candidates
    print("\n🔍 Step 2: Filtering chart candidates...")
    candidates = extractor.filter_chart_candidates(images)
    print(f"   Filtered to {len(candidates)} chart candidates")
    for img in candidates:
        print(f"   - {img.filename}: {img.size_bytes:,} bytes")
    
    # Step 3: Analyze charts with Gemini Vision
    print("\n🤖 Step 3: Analyzing charts with Gemini Vision...")
    extracted_charts = []
    for img in candidates[:5]:  # Limit to 5 for testing
        print(f"\n   Analyzing: {img.filename}...")
        chart_data = extractor.analyze_chart_with_gemini(img)
        if chart_data:
            print(f"   ✅ Extracted: {chart_data.get('chart_type', 'unknown')} chart")
            print(f"      Title: {chart_data.get('title', 'N/A')}")
            if chart_data.get('data_table'):
                headers = chart_data['data_table'].get('headers', [])
                rows = chart_data['data_table'].get('rows', [])
                print(f"      Data: {len(headers)} columns, {len(rows)} rows")
            extracted_charts.append((img, chart_data))
        else:
            print(f"   ⏭️ Not a chart (skipped)")
    
    # Step 4: Convert to markdown tables
    print("\n📝 Step 4: Converting to markdown tables...")
    markdown_tables = []
    for img, data in extracted_charts:
        table_md = extractor.convert_chart_to_markdown_table(data)
        if table_md:
            markdown_tables.append(table_md)
            print(f"\n   From {img.filename}:")
            print("   " + table_md.replace("\n", "\n   "))
    
    # Step 5: Save output
    output_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "docs"
    )
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, "chart_extraction_test_output.md")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Chart Extraction Test Output\n\n")
        f.write(f"Source: `{os.path.basename(docx_path)}`\n\n")
        f.write(f"Extracted {len(extracted_charts)} charts from {len(images)} total images.\n\n")
        
        for i, (img, data) in enumerate(extracted_charts, 1):
            f.write(f"## Chart {i}: {img.filename}\n\n")
            f.write(f"**Type:** {data.get('chart_type', 'unknown')}\n\n")
            if data.get('title'):
                f.write(f"**Title:** {data.get('title')}\n\n")
            if data.get('key_findings'):
                f.write(f"**Key Findings:** {data.get('key_findings')}\n\n")
            
            table_md = extractor.convert_chart_to_markdown_table(data)
            if table_md:
                f.write("### Extracted Data\n\n")
                f.write(table_md + "\n\n")
            
            f.write("---\n\n")
    
    print(f"\n💾 Output saved to: {output_path}")
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print(f"   Extracted data from {len(extracted_charts)} charts")


if __name__ == "__main__":
    main()
