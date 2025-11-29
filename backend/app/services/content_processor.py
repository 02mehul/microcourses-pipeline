import re
import json
import logging
import os
import time
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
from ..models import Block

logger = logging.getLogger(__name__)

class ContentProcessor:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize ContentProcessor with Gemini API.

        Args:
            api_key: Gemini API key. If not provided, reads from GEMINI_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY must be set in environment or passed to constructor")

        # Initialize Gemini client
        self.client = genai.Client(api_key=self.api_key)

    def filter_content(self, text: str) -> str:
        """
        Filter out irrelevant content like legal notices, editorial details, etc.
        """
        # Patterns to remove
        patterns = [
            r"© DIW Berlin \d{4}",
            r"DIW Weekly Report \d+\+\d+/\d+",
            r"LEGAL AND EDITORIAL DETAILS",
            r"DIW Berlin — Deutsches Institut für Wirtschaftsforschung e\. V\.",
            r"www\.diw\.de",
            r"Phone: \+49 30 897 89 – 0",
            r"ISSN \d{4}-\d{4}",
            r"Reprint and further distribution.*",
            r"JEL:.*",
            r"Keywords:.*",
            r"Layout\s+Roman Wilhelm.*",
            r"Composition\s+Satz-Rechen-Zentrum.*",
            r"Editors-in-chief.*",
            r"Reviewer.*",
            r"Editorial staff.*",
        ]

        filtered_text = text
        for pattern in patterns:
            filtered_text = re.sub(pattern, "", filtered_text, flags=re.IGNORECASE | re.MULTILINE)

        # Remove multiple newlines
        filtered_text = re.sub(r"\n{3,}", "\n\n", filtered_text)
        return filtered_text.strip()

    def detect_subchapters(self, blocks: List[Block]) -> List[Dict[str, Any]]:
        """
        Detect chapter and subchapter boundaries from blocks.
        Returns list of subchapter dictionaries with metadata and content blocks.
        """
        subchapters = []
        current_chapter = None
        current_subchapter = None
        current_blocks = []

        for block in blocks:
            # Skip non-text blocks for hierarchy detection
            if not block.text_raw or not block.semantic_role:
                current_blocks.append(block)
                continue

            role = block.semantic_role
            text = block.text_raw.strip()

            # Detect chapter heading (H1 or title)
            if role in ["title", "chapter_heading"] or block.hierarchy_level == 0:
                # Save previous subchapter if exists
                if current_subchapter and current_blocks:
                    current_subchapter["blocks"] = current_blocks
                    subchapters.append(current_subchapter)
                    current_blocks = []

                # New chapter
                current_chapter = text
                current_subchapter = None

            # Detect subchapter/section heading (H2, H3)
            elif role == "section_heading" or (block.hierarchy_level and block.hierarchy_level >= 1):
                # Save previous subchapter if exists
                if current_subchapter and current_blocks:
                    current_subchapter["blocks"] = current_blocks
                    subchapters.append(current_subchapter)

                # New subchapter
                subchapter_id = f"ch{len(subchapters) + 1}"
                current_subchapter = {
                    "id": subchapter_id,
                    "chapter_title": current_chapter or "Introduction",
                    "subchapter_title": text,
                    "blocks": []
                }
                current_blocks = [block]

            else:
                # Regular content block
                current_blocks.append(block)

        # Save final subchapter
        if current_subchapter and current_blocks:
            current_subchapter["blocks"] = current_blocks
            subchapters.append(current_subchapter)
        elif current_blocks:
            # No subchapters detected, create a default one
            subchapters.append({
                "id": "ch1",
                "chapter_title": current_chapter or "Document Content",
                "subchapter_title": "Main Content",
                "blocks": current_blocks
            })

        logger.info(f"Detected {len(subchapters)} subchapters")
        return subchapters

    def chunk_subchapter_into_slides(self, subchapter: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Chunk a single subchapter into multiple slides if needed.
        Strategy: Create slides of reasonable size, considering graphics/tables.
        """
        blocks = subchapter["blocks"]
        if not blocks:
            return []

        # Calculate content length and complexity
        total_text = "\n".join([b.text_raw for b in blocks if b.text_raw])
        has_tables = any(b.type == "table" for b in blocks)
        has_figures = any(b.type == "figure" for b in blocks)

        # Adjust chunk size based on content
        BASE_CHUNK_SIZE = 1500  # characters
        if has_tables or has_figures:
            # Smaller chunks for content with graphics
            chunk_size = 1000
        else:
            chunk_size = BASE_CHUNK_SIZE

        # If subchapter is small enough, return as single slide
        if len(total_text) <= chunk_size:
            return [{
                "chapter_title": subchapter["chapter_title"],
                "subchapter_title": subchapter["subchapter_title"],
                "subchapter_id": subchapter["id"],
                "content": total_text
            }]

        # Split into multiple slides
        slides = []
        current_chunk = []
        current_length = 0

        for block in blocks:
            if not block.text_raw:
                continue

            block_text = block.text_raw
            block_length = len(block_text)

            # Add block to current chunk
            if current_length + block_length <= chunk_size or not current_chunk:
                current_chunk.append(block_text)
                current_length += block_length
            else:
                # Save current chunk and start new one
                slides.append({
                    "chapter_title": subchapter["chapter_title"],
                    "subchapter_title": subchapter["subchapter_title"],
                    "subchapter_id": subchapter["id"],
                    "content": "\n\n".join(current_chunk)
                })
                current_chunk = [block_text]
                current_length = block_length

        # Save final chunk
        if current_chunk:
            slides.append({
                "chapter_title": subchapter["chapter_title"],
                "subchapter_title": subchapter["subchapter_title"],
                "subchapter_id": subchapter["id"],
                "content": "\n\n".join(current_chunk)
            })

        logger.info(f"Split subchapter '{subchapter['subchapter_title']}' into {len(slides)} slides")
        return slides

    def chunk_content(self, blocks: List[Block]) -> List[Dict[str, Any]]:
        """
        Hierarchical chunking: Detect subchapters and create slides respecting structure.
        Returns list of slide dictionaries with chapter/subchapter metadata.
        """
        # Detect subchapter boundaries
        subchapters = self.detect_subchapters(blocks)

        if not subchapters:
            logger.warning("No subchapters detected, using fallback chunking")
            # Fallback to simple text chunking
            all_text = "\n".join([b.text_raw for b in blocks if b.text_raw])
            return [{
                "chapter_title": "Document",
                "subchapter_title": "Content",
                "subchapter_id": "ch1",
                "content": all_text
            }]

        # Chunk each subchapter into slides
        all_slides = []
        for subchapter in subchapters:
            slides = self.chunk_subchapter_into_slides(subchapter)
            all_slides.extend(slides)

        logger.info(f"Generated {len(all_slides)} slides from {len(subchapters)} subchapters")
        return all_slides

    def generate_all_slides_batch(self, blocks: List[Block]) -> List[Dict[str, Any]]:
        """
        Generate ALL slides in a single API call by passing the entire document content.
        The AI will determine the optimal number of slides (typically 5-10).
        
        Args:
            blocks: List of Block objects containing the document content
            
        Returns:
            List of slide dictionaries, each with title, subheading, and summary
        """
        # Combine all text blocks into single content string, including table data
        full_content = "\n\n".join([
            f"[{block.semantic_role or block.type}] {block.text_raw}" +
            (f"\n[TABLE_DATA] {json.dumps(block.table_data)}" if block.table_data else "")
            for block in blocks
            if block.text_raw
        ])
        
        # Filter content
        full_content = self.filter_content(full_content)
        
        if not full_content:
            logger.warning("No content after filtering")
            return []
        
        prompt = f"""You are an expert educational content creator. Analyze the following document content and create a comprehensive presentation.

INSTRUCTIONS:
1. Read through ALL the content carefully
2. Determine the optimal number of slides needed (typically 5-10, but use your judgment)
3. Create slides that cover the key topics, concepts, and insights
4. For EACH slide, decide if including a small table would enhance understanding
5. Only include a table if:
   - It contains important data/statistics referenced in the bullet points
   - It's small and focused (max 5 columns, 5-7 rows)
   - It provides visual clarity that text alone cannot
6. Tables should be COMPLEMENTARY to bullet points, not redundant

SLIDE LAYOUT DESIGN:
- Left side: 3-4 bullet points (key insights)
- Right side: Optional small table (supporting data)

Return ONLY a JSON object with a "slides" key containing an array of slide objects.
Each slide object must have:
- title: A clear, concise title
- subheading: A brief subheading or context
- summary: A bulleted list of 3-4 key points (as an array of strings)
- table: (OPTIONAL) Object with:
  - headers: Array of column headers (max 5)
  - rows: Array of row arrays (max 7 rows)
  - caption: Brief description of what the table shows

EXAMPLE OUTPUT:
{{
  "slides": [
    {{
      "title": "Productivity Trends",
      "subheading": "Regional Convergence Analysis",
      "summary": [
        "Rural regions show significant convergence",
        "Urban productivity gaps persist",
        "Metropolitan areas maintain advantage"
      ],
      "table": {{
        "headers": ["Year", "Rural", "Urban"],
        "rows": [
          ["2004", "65%", "85%"],
          ["2024", "89%", "93%"]
        ],
        "caption": "Eastern Germany productivity (% of national avg)"
      }}
    }}
  ]
}}

DOCUMENT CONTENT (includes [TABLE_DATA] for available tables):
{full_content[:15000]}

JSON Output:"""

        try:
            logger.info("Generating all slides in single batch API call...")
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.7
                )
            )

            result = json.loads(response.text)
            slides = result.get("slides", [])
            
            # Validate and normalize slide format
            normalized_slides = []
            for slide in slides:
                summary = slide.get("summary", [])
                # Ensure summary is formatted as bullet list
                if isinstance(summary, list):
                    summary_text = "\n".join(f"- {item}" for item in summary if item)
                elif isinstance(summary, str):
                    summary_text = summary
                else:
                    summary_text = str(summary)

                # Process table data if present
                table_data = slide.get("table")
                has_table = table_data is not None and isinstance(table_data, dict)

                # Validate table structure
                if has_table:
                    if not table_data.get("headers") or not table_data.get("rows"):
                        logger.warning(f"Invalid table structure in slide '{slide.get('title')}', skipping table")
                        has_table = False
                        table_data = None

                normalized_slides.append({
                    "title": slide.get("title", "Untitled Slide"),
                    "subheading": slide.get("subheading", ""),
                    "summary": summary_text,
                    "table_data": table_data,
                    "has_table": has_table
                })
            
            logger.info(f"Successfully generated {len(normalized_slides)} slides in single batch call")
            return normalized_slides

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error from Gemini batch generation: {e}", exc_info=True)
            logger.error(f"Raw response: {response.text if 'response' in locals() else 'No response'}")
            return []
        except Exception as e:
            logger.error(f"Error in batch slide generation: {e}", exc_info=True)
            return []

    def generate_slide_content(self, chunk: str) -> Dict[str, Any]:
        """
        Generate slide content using Gemini API.
        
        DEPRECATED: Use generate_all_slides_batch() instead for better performance.
        This method is kept for backward compatibility.
        """
        prompt = f"""You are an expert educational content creator. Your task is to create a single presentation slide from the following text chunk.

Return ONLY a JSON object with the following fields:
- title: A concise title for the slide.
- subheading: A brief subheading.
- summary: A bulleted summary of the key points (max 3-4 bullets).

Text Chunk:
{chunk}

JSON Output:"""

        try:
            # Add small delay to avoid rate limits
            time.sleep(1)

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",  # More stable with better rate limits
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.7
                )
            )

            result = json.loads(response.text)
            logger.debug(f"Gemini response: {result}")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error from Gemini: {e}", exc_info=True)
            logger.error(f"Raw response: {response.text if 'response' in locals() else 'No response'}")
            return {
                "title": "Error Generating Slide",
                "subheading": "",
                "summary": "Could not parse JSON response from API."
            }
        except Exception as e:
            logger.error(f"Error generating slide content: {e}", exc_info=True)
            return {
                "title": "Error Generating Slide",
                "subheading": "",
                "summary": "Could not generate content."
            }

    def generate_questions_for_subchapter(self, subchapter_content: str) -> List[Dict[str, str]]:
        """
        Generate 3-4 review questions for an entire subchapter (Milestone 3 requirement).
        """
        prompt = f"""You are an expert educational content creator. Create 3-4 comprehensive review questions for this subchapter.

These questions should test understanding of the ENTIRE subchapter content, not just individual slides.

Return ONLY a JSON object with a key "questions" containing a list of objects, each with:
- question_text: A clear, comprehensive question
- answer_text: A detailed correct answer

Subchapter Content:
{subchapter_content[:3000]}

JSON Output:"""

        try:
            # Add delay to avoid rate limits
            time.sleep(1)

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.7
                )
            )

            data = json.loads(response.text)
            questions = data.get("questions", [])
            logger.info(f"Generated {len(questions)} questions for subchapter")
            return questions

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error from Gemini: {e}", exc_info=True)
            logger.error(f"Raw response: {response.text if 'response' in locals() else 'No response'}")
            return []
        except Exception as e:
            logger.error(f"Error generating questions: {e}", exc_info=True)
            return []

    def generate_questions(self, chunk: str) -> List[Dict[str, str]]:
        """
        Generate review questions using Gemini API (legacy method for single chunks).
        """
        prompt = f"""You are an expert educational content creator. Create 3 review questions based on the following text.

Return ONLY a JSON object with a key "questions" containing a list of objects, each with:
- question_text: The question.
- answer_text: The correct answer.

Text:
{chunk}

JSON Output:"""

        try:
            # Add small delay to avoid rate limits
            time.sleep(1)

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",  # More stable with better rate limits
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.7
                )
            )

            data = json.loads(response.text)
            questions = data.get("questions", [])
            logger.debug(f"Generated {len(questions)} questions")
            return questions

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error from Gemini: {e}", exc_info=True)
            logger.error(f"Raw response: {response.text if 'response' in locals() else 'No response'}")
            return []
        except Exception as e:
            logger.error(f"Error generating questions: {e}", exc_info=True)
            return []
