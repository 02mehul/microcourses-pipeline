"""
Chart Extractor Service using Gemini Vision.

Extracts embedded images from DOCX files, identifies charts/graphs,
and uses Gemini Vision to extract numerical data from them.
"""

import io
import re
import base64
import logging
import zipfile
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import os

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


@dataclass
class ChartImage:
    """Represents an extracted chart image from a DOCX file."""
    filename: str
    image_bytes: bytes
    size_bytes: int
    figure_number: Optional[int] = None


class ChartExtractor:
    """
    Extracts chart data from DOCX files using Gemini Vision.
    
    Process:
    1. Extract embedded images from DOCX (it's a ZIP file)
    2. Filter for chart-sized images (typically > 5KB, charts are not tiny icons)
    3. Use Gemini Vision to analyze each chart and extract data
    4. Return structured data for each chart
    """
    
    # Minimum size to consider an image as a potential chart (5KB)
    MIN_CHART_SIZE_BYTES = 5000
    
    # Maximum images to process (to avoid API overuse)
    MAX_CHARTS_TO_PROCESS = 10
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the chart extractor with Gemini API.
        
        Args:
            api_key: Gemini API key. If not provided, reads from GEMINI_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY must be set in environment or passed to constructor")
        
        self.client = genai.Client(api_key=self.api_key)
        
    def extract_images_from_docx(self, docx_path: str) -> List[ChartImage]:
        """
        Extract all embedded images from a DOCX file.
        
        DOCX files are ZIP archives with images in word/media/ folder.
        
        Args:
            docx_path: Path to the DOCX file
            
        Returns:
            List of ChartImage objects
        """
        images = []
        
        try:
            with zipfile.ZipFile(docx_path, 'r') as docx_zip:
                for item in docx_zip.namelist():
                    # Images are stored in word/media/
                    if item.startswith('word/media/') and not item.endswith('/'):
                        # Check if it's an image file
                        ext = item.lower().split('.')[-1]
                        if ext in ('png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'):
                            image_bytes = docx_zip.read(item)
                            size = len(image_bytes)
                            
                            images.append(ChartImage(
                                filename=item.split('/')[-1],
                                image_bytes=image_bytes,
                                size_bytes=size
                            ))
                            
            logger.info(f"Extracted {len(images)} images from DOCX")
            return images
            
        except zipfile.BadZipFile:
            logger.error(f"Invalid DOCX file: {docx_path}")
            return []
        except Exception as e:
            logger.error(f"Error extracting images from DOCX: {e}", exc_info=True)
            return []
    
    def filter_chart_candidates(self, images: List[ChartImage]) -> List[ChartImage]:
        """
        Filter images that are likely to be charts based on size.
        
        Charts typically:
        - Are larger than icons (> 5KB)
        - Are PNG or JPEG format
        
        Args:
            images: List of all extracted images
            
        Returns:
            Filtered list of potential charts
        """
        candidates = [
            img for img in images 
            if img.size_bytes >= self.MIN_CHART_SIZE_BYTES
        ]
        
        # Sort by size descending (larger images are more likely to be important charts)
        candidates.sort(key=lambda x: x.size_bytes, reverse=True)
        
        # Limit to max charts
        candidates = candidates[:self.MAX_CHARTS_TO_PROCESS]
        
        logger.info(f"Filtered to {len(candidates)} chart candidates from {len(images)} images")
        return candidates
    
    def analyze_chart_with_gemini(self, image: ChartImage, max_retries: int = 3) -> Optional[Dict]:
        """
        Use Gemini Vision to analyze a chart image and extract data.
        
        Args:
            image: ChartImage object with the image bytes
            max_retries: Maximum number of retry attempts for rate limit errors
            
        Returns:
            Dictionary with extracted chart data, or None if not a chart
        """
        import time
        import json
        
        # Determine MIME type
        ext = image.filename.lower().split('.')[-1]
        mime_type = {
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'gif': 'image/gif',
            'bmp': 'image/bmp',
        }.get(ext, 'image/png')
        
        # Create image part for Gemini
        image_part = types.Part.from_bytes(
            data=image.image_bytes,
            mime_type=mime_type
        )
        
        prompt = """Analyze this image. If it's a chart, graph, or data visualization, extract ALL the numerical data.

INSTRUCTIONS:
1. First, determine if this is a chart/graph/visualization or just a regular image/icon/decorative element
2. If it's NOT a chart (e.g., logo, icon, photo, decorative), respond with: {"is_chart": false}
3. If it IS a chart, extract ALL data points visible

For CHARTS, provide:
{
  "is_chart": true,
  "chart_type": "bar|line|scatter|pie|area|other",
  "title": "Chart title if visible",
  "x_axis_label": "X axis label",
  "y_axis_label": "Y axis label", 
  "data_table": {
    "headers": ["Column1", "Column2", ...],
    "rows": [
      ["value1", "value2", ...],
      ["value3", "value4", ...]
    ]
  },
  "key_findings": "Brief description of what the chart shows"
}

IMPORTANT:
- Read numerical values as precisely as possible from the chart
- For line/bar charts, include all data points you can identify
- For scatter plots, list representative data points
- Include units (%, millions, etc.) with values
- If exact values aren't clear, provide best estimates with "~" prefix

Return ONLY valid JSON."""

        # Retry loop with exponential backoff
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model="gemini-3-pro-preview",
                    contents=[prompt, image_part],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.1  # Low temperature for precise extraction
                    )
                )
                
                result = json.loads(response.text)
                
                if result.get("is_chart", False):
                    logger.info(f"✅ Extracted chart data from {image.filename}: {result.get('chart_type')}")
                    return result
                else:
                    logger.debug(f"⏭️ Skipping non-chart image: {image.filename}")
                    return None
                    
            except Exception as e:
                error_str = str(e)
                # Check if it's a rate limit error
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    wait_time = (2 ** attempt) * 5  # 5s, 10s, 20s
                    logger.warning(f"Rate limited on {image.filename}, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    logger.warning(f"Error analyzing image {image.filename}: {e}")
                    return None
        
        logger.warning(f"Max retries exceeded for {image.filename}")
        return None
    
    def find_figure_references(self, markdown: str) -> List[int]:
        """
        Find figure numbers referenced in the markdown text.
        
        Args:
            markdown: The parsed markdown content
            
        Returns:
            List of figure numbers found (e.g., [1, 2, 3])
        """
        # Match patterns like "Figure 1", "Figure 2:", "(Figure 3)"
        pattern = r'(?:Figure|Fig\.?)\s*(\d+)'
        matches = re.findall(pattern, markdown, re.IGNORECASE)
        figure_numbers = sorted(set(int(m) for m in matches))
        logger.info(f"Found figure references: {figure_numbers}")
        return figure_numbers
    
    def convert_chart_to_markdown_table(self, chart_data: Dict) -> str:
        """
        Convert extracted chart data to a markdown table.
        
        Args:
            chart_data: Dictionary with chart information
            
        Returns:
            Markdown formatted table string
        """
        if not chart_data or not chart_data.get("data_table"):
            return ""
        
        table = chart_data["data_table"]
        headers = table.get("headers", [])
        rows = table.get("rows", [])
        
        if not headers or not rows:
            return ""
        
        # Build markdown table
        lines = []
        
        # Add title if present
        if chart_data.get("title"):
            lines.append(f"**{chart_data['title']}**\n")
        
        # Header row
        lines.append("| " + " | ".join(str(h) for h in headers) + " |")
        
        # Separator row
        lines.append("| " + " | ".join("---" for _ in headers) + " |")
        
        # Data rows
        for row in rows:
            # Pad row to match header length
            padded_row = list(row) + [""] * (len(headers) - len(row))
            lines.append("| " + " | ".join(str(v) for v in padded_row[:len(headers)]) + " |")
        
        # Add key findings if present
        if chart_data.get("key_findings"):
            lines.append(f"\n*{chart_data['key_findings']}*")
        
        return "\n".join(lines)
    
    def enhance_markdown_with_chart_data(
        self, 
        markdown: str, 
        charts: List[Tuple[ChartImage, Dict]]
    ) -> str:
        """
        Enhance the parsed markdown by replacing empty tables with extracted chart data.
        
        Strategy:
        1. Find empty tables in the markdown (tables with mostly empty cells)
        2. Find figure references near those tables
        3. Replace empty tables with extracted chart data
        
        Args:
            markdown: Original parsed markdown
            charts: List of (ChartImage, extracted_data) tuples
            
        Returns:
            Enhanced markdown with chart data filled in
        """
        if not charts:
            return markdown
        
        # Pattern to find markdown tables with empty cells
        # This matches tables where data rows have mostly empty cells
        empty_table_pattern = r'(\|[^|\n]+\|[^\n]*\n\|[-:\s|]+\|\n(?:\|[|\s]*\|[\s]*\n)+)'
        
        enhanced = markdown
        chart_tables = [self.convert_chart_to_markdown_table(data) for _, data in charts if data]
        chart_tables = [t for t in chart_tables if t]  # Filter empty
        
        if not chart_tables:
            return markdown
        
        # Find figure references and try to match charts to them
        figure_refs = self.find_figure_references(markdown)
        
        # For each empty table section, try to enhance it
        def replace_empty_table(match):
            table_text = match.group(0)
            # Check if this table has mostly empty cells
            cells = re.findall(r'\|([^|]*)\|', table_text)
            empty_count = sum(1 for c in cells if c.strip() == '')
            total_count = len(cells)
            
            if total_count > 0 and empty_count / total_count > 0.5:
                # This table is mostly empty, try to replace with chart data
                if chart_tables:
                    replacement = chart_tables.pop(0)
                    logger.info("Replaced empty table with extracted chart data")
                    return replacement + "\n"
            
            return table_text
        
        enhanced = re.sub(empty_table_pattern, replace_empty_table, enhanced)
        
        # If we still have chart data, append it at the end of relevant sections
        if chart_tables:
            logger.info(f"Appending {len(chart_tables)} remaining chart tables")
            enhanced += "\n\n## Extracted Chart Data\n\n"
            enhanced += "\n\n".join(chart_tables)
        
        return enhanced
    
    def process_docx(self, docx_path: str, markdown: str) -> str:
        """
        Main entry point: Process a DOCX file and enhance its parsed markdown with chart data.
        
        Args:
            docx_path: Path to the DOCX file
            markdown: Already parsed markdown content (from LlamaParse)
            
        Returns:
            Enhanced markdown with chart data extracted and filled in
        """
        logger.info(f"🔍 Starting chart extraction for: {docx_path}")
        
        # Step 1: Extract images from DOCX
        all_images = self.extract_images_from_docx(docx_path)
        if not all_images:
            logger.info("No images found in DOCX, returning original markdown")
            return markdown
        
        # Step 2: Filter for chart candidates
        chart_candidates = self.filter_chart_candidates(all_images)
        if not chart_candidates:
            logger.info("No chart candidates found, returning original markdown")
            return markdown
        
        # Step 3: Analyze each chart with Gemini Vision
        extracted_charts = []
        for image in chart_candidates:
            logger.info(f"📊 Analyzing image: {image.filename} ({image.size_bytes} bytes)")
            chart_data = self.analyze_chart_with_gemini(image)
            if chart_data:
                extracted_charts.append((image, chart_data))
        
        logger.info(f"Successfully extracted data from {len(extracted_charts)} charts")
        
        # Step 4: Enhance markdown with extracted chart data
        if extracted_charts:
            enhanced_markdown = self.enhance_markdown_with_chart_data(markdown, extracted_charts)
            logger.info("✅ Markdown enhanced with chart data")
            return enhanced_markdown
        
        return markdown
