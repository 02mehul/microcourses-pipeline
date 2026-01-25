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
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY must be set in environment or passed to constructor")

        self.client = genai.Client(api_key=self.api_key)

    def filter_content(self, text: str) -> str:
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

        filtered_text = re.sub(r"\n{3,}", "\n\n", filtered_text)
        return filtered_text.strip()

    def detect_subchapters(self, blocks: List[Block]) -> List[Dict[str, Any]]:
        subchapters = []
        current_chapter = None
        current_subchapter = None
        current_blocks = []

        section_patterns = [
            r'^Figure \d+',
            r'^Chart \d+',
            r'^Table \d+',
            r'^Section:',
            r'^Document section:',
            r'^Box —',
            r'^\d+\.\s+[A-Z]',
        ]
        section_regex = re.compile('|'.join(section_patterns), re.IGNORECASE)

        for block in blocks:
            if not block.text_raw or not block.semantic_role:
                current_blocks.append(block)
                continue

            role = block.semantic_role
            text = block.text_raw.strip()

            if role in ["title", "chapter_heading"] or block.hierarchy_level == 0:
                if current_subchapter and current_blocks:
                    current_subchapter["blocks"] = current_blocks
                    subchapters.append(current_subchapter)
                    current_blocks = []

                current_chapter = text
                current_subchapter = None

            elif role == "section_heading" or (block.hierarchy_level and block.hierarchy_level >= 1):
                if current_subchapter and current_blocks:
                    current_subchapter["blocks"] = current_blocks
                    subchapters.append(current_subchapter)

                subchapter_id = f"ch{len(subchapters) + 1}"
                current_subchapter = {
                    "id": subchapter_id,
                    "chapter_title": current_chapter or "Introduction",
                    "subchapter_title": text,
                    "blocks": []
                }
                current_blocks = [block]

            elif section_regex.match(text):
                if current_subchapter and current_blocks:
                    current_subchapter["blocks"] = current_blocks
                    subchapters.append(current_subchapter)

                subchapter_id = f"ch{len(subchapters) + 1}"
                title = text[:80].split('\n')[0]
                current_subchapter = {
                    "id": subchapter_id,
                    "chapter_title": current_chapter or "Document Content",
                    "subchapter_title": title,
                    "blocks": []
                }
                current_blocks = [block]

            else:
                current_blocks.append(block)

        if current_subchapter and current_blocks:
            current_subchapter["blocks"] = current_blocks
            subchapters.append(current_subchapter)
        elif current_blocks:
            subchapters.append({
                "id": "ch1",
                "chapter_title": current_chapter or "Document Content",
                "subchapter_title": "Main Content",
                "blocks": current_blocks
            })

        MAX_SUBCHAPTERS = 8
        if len(subchapters) > MAX_SUBCHAPTERS:
            logger.info(f"Detected {len(subchapters)} subchapters, merging to max {MAX_SUBCHAPTERS}...")
            
            import math
            chunk_size = math.ceil(len(subchapters) / MAX_SUBCHAPTERS)
            
            merged_subchapters = []
            for i in range(0, len(subchapters), chunk_size):
                chunk = subchapters[i:i + chunk_size]
                if not chunk:
                    continue
                
                base = chunk[0]
                merged_blocks = []
                for sc in chunk:
                    merged_blocks.extend(sc["blocks"])
                
                if len(chunk) > 1:
                    new_title = f"{base['subchapter_title']} - {chunk[-1]['subchapter_title']}"
                    if len(new_title) > 100:
                        new_title = f"{base['subchapter_title']} et al."
                else:
                    new_title = base["subchapter_title"]

                merged_subchapters.append({
                    "id": base["id"],
                    "chapter_title": base["chapter_title"],
                    "subchapter_title": new_title,
                    "blocks": merged_blocks
                })
            
            subchapters = merged_subchapters

        logger.info(f"Final subchapters count: {len(subchapters)}")
        return subchapters

    def chunk_subchapter_into_slides(self, subchapter: Dict[str, Any]) -> List[Dict[str, Any]]:
        blocks = subchapter["blocks"]
        if not blocks:
            return []

        total_text = "\n".join([b.text_raw for b in blocks if b.text_raw])
        has_tables = any(b.type == "table" for b in blocks)
        has_figures = any(b.type == "figure" for b in blocks)

        BASE_CHUNK_SIZE = 1500
        if has_tables or has_figures:
            chunk_size = 1000
        else:
            chunk_size = BASE_CHUNK_SIZE

        if len(total_text) <= chunk_size:
            return [{
                "chapter_title": subchapter["chapter_title"],
                "subchapter_title": subchapter["subchapter_title"],
                "subchapter_id": subchapter["id"],
                "content": total_text
            }]

        slides = []
        current_chunk = []
        current_length = 0

        for block in blocks:
            if not block.text_raw:
                continue

            block_text = block.text_raw
            block_length = len(block_text)

            if current_length + block_length <= chunk_size or not current_chunk:
                current_chunk.append(block_text)
                current_length += block_length
            else:
                slides.append({
                    "chapter_title": subchapter["chapter_title"],
                    "subchapter_title": subchapter["subchapter_title"],
                    "subchapter_id": subchapter["id"],
                    "content": "\n\n".join(current_chunk)
                })
                current_chunk = [block_text]
                current_length = block_length

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
        subchapters = self.detect_subchapters(blocks)

        if not subchapters:
            logger.warning("No subchapters detected, using fallback chunking")
            all_text = "\n".join([b.text_raw for b in blocks if b.text_raw])
            return [{
                "chapter_title": "Document",
                "subchapter_title": "Content",
                "subchapter_id": "ch1",
                "content": all_text
            }]

        all_slides = []
        for subchapter in subchapters:
            slides = self.chunk_subchapter_into_slides(subchapter)
            all_slides.extend(slides)

        logger.info(f"Generated {len(all_slides)} slides from {len(subchapters)} subchapters")
        return all_slides

    def generate_all_slides_batch(self, blocks: List[Block]) -> List[Dict[str, Any]]:
        full_content = "\n\n".join([
            f"[{block.semantic_role or block.type}] {block.text_raw}" +
            (f"\n[TABLE_DATA] {json.dumps(block.table_data)}" if block.table_data else "")
            for block in blocks
            if block.text_raw
        ])
        
        full_content = self.filter_content(full_content)
        
        if not full_content:
            logger.warning("No content after filtering")
            return []
        
        prompt = f"""You are an expert educational content creator. Analyze the following document content and create a comprehensive presentation.

INSTRUCTIONS:
1. Read through ALL the content carefully
2. Create UP TO 8 slides maximum (aim for 6-8 slides for comprehensive coverage)
3. Create slides that cover the key topics, concepts, and insights
4. For EACH slide, analyze if the content contains data that would benefit from visualization

VISUALIZATION DECISION FRAMEWORK:
For each slide, decide the BEST way to present data (if any):

**Line Chart** - Use when:
- Showing trends over time (years, quarters, months)
- Continuous progression or growth patterns
- Comparing multiple trend lines
- Example: GDP growth 2015-2025, temperature changes, stock prices

**Bar Chart** - Use when:
- Comparing quantities across distinct categories
- Ranking items by value
- Side-by-side group comparisons
- Example: Sales by region, survey results by demographic

**Pie Chart** - Use when:
- Showing proportions or percentages that sum to 100%
- Part-to-whole relationships (3-6 segments max for clarity)
- Market share, budget allocation
- Example: Budget breakdown by department, market share distribution

**Table** - Use when:
- Multi-attribute comparisons (feature matrices)
- Precise lookup data needed
- Data doesn't fit time/category/proportion patterns
- Example: Product feature comparison, specification sheet

**No Visualization** - Use when:
- Content is conceptual (theories, definitions, frameworks)
- Narrative or qualitative insights
- No numeric data present

RULES:
- Maximum 1 visualization per slide
- Keep visualizations simple (5-8 data points ideal, max 10)
- Only visualize data explicitly stated in the document
- Do NOT invent or extrapolate data
- Visualizations should COMPLEMENT bullet points, not duplicate them

SLIDE LAYOUT:
- Left side: 3-4 bullet points (key insights)
- Right side: Optional visualization (chart or table)

Return ONLY a JSON object with a "slides" key containing an array of slide objects.
Each slide object must have:
- title: Clear, concise title
- subheading: Brief context or subtitle
- summary: Array of 3-4 key points (strings)
- visualization: (OPTIONAL) Object with one of these formats:

LINE CHART FORMAT:
{{
  "type": "chart",
  "chart_type": "line",
  "data": [
    {{"name": "2015", "value": 100}},
    {{"name": "2016", "value": 120}},
    {{"name": "2017", "value": 135}}
  ],
  "title": "GDP Growth Over Time"
}}

BAR CHART FORMAT:
{{
  "type": "chart",
  "chart_type": "bar",
  "data": [
    {{"name": "Product A", "value": 450}},
    {{"name": "Product B", "value": 380}},
    {{"name": "Product C", "value": 320}}
  ],
  "title": "Sales by Product"
}}

PIE CHART FORMAT:
{{
  "type": "chart",
  "chart_type": "pie",
  "data": [
    {{"name": "Marketing", "value": 35}},
    {{"name": "R&D", "value": 25}},
    {{"name": "Operations", "value": 40}}
  ],
  "title": "Budget Allocation (%)"
}}

TABLE FORMAT:
{{
  "type": "table",
  "data": {{
    "headers": ["Feature", "Plan A", "Plan B"],
    "rows": [
      ["Storage", "10GB", "50GB"],
      ["Users", "5", "Unlimited"],
      ["Support", "Email", "24/7 Phone"]
    ]
  }},
  "title": "Plan Comparison"
}}

EXAMPLE OUTPUT:
{{
  "slides": [
    {{
      "title": "Productivity Trends",
      "subheading": "Regional Convergence Analysis",
      "summary": [
        "Rural regions show 24% convergence since 2004",
        "Urban productivity gaps narrowed to 4%",
        "Metropolitan areas maintain consistent advantage"
      ],
      "visualization": {{
        "type": "chart",
        "chart_type": "line",
        "data": [
          {{"name": "2004", "value": 65}},
          {{"name": "2014", "value": 78}},
          {{"name": "2024", "value": 89}}
        ],
        "title": "Rural Productivity (% of national average)"
      }}
    }}
  ]
}}

DOCUMENT CONTENT (includes [TABLE_DATA] for available tables):
{full_content[:25000]}

JSON Output:"""

        try:
            logger.info("Generating all slides in single batch API call...")
            
            response = self.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.7
                )
            )

            result = json.loads(response.text)
            slides = result.get("slides", [])
            
            normalized_slides = []
            for slide in slides:
                summary = slide.get("summary", [])
                if isinstance(summary, list):
                    summary_text = "\n".join(f"- {item}" for item in summary if item)
                elif isinstance(summary, str):
                    summary_text = summary
                else:
                    summary_text = str(summary)

                visualization = slide.get("visualization")
                visualization_data = None
                has_table = False
                table_data = None

                if visualization and isinstance(visualization, dict):
                    viz_type = visualization.get("type")

                    if viz_type == "chart":
                        if visualization.get("chart_type") in ["line", "bar", "pie"] and visualization.get("data"):
                            visualization_data = visualization
                            logger.info(f"Slide '{slide.get('title')}': Using {visualization.get('chart_type')} chart")
                        else:
                            logger.warning(f"Invalid chart structure in slide '{slide.get('title')}', skipping visualization")

                    elif viz_type == "table":
                        table_info = visualization.get("data", {})
                        if table_info.get("headers") and table_info.get("rows"):
                            visualization_data = visualization
                            has_table = True
                            table_data = table_info
                            logger.info(f"Slide '{slide.get('title')}': Using table")
                        else:
                            logger.warning(f"Invalid table structure in slide '{slide.get('title')}', skipping visualization")

                normalized_slides.append({
                    "title": slide.get("title", "Untitled Slide"),
                    "subheading": slide.get("subheading", ""),
                    "summary": summary_text,
                    "visualization_data": visualization_data,
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

    def generate_slides_for_subchapter(self, blocks: List[Block], subchapter_meta: Dict[str, Any]) -> List[Dict[str, Any]]:
        full_content = "\n\n".join([
            f"[{block.semantic_role or block.type}] {block.text_raw}" +
            (f"\n[TABLE_DATA] {json.dumps(block.table_data)}" if block.table_data else "")
            for block in blocks
            if block.text_raw
        ])
        
        full_content = self.filter_content(full_content)
        
        if not full_content:
            return []

        prompt = f"""You are an expert educational content creator. Create a set of presentation slides for the following subchapter.

CONTEXT:
Chapter: {subchapter_meta.get('chapter_title')}
Subchapter: {subchapter_meta.get('subchapter_title')}

INSTRUCTIONS:
1. Create 1-3 slides that cover the key concepts of this subchapter.
2. Each slide must have a clear title, subheading, and bulleted summary.
3. Include a small table ONLY if the content contains data that benefits from it.

Return ONLY a JSON object with a "slides" key containing an array of slide objects.
Each slide object must have:
- title: A clear, concise title
- subheading: A brief subheading
- summary: A bulleted list of 3-4 key points (as an array of strings)
- table: (OPTIONAL) {{headers: [], rows: [], caption: ""}}

CONTENT:
{full_content[:10000]}

JSON Output:"""

        try:
            time.sleep(1)
            
            response = self.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.7
                )
            )

            result = json.loads(response.text)
            slides = result.get("slides", [])
            
            normalized_slides = []
            for slide in slides[:3]:
                summary = slide.get("summary", [])
                if isinstance(summary, list):
                    summary_text = "\n".join(f"- {item}" for item in summary if item)
                elif isinstance(summary, str):
                    summary_text = summary
                else:
                    summary_text = str(summary)

                table_data = slide.get("table")
                has_table = table_data is not None and isinstance(table_data, dict)
                if has_table and (not table_data.get("headers") or not table_data.get("rows")):
                    has_table = False
                    table_data = None

                normalized_slides.append({
                    "title": slide.get("title", "Untitled Slide"),
                    "subheading": slide.get("subheading", ""),
                    "summary": summary_text,
                    "table_data": table_data,
                    "has_table": has_table,
                    "chapter_title": subchapter_meta.get("chapter_title"),
                    "subchapter_title": subchapter_meta.get("subchapter_title"),
                    "subchapter_id": subchapter_meta.get("id")
                })
            
            return normalized_slides

        except Exception as e:
            logger.error(f"Error generating slides for subchapter: {e}", exc_info=True)
            return []


    def generate_questions_for_subchapter(self, subchapter_content: str) -> List[Dict[str, str]]:
        prompt = f"""You are an expert educational content creator. Create 4-5 comprehensive review questions for this subchapter using MULTIPLE question formats.

QUESTION TYPE GUIDELINES:

1. **Short Answer** - Use for factual, specific information:
   - Dates, names, single terms, numbers
   - Example: "What year did the Berlin Wall fall?" → Answer: "1989"

2. **Sentence** - Use for explanations and concepts:
   - "Why", "How", "Explain" questions
   - Example: "Explain the main factor..." → Answer: Full sentence explanation

3. **Multiple Choice** - Use for testing understanding between options:
   - Comparing concepts, identifying best practices
   - 4 options (A, B, C, D), one correct
   - Example: "Which region showed the highest growth?"

DISTRIBUTION:
- Create a MIX of all three types (not all the same type)
- Aim for: 1-2 short_answer, 2-3 sentence, 1-2 multiple_choice

Return ONLY a JSON object with a key "questions" containing a list of objects, each with:
- question_text: The question
- question_type: "short_answer" | "sentence" | "multiple_choice"
- answer_text: The correct answer (for short_answer and sentence types)
- options: Array of 4 option strings (ONLY for multiple_choice, omit for others)
- correct_answer: The correct option letter "A", "B", "C", or "D" (ONLY for multiple_choice)

EXAMPLE OUTPUT:
{{
  "questions": [
    {{
      "question_text": "What percentage of growth was observed in the rural sector?",
      "question_type": "short_answer",
      "answer_text": "24%"
    }},
    {{
      "question_text": "Explain why the urban-rural productivity gap narrowed between 2004-2024.",
      "question_type": "sentence",
      "answer_text": "The gap narrowed due to targeted infrastructure investments and education programs in rural areas, which increased productivity."
    }},
    {{
      "question_text": "Which region maintained the highest productivity throughout the study period?",
      "question_type": "multiple_choice",
      "options": [
        "Rural eastern regions",
        "Metropolitan areas",
        "Mid-sized cities",
        "Coastal towns"
      ],
      "correct_answer": "B"
    }}
  ]
}}

Subchapter Content:
{subchapter_content[:3000]}

JSON Output:"""

        try:
            time.sleep(1)

            response = self.client.models.generate_content(
                model="gemini-2.5-pro",
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
        prompt = f"""You are an expert educational content creator. Create 3 review questions based on the following text.

Return ONLY a JSON object with a key "questions" containing a list of objects, each with:
- question_text: The question.
- answer_text: The correct answer.

Text:
{chunk}

JSON Output:"""

        try:
            time.sleep(1)

            response = self.client.models.generate_content(
                model="gemini-2.5-pro",
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

    def chat_with_document(self, document_text: str, message: str, history: List[Dict[str, str]]) -> str:
        try:
            chat_history = []
            for msg in history:
                role = "user" if msg["role"] == "user" else "model"
                chat_history.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))

            system_instruction = f"""You are a helpful and knowledgeable Teaching Assistant for a micro-course.
            
            CONTEXT:
            The user is studying the following document:
            
            {document_text[:30000]}
            
            INSTRUCTIONS:
            1. Answer the user's questions based PRIMARILY on the provided document content.
            2. If the answer is not in the document, you can use your general knowledge but mention that it's outside the document's scope.
            3. Be encouraging, clear, and educational.
            4. Use Markdown for formatting (bold, lists, code blocks) to make answers easy to read.
            5. Keep answers concise unless asked for detailed explanations.
            6. DATA ANALYSIS & CHARTS:
               - The document content may contain [TABLE_DATA] JSON blocks. Use this data to answer analytical questions.
               - If the user asks for a chart, visualization, or analysis that benefits from a chart, generate a JSON block wrapped in [CHART] tags.
               - Supported chart types: "bar", "line", "pie", "area".
               - Format:
                 [CHART]
                 {{
                   "type": "bar",
                   "title": "Chart Title",
                   "data": [
                     {{"label": "Category A", "value": 10}},
                     {{"label": "Category B", "value": 20}}
                   ],
                   "xAxisKey": "label",
                   "seriesKey": "value",
                   "description": "Brief explanation of the chart"
                 }}
                 [/CHART]
               - You can include multiple charts if needed.
               - Always provide a text summary/analysis along with the chart.
            """

            chat = self.client.chats.create(
                model="gemini-2.5-pro",
                history=chat_history,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.7,
                )
            )

            response = chat.send_message(message)
            return response.text

        except Exception as e:
            logger.error(f"Error in chat: {e}", exc_info=True)
            return "I apologize, but I encountered an error while processing your request. Please try again."
