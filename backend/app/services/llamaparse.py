import os
from llama_parse import LlamaParse
from ..config import settings


class LlamaParseService:
    def __init__(self):
        self.api_key = settings.LLAMA_CLOUD_API_KEY
        if not self.api_key or self.api_key == "llx-...":
            raise ValueError("LLAMA_CLOUD_API_KEY is not set")

        self.parser = LlamaParse(
            api_key=self.api_key,
            result_type="markdown",
            parse_mode="parse_document_with_lvm",
            use_vendor_multimodal_model=True,
            extract_charts=True,
            extract_layout=True,
            high_res_ocr=True,
            adaptive_long_table=True,
            outlined_table_extraction=True,
            output_tables_as_HTML=True,
            preserve_layout_alignment_across_pages=True,
            preserve_very_small_text=True,
            continuous_mode=True,
            premium_mode=True,
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
            invalidate_cache=True,
            skip_diagonal_text=False,
            verbose=True,
        )

    def parse_pdf(self, file_path: str) -> list:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        documents = self.parser.load_data(file_path)

        return documents
