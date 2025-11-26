import os
import nest_asyncio
from llama_parse import LlamaParse
from ..config import settings

# Apply nest_asyncio to allow nested event loops (needed for LlamaParse in some envs)
# nest_asyncio.apply() # Removed to fix uvloop conflict

class LlamaParseService:
    def __init__(self):
        self.api_key = settings.LLAMA_CLOUD_API_KEY
        if not self.api_key or self.api_key == "llx-...":
            raise ValueError("LLAMA_CLOUD_API_KEY is not set")

        self.parser = LlamaParse(
            api_key=self.api_key,
            parse_mode="parse_page_with_agent",
            result_type="markdown",
            high_res_ocr=True,
            adaptive_long_table=True,
            output_tables_as_HTML=True,  # Keep HTML tables for better structure in MD
            extract_charts=True,
            auto_mode=True,
            auto_mode_trigger_on_image_in_page=True,
            auto_mode_trigger_on_table_in_page=True,
        )

    async def parse_pdf(self, file_path: str) -> list:
        """
        Parse a PDF file using LlamaParse and return the list of Document objects (one per page).
        Images will be referenced in the Markdown output.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Parse the document - aload_data returns Document objects with images embedded in markdown
        documents = await self.parser.aload_data(file_path)
        
        # Note: With output_tables_as_HTML=True and image extraction enabled,
        # images will appear as ![alt](url) in the markdown
        # and tables will be HTML in the markdown text
        
        return documents
