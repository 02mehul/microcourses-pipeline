
import mistune
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

class MarkdownParser:
    def __init__(self):
        self.markdown = mistune.create_markdown(renderer=None, plugins=['table'])


    def parse(self, markdown_text: str, page_num: int) -> List[Dict[str, Any]]:
        """
        Parse Markdown text for a specific page.
        """
        # Mistune returns an AST (Abstract Syntax Tree)
        ast = self.markdown(markdown_text)
        
        blocks = [] 

        for node in ast:
            block = self._process_node(node)
            if not block:
                continue
            blocks.append(block)

        return blocks

    def _process_node(self, node: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert a Mistune AST node to our Block schema format."""
        node_type = node["type"]
        
        if node_type == "heading":
            level = node["attrs"]["level"]
            text = self._get_text_content(node)
            
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
                "text_raw": text,
                "bbox": {"x0": 0, "y0": 0, "x1": 0, "y1": 0} # Placeholder, LlamaParse MD doesn't give bbox per line easily
            }

        elif node_type == "paragraph":
            text = self._get_text_content(node)
            # Check for images in paragraph
            if "![" in text and "](" in text: 
                # Basic check, mistune might have nested image node
                # For now, treat as text, we might need deeper inspection for images
                pass
            
            return {
                "type": "text",
                "semantic_role": "paragraph",
                "text_raw": text,
                "bbox": {"x0": 0, "y0": 0, "x1": 0, "y1": 0}
            }

        elif node_type == "list":
            # We could flatten lists or keep them as a block
            # For now, let's extract all items as individual list_item blocks
            # But here we return None and handle children? 
            # Mistune AST is nested. 
            # If we want to flatten, we need to return a list of blocks.
            # Current structure assumes 1-to-1. 
            # Let's just grab the text of the whole list for now to keep it simple.
            text = self._get_text_content(node)
            return {
                "type": "text",
                "semantic_role": "list",
                "text_raw": text,
                "bbox": {"x0": 0, "y0": 0, "x1": 0, "y1": 0}
            }
            
        elif node_type == "table":
            # Handle Markdown table
            table_data = self._parse_markdown_table(node)
            text_raw = self._reconstruct_markdown_table(table_data)
            return {
                "type": "table",
                "semantic_role": "table",
                "text_raw": text_raw,
                "table_data": table_data,
                "bbox": {"x0": 0, "y0": 0, "x1": 0, "y1": 0}
            }
        
        elif node_type == "image":
            # Handle image nodes
            # As per requirements, we are ignoring images for now
            return None
        
        elif node_type == "block_html":
            # Handle HTML blocks (for HTML tables when output_tables_as_HTML=True)
            html_content = node.get("raw", "")
            if "<table" in html_content:
                # Parse HTML table
                table_data = self._parse_html_table(html_content)
                # For HTML tables, we want to preserve the raw HTML to keep colspan/rowspan
                text_raw = html_content 
                return {
                    "type": "table",
                    "semantic_role": "table",
                    "text_raw": text_raw,
                    "table_data": table_data,
                    "bbox": {"x0": 0, "y0": 0, "x1": 0, "y1": 0}
                }

        return None

    def _get_text_content(self, node: Dict[str, Any]) -> str:
        """Recursively extract text from node children."""
        # Mistune 3 uses 'raw' for text content
        if "raw" in node:
            return node["raw"]
        if "text" in node:
            return node["text"]
        if "children" in node:
            return "".join([self._get_text_content(child) for child in node["children"]])
        return ""
    
    def _parse_html_table(self, html_str: str) -> Dict[str, Any]:
        """Parse HTML table into structured JSON."""
        try:
            soup = BeautifulSoup(html_str, "html.parser")
            table = soup.find("table")
            
            if not table:
                return {}
            
            # Extract headers
            headers = []
            thead = table.find("thead")
            if thead:
                header_row = thead.find("tr")
                if header_row:
                    headers = [th.get_text(strip=True) for th in header_row.find_all(["th", "td"])]
            
            # Extract rows
            rows = []
            tbody = table.find("tbody") or table
            for tr in tbody.find_all("tr"):
                # Skip header rows in tbody
                if tr.parent.name == "thead":
                    continue
                    
                cells = []
                for cell in tr.find_all(["td", "th"]):
                    cells.append({
                        "text": cell.get_text(strip=True),
                        "colspan": int(cell.get("colspan", 1)),
                        "rowspan": int(cell.get("rowspan", 1)),
                    })
                rows.append(cells)
            
            return {
                "headers": headers,
                "rows": rows,
                "num_columns": len(headers) if headers else (len(rows[0]) if rows else 0),
                "num_rows": len(rows),
            }
        except Exception as e:
            return {"error": str(e)}

    def _parse_markdown_table(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Mistune Markdown table AST into structured JSON."""
        headers = []
        rows = []
        
        children = node.get("children", [])
        for child in children:
            if child["type"] == "table_head":
                for row in child.get("children", []):
                    for cell in row.get("children", []):
                        headers.append(self._get_text_content(cell))
            elif child["type"] == "table_body":
                for row in child.get("children", []):
                    current_row = []
                    for cell in row.get("children", []):
                        current_row.append({
                            "text": self._get_text_content(cell),
                            "colspan": 1, # Markdown tables don't support colspan/rowspan standardly
                            "rowspan": 1
                        })
                    rows.append(current_row)
                    
        return {
            "headers": headers,
            "rows": rows,
            "num_columns": len(headers) if headers else (len(rows[0]) if rows else 0),
            "num_rows": len(rows),
        }

    def _reconstruct_markdown_table(self, table_data: Dict[str, Any]) -> str:
        """Reconstruct a Markdown table string from structured table data."""
        headers = table_data.get("headers", [])
        rows = table_data.get("rows", [])
        
        if not headers and not rows:
            return ""
            
        lines = []
        
        # 1. Header row
        if headers:
            header_line = "| " + " | ".join(headers) + " |"
            lines.append(header_line)
            
            # 2. Separator row
            separator_line = "| " + " | ".join(["---"] * len(headers)) + " |"
            lines.append(separator_line)
        
        # 3. Data rows
        for row in rows:
            # Row is a list of dicts with 'text' key
            cell_texts = [cell.get("text", "") for cell in row]
            
            # Handle case where row might have different length than headers (shouldn't happen in valid MD but good for safety)
            # If headers exist, ensure row matches header count (pad with empty)
            if headers:
                while len(cell_texts) < len(headers):
                    cell_texts.append("")
                # Truncate if too long? Or just let it be. MD tables are flexible.
            
            row_line = "| " + " | ".join(cell_texts) + " |"
            lines.append(row_line)
            
        return "\n".join(lines)
