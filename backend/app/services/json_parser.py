from typing import List, Dict, Any, Optional

class JsonParser:
    def __init__(self):
        self.hierarchy_stack = []

    def parse(self, json_data: List[Dict[str, Any]], page_num: int) -> List[Dict[str, Any]]:
        """
        Parse LlamaParse JSON output for a specific page.
        Input is expected to be a list of items (dictionaries) from the JSON result.
        """
        blocks = []
        
        for item in json_data:
            block = self._process_item(item)
            if block:
                blocks.append(block)
                
        return blocks

    def _process_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert a LlamaParse JSON item to our Block schema format."""
        item_type = item.get("type")
        content = item.get("value", "")
        md_content = item.get("md", "")
        
        # Default bbox (LlamaParse JSON might provide it, but let's default for now)
        # If LlamaParse provides 'bBox', we can use it.
        # Example: "bBox": {"x": 10, "y": 10, "w": 100, "h": 20} -> convert to x0, y0, x1, y1
        bbox = {"x0": 0, "y0": 0, "x1": 0, "y1": 0}
        
        if item_type == "heading":
            # LlamaParse JSON usually gives "lvl" for heading level
            level = item.get("lvl", 1)
            
            role = "paragraph"
            hierarchy_level = None
            
            if level == 1:
                role = "title"
                hierarchy_level = 0
            elif level == 2:
                role = "chapter_heading"
                hierarchy_level = 1
            elif level >= 3:
                role = "section_heading"
                hierarchy_level = level - 1
            
            return {
                "type": "text",
                "semantic_role": role,
                "hierarchy_level": hierarchy_level,
                "text_raw": content, # Use plain text value
                "bbox": bbox
            }

        elif item_type == "text":
            return {
                "type": "text",
                "semantic_role": "paragraph",
                "text_raw": content,
                "bbox": bbox
            }

        elif item_type == "list":
            # LlamaParse JSON might return list items individually or as a block
            # If it's a block, content might be the full list text
            return {
                "type": "text",
                "semantic_role": "list",
                "text_raw": content,
                "bbox": bbox
            }
            
        elif item_type == "table":
            # Handle Table
            # LlamaParse JSON for table usually contains 'rows' or 'csv' or 'md'
            # We need to extract structured data if available, or parse the MD/HTML
            
            # If 'rows' is present, use it
            rows = item.get("rows", [])
            headers = [] # LlamaParse JSON might not explicitly separate headers in 'rows' list
            
            # If we requested output_tables_as_HTML=True, the 'md' field might contain HTML
            # But here we are in JSON mode.
            # Let's check if 'md' contains HTML table
            
            text_raw = md_content # Use the MD/HTML representation for text_raw
            
            # Construct table_data
            # If we have structured rows, use them
            table_data = {}
            if rows:
                # rows is usually List[List[str]] or List[List[Dict]]
                # Let's assume simple structure for now, or refine based on debug output
                # For now, let's try to parse 'md' if it looks like HTML, using our existing logic?
                # Or just store what we have.
                
                # Let's try to use the 'md' content if it's HTML, as we did for the fix
                if "<table" in md_content:
                     # We can reuse the HTML parsing logic if we move it to a utility or duplicate it
                     # For now, let's just store the raw text and empty table_data if we can't easily parse it without the parser instance
                     pass
            
            return {
                "type": "table",
                "semantic_role": "table",
                "text_raw": text_raw,
                "table_data": {"rows": rows}, # Store raw rows for now
                "bbox": bbox
            }
        
        # Handle other types...
        
        return None
