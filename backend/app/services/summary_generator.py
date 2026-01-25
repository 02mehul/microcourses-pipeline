import json
import logging
import os
import re
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
from ..models import Block

logger = logging.getLogger(__name__)


class SummaryGenerator:

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        
        self.client = genai.Client(api_key=self.api_key)
        self.model_id = "gemini-2.0-flash"

    def _extract_text_from_blocks(self, blocks: List[Block]) -> str:
        text_parts = []
        for block in blocks:
            if block.text_raw:
                text_parts.append(block.text_raw)
        return "\n\n".join(text_parts)

    def _count_words(self, text: str) -> int:
        return len(text.split())

    def _estimate_reading_time(self, word_count: int) -> int:
        return max(1, round(word_count / 200))

    def _count_tables(self, blocks: List[Block]) -> int:
        return sum(1 for b in blocks if b.type == "table" or b.table_data)

    def _count_images(self, blocks: List[Block]) -> int:
        return sum(1 for b in blocks if b.type == "figure" or b.image_path)

    def calculate_stats(self, blocks: List[Block], page_count: int) -> Dict[str, Any]:
        full_text = self._extract_text_from_blocks(blocks)
        word_count = self._count_words(full_text)
        
        avg_words_per_block = word_count / len(blocks) if blocks else 0
        table_count = self._count_tables(blocks)
        image_count = self._count_images(blocks)
        
        complexity = 5.0
        if avg_words_per_block > 100:
            complexity += 1
        if avg_words_per_block > 200:
            complexity += 1
        if table_count > 3:
            complexity += 1
        if word_count > 5000:
            complexity += 1
        if word_count > 10000:
            complexity += 1
        complexity = min(10, max(1, complexity))

        return {
            "word_count": word_count,
            "reading_time_minutes": self._estimate_reading_time(word_count),
            "page_count": page_count,
            "complexity_score": round(complexity, 1),
            "block_count": len(blocks),
            "table_count": table_count,
            "image_count": image_count
        }

    def generate_executive_summary(self, blocks: List[Block]) -> str:
        full_text = self._extract_text_from_blocks(blocks)

        max_chars = 15000
        if len(full_text) > max_chars:
            full_text = full_text[:max_chars] + "..."

        prompt = f"""You are creating an executive summary for educational purposes.

Write a concise 3-5 sentence summary that:
- Clearly states the document's main topic and purpose
- Identifies the key problem or question being addressed
- Highlights the most significant concepts, findings, or arguments
- Is written in clear, accessible language suitable for learners
- Provides enough context for someone unfamiliar with the topic

Write ONLY the executive summary as plain text, no formatting or preamble.

Document content:
{full_text}"""

        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=500
                )
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
            return "Summary generation failed. Please try again."

    def extract_key_concepts(self, blocks: List[Block]) -> List[Dict[str, Any]]:
        full_text = self._extract_text_from_blocks(blocks)

        max_chars = 15000
        if len(full_text) > max_chars:
            full_text = full_text[:max_chars] + "..."

        prompt = f"""You are analyzing an educational document to identify the most important concepts for a learner.

Extract the 6-8 most critical concepts or topics that a student must understand from this document.

For each concept, provide:
- name: The concept name (2-4 words maximum, clear and specific)
- importance: A score from 0-100 indicating how essential this concept is for understanding the document (be selective - only truly important concepts should score above 70)
- frequency: Estimated number of times this concept appears or is referenced throughout the document
- category: Classify as one of: "Core Concept", "Methodology", "Theory", "Application", "Case Study", "Framework"

IMPORTANT: Rank by pedagogical importance, not just frequency. Focus on concepts that form the foundation of understanding.

Return ONLY a valid JSON array with no markdown, explanations, or additional text:
[{{"name": "...", "importance": 85, "frequency": 12, "category": "..."}}, ...]

Document content:
{full_text}"""

        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=1000
                )
            )

            text = response.text.strip()
            if text.startswith("```"):
                text = re.sub(r'^```(?:json)?\n?', '', text)
                text = re.sub(r'\n?```$', '', text)

            try:
                concepts = json.loads(text)
            except json.JSONDecodeError as json_err:
                logger.error(f"Failed to parse JSON for key concepts: {json_err}")
                logger.debug(f"Raw response text: {text}")
                return []

            validated = []
            for c in concepts[:8]:
                try:
                    validated.append({
                        "name": str(c.get("name", "Unknown"))[:50],
                        "importance": min(100, max(0, float(c.get("importance", 50)))),
                        "frequency": max(1, int(c.get("frequency", 1))),
                        "category": str(c.get("category", "General"))[:30]
                    })
                except (ValueError, TypeError) as val_err:
                    logger.warning(f"Skipping invalid concept entry: {val_err}")
                    continue

            return validated
        except Exception as e:
            logger.error(f"Error extracting key concepts: {e}")
            return []


    def extract_takeaways_and_objectives(self, blocks: List[Block]) -> Dict[str, List[str]]:
        full_text = self._extract_text_from_blocks(blocks)

        max_chars = 15000
        if len(full_text) > max_chars:
            full_text = full_text[:max_chars] + "..."

        prompt = f"""You are creating a learning summary for students studying this document.

Extract two critical elements:

1. **Main Takeaways** (4-6 items): The most important insights, facts, or conclusions that a learner must remember. These should be:
   - Specific and actionable
   - Written as complete sentences
   - Focused on "what you should know"
   - Prioritized by importance

2. **Learning Objectives** (3-5 items): What a learner will be able to DO after studying this material. Start each with action verbs like:
   - "Explain...", "Apply...", "Analyze...", "Demonstrate...", "Evaluate...", "Create..."
   - Focus on skills and capabilities, not just knowledge retention

Return ONLY a valid JSON object with no markdown, explanations, or additional text:
{{
    "takeaways": ["Takeaway 1", "Takeaway 2", ...],
    "objectives": ["Explain the relationship between...", "Apply the concept of...", ...]
}}

Document content:
{full_text}"""

        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=1000
                )
            )

            text = response.text.strip()
            if text.startswith("```"):
                text = re.sub(r'^```(?:json)?\n?', '', text)
                text = re.sub(r'\n?```$', '', text)

            try:
                data = json.loads(text)
            except json.JSONDecodeError as json_err:
                logger.error(f"Failed to parse JSON for takeaways/objectives: {json_err}")
                logger.debug(f"Raw response text: {text}")
                return {"takeaways": [], "objectives": []}

            return {
                "takeaways": [str(t)[:200] for t in data.get("takeaways", [])[:6]],
                "objectives": [str(o)[:200] for o in data.get("objectives", [])[:5]]
            }
        except Exception as e:
            logger.error(f"Error extracting takeaways and objectives: {e}")
            return {"takeaways": [], "objectives": []}

    def create_full_summary(self, blocks: List[Block], page_count: int) -> Dict[str, Any]:
        logger.info(f"Generating full summary for {len(blocks)} blocks")
        
        stats = self.calculate_stats(blocks, page_count)
        logger.info(f"Stats calculated: {stats['word_count']} words")
        
        executive_summary = self.generate_executive_summary(blocks)
        logger.info("Executive summary generated")
        
        key_concepts = self.extract_key_concepts(blocks)
        logger.info(f"Extracted {len(key_concepts)} key concepts")

        insights = self.extract_takeaways_and_objectives(blocks)
        logger.info(f"Extracted {len(insights['takeaways'])} takeaways and {len(insights['objectives'])} objectives")
        
        return {
            "executive_summary": executive_summary,
            "stats": stats,
            "key_concepts": key_concepts,
            "topic_distribution": [],
            "main_takeaways": insights["takeaways"],
            "learning_objectives": insights["objectives"]
        }
