import os
from llama_parse import LlamaParse
from ..config import settings



class LlamaParseService:
    def __init__(self):
        self.api_key = settings.LLAMA_CLOUD_API_KEY
        if not self.api_key or self.api_key == "llx-...":
            raise ValueError("LLAMA_CLOUD_API_KEY is not set")

        # Get OpenAI API key for multimodal parsing (chart extraction)
        self.openai_api_key = settings.OPENAI_API_KEY

        # GPT-4o VISION MODE - Best for chart/graph data extraction
        # Uses OpenAI's GPT-4o for superior visual understanding of charts
        self.parser = LlamaParse(
            api_key=self.api_key,
            result_type="markdown",
            
            # Use document-level LVM for better cross-page context
            parse_mode="parse_document_with_lvm",
            
            # CRITICAL: Use GPT-4o for multimodal parsing (best for charts)
            use_vendor_multimodal_model=True,
            vendor_multimodal_model_name="openai-gpt-5",
            vendor_multimodal_api_key=self.openai_api_key,
            
            # Enable chart extraction
            extract_charts=True,
            
            # Enable layout/figure extraction
            extract_layout=True,
            
            # Enhanced extraction features
            high_res_ocr=True,  # High resolution OCR
            adaptive_long_table=True,  # Detect and adapt long tables
            outlined_table_extraction=True,  # Extract outlined tables
            output_tables_as_HTML=True,  # Output tables as HTML in markdown
            
            # Layout preservation for accurate structure
            preserve_layout_alignment_across_pages=True,
            preserve_very_small_text=True,  # Capture small text in charts/legends
            
            # Cross-page context preservation
            continuous_mode=True,
            
            # Premium accuracy mode
            premium_mode=True,
            
            # Parsing instructions for GPT-4o Vision
            parsing_instruction="""
            You are analyzing an academic research document with charts and graphs.
            
            CRITICAL REQUIREMENTS:
            
            1. CHARTS & GRAPHS - Extract ALL numerical data:
               - Read bar chart values from the y-axis
               - Read line graph data points for each year/period
               - Extract scatter plot coordinates
               - Convert ALL visual data into structured markdown tables
               - Example: Bar chart with "Sweden: 0.92, Germany: 0.85" becomes:
                 | Country | Equality Index |
                 |---------|----------------|
                 | Sweden  | 0.92           |
                 | Germany | 0.85           |
            
            2. TABLES - Fill ALL cells:
               - Never leave table cells empty if data is visible
               - Extract exact numeric values
            
            3. STRUCTURE: Preserve document hierarchy
            
            4. ACCURACY: Double-check all extracted numbers against the visual
            """,

            # Fresh parse
            invalidate_cache=True,
            skip_diagonal_text=False,
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
