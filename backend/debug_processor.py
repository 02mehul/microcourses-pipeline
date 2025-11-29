import asyncio
import logging
from app.services.content_processor import ContentProcessor
from app.models import Block

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    print("--- Starting Debug ---")
    
    # 1. Mock Blocks
    blocks = [
        Block(text_raw="Chapter 1: Introduction", semantic_role="title"),
        Block(text_raw="This is the introduction to the course.", semantic_role="paragraph"),
        Block(text_raw="We will learn about many things.", semantic_role="paragraph"),
        Block(text_raw="Section 1.1: Basics", semantic_role="h2"),
        Block(text_raw="Here are the basics.", semantic_role="paragraph"),
        Block(text_raw="© DIW Berlin 2025", semantic_role="paragraph"), # Should be filtered
    ]
    
    print(f"Created {len(blocks)} mock blocks.")

    # 2. Initialize Processor
    processor = ContentProcessor()
    
    # 3. Test Chunking
    chunks = processor.chunk_content(blocks)
    print(f"Generated {len(chunks)} chunks.")
    for i, c in enumerate(chunks):
        print(f"Chunk {i}: {len(c)} chars")
        print(f"--- START CHUNK {i} ---\n{c}\n--- END CHUNK {i} ---")

    # 4. Test Filtering
    print("\nTesting Filtering...")
    for i, c in enumerate(chunks):
        filtered = processor.filter_content(c)
        print(f"Chunk {i} Filtered: {len(filtered)} chars")
        print(f"--- START FILTERED {i} ---\n{filtered}\n--- END FILTERED {i} ---")

    # 5. Test LLM (Optional - requires Ollama)
    print("\nTesting LLM Connection (Expect failure if Ollama not running)...")
    try:
        slide = await processor.generate_slide_content(chunks[0])
        print("Slide Generation Result:", slide)
    except Exception as e:
        print(f"LLM Test Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
