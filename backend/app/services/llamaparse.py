import os
from llama_parse import LlamaParse
from ..config import settings



class LlamaParseService:
    def __init__(self):
        self.api_key = settings.LLAMA_CLOUD_API_KEY
        if not self.api_key or self.api_key == "llx-...":
            raise ValueError("LLAMA_CLOUD_API_KEY is not set")

        # MAXIMUM ACCURACY CONFIGURATION
        # Optimized for academic documents (research papers, course materials)
        self.parser = LlamaParse(
            api_key=self.api_key,
            result_type="markdown",

            # MAXIMUM ACCURACY MODE - Enhanced for charts and data extraction
            parsing_instruction="""
            This is an academic document for a micro-course. CRITICAL: Extract ALL data.

            1. STRUCTURE: Clearly distinguish and mark:
               - Main titles (chapters)
               - Subtitles (sections/subsections)
               - Paragraph text
               - Author fields and metadata
               - Text boxes and callouts

            2. TABLES: 
               - Preserve exact table structure with proper alignment
               - Extract ALL cell values, including numbers
               - Never leave table cells empty if data is visible

            3. CHARTS AND GRAPHS (CRITICAL):
               - This document contains bar charts, line graphs, and statistical visualizations
               - You MUST extract the actual numerical data values from charts
               - Read axis labels and extract all data points with their values
               - Convert chart visuals to structured data tables
               - Example: A bar chart showing "Rural: 65%, Urban: 85%" should output:
                 | Category | Value |
                 |----------|-------|
                 | Rural    | 65%   |
                 | Urban    | 85%   |
               - For time series charts, include all years/periods as rows
               - Never output empty tables - if you see a chart, extract its data

            4. DATA VALUES:
               - Extract ALL numerical values visible in any graphic
               - Include units (%, millions, etc.)
               - For legends, list all categories with their values

            5. RELATIONSHIPS: Maintain clear hierarchy and relationships between components

            6. FORMATTING: Preserve emphasis (bold, italic), lists, and numbering
            """,

            parse_mode="parse_document_with_agent",
            # Use premium parsing (highest accuracy, slower)
            premium_mode=True,

            # Never use cache (always fresh parse for accuracy)
            invalidate_cache=True,

            # Don't skip any content
            skip_diagonal_text=False,

            # Parse embedded objects (images, tables) using best vision model
            vendor_multimodal_model_name="openai-gpt4o",

            # Verbose output for debugging
            verbose=True,
        )

    def parse_pdf(self, file_path: str) -> list:
        """
        Parse a document using LlamaParse with maximum accuracy settings.
        Returns list of Document objects (one per page) with structured markdown.

        Images will be referenced in markdown, tables will be preserved,
        and hierarchical structure will be clearly marked.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Parse the document with premium accuracy
        documents = self.parser.load_data(file_path)

        return documents
