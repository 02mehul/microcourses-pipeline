
import mistune
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

class MarkdownParser:
    def __init__(self):
        self.markdown = mistune.create_markdown(renderer=None, plugins=['table'])


    def parse(self, markdown_text: str, page_num: int) -> List[Dict[str, Any]]:
        ast = self.markdown(markdown_text)
        
        blocks = [] 

        for node in ast:
            block = self._process_node(node)
            if not block:
                continue
            blocks.append(block)

        return blocks

    def _process_node(self, node: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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
                "bbox": {"x0": 0, "y0": 0, "x1": 0, "y1": 0}
            }

        elif node_type == "paragraph":
            text = self._get_text_content(node)

            if "![" in text and "](" in text:
                pass

            text_lower = text.lower()
            is_figure_caption = (
                text.startswith("Note:") or
                text.startswith("Figure ") or
                text.startswith("Chart ") or
                "the chart shows" in text_lower or
                "the figure shows" in text_lower or
                "the graph shows" in text_lower or
                "source:" in text_lower or
                "© diw berlin" in text_lower
            )

            if is_figure_caption:
                return {
                    "type": "figure",
                    "semantic_role": "figure_caption",
                    "text_raw": text,
                    "bbox": {"x0": 0, "y0": 0, "x1": 0, "y1": 0}
                }

            return {
                "type": "text",
                "semantic_role": "paragraph",
                "text_raw": text,
                "bbox": {"x0": 0, "y0": 0, "x1": 0, "y1": 0}
            }

        elif node_type == "list":
            text = self._get_text_content(node)
            return {
                "type": "text",
                "semantic_role": "list",
                "text_raw": text,
                "bbox": {"x0": 0, "y0": 0, "x1": 0, "y1": 0}
            }
            
        elif node_type == "table":
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
            children = node.get("children", [])
            alt_text = ""
            image_url = ""

            if children:
                alt_text = self._get_text_content(node)

            if "attrs" in node and "url" in node["attrs"]:
                image_url = node["attrs"]["url"]
            elif children and "raw" in children[0]:
                image_url = children[0]["raw"]

            return {
                "type": "figure",
                "semantic_role": "figure",
                "text_raw": alt_text,
                "image_path": image_url,
                "bbox": {"x0": 0, "y0": 0, "x1": 0, "y1": 0},
                "metadata": {
                    "original_url": image_url,
                    "alt_text": alt_text
                }
            }
        
        elif node_type == "block_html":
            html_content = node.get("raw", "")
            if "<table" in html_content:
                table_data = self._parse_html_table(html_content)
                text_raw = html_content 
                return {
                    "type": "table",
                    "semantic_role": "table",
                    "text_raw": text_raw,
                    "table_data": table_data,
                    "bbox": {"x0": 0, "y0": 0, "x1": 0, "y1": 0}
                }

        elif node_type == "block_code":
            text = node.get("raw", "")
            return {
                "type": "text",
                "semantic_role": "code_block",
                "text_raw": text,
                "bbox": {"x0": 0, "y0": 0, "x1": 0, "y1": 0}
            }

        elif node_type == "block_quote":
            text = self._get_text_content(node)
            return {
                "type": "text",
                "semantic_role": "quote",
                "text_raw": text,
                "bbox": {"x0": 0, "y0": 0, "x1": 0, "y1": 0}
            }

        elif node_type == "thematic_break":
            return None

        return None

    def _get_text_content(self, node: Dict[str, Any]) -> str:
        if "raw" in node:
            return node["raw"]
        if "text" in node:
            return node["text"]
        if "children" in node:
            return "".join([self._get_text_content(child) for child in node["children"]])
        return ""
    
    def _parse_html_table(self, html_str: str) -> Dict[str, Any]:
        try:
            soup = BeautifulSoup(html_str, "html.parser")
            table = soup.find("table")
            
            if not table:
                return {}
            
            headers = []
            thead = table.find("thead")
            if thead:
                header_row = thead.find("tr")
                if header_row:
                    headers = [th.get_text(strip=True) for th in header_row.find_all(["th", "td"])]
            
            rows = []
            tbody = table.find("tbody") or table
            for tr in tbody.find_all("tr"):
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
                            "colspan": 1,
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
        headers = table_data.get("headers", [])
        rows = table_data.get("rows", [])
        
        if not headers and not rows:
            return ""
            
        lines = []
        
        if headers:
            header_line = "| " + " | ".join(headers) + " |"
            lines.append(header_line)
            
            separator_line = "| " + " | ".join(["---"] * len(headers)) + " |"
            lines.append(separator_line)
        
        for row in rows:
            cell_texts = [cell.get("text", "") for cell in row]
            
            if headers:
                while len(cell_texts) < len(headers):
                    cell_texts.append("")
            
            row_line = "| " + " | ".join(cell_texts) + " |"
            lines.append(row_line)
            
        return "\n".join(lines)
