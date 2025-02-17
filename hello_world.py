############ Extract schema using LLM ################### **Working**
import os
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)
import json
import asyncio
from pydantic import BaseModel, Field
from typing import Dict, List
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode, LXMLWebScrapingStrategy
from crawl4ai.extraction_strategy import LLMExtractionStrategy

class DialogueMessage(BaseModel):
    speaker: str = Field(..., description="Name of the speaker")
    message: str = Field(..., description="The message spoken by this speaker")
    sequence: int = Field(..., description="The order in which this message appeared in the conversation")
    
class ConversationStructure(BaseModel):
    title: str = Field(..., description="A descriptive title for the conversation based on its content")
    participants: List[str] = Field(..., description="List of all speakers involved in the conversation")
    relationships: List[str] = Field(..., description="Relationships between speakers, such as father-son, friend-friend, etc.")
    dialogue: List[DialogueMessage] = Field(..., description="The complete conversation in chronological order")
    summary: str = Field(..., description="A comprehensive summary of the conversation")
    topics: List[str] = Field(..., description="Main topics or themes discussed in the conversation")

async def extract_structured_data_using_llm(
    provider: str, api_token: str = None, extra_headers: Dict[str, str] = None
):
    print(f"\n--- Extracting Structured Data with {provider} ---")

    if api_token is None and provider != "ollama":
        print(f"API token is required for {provider}. Skipping this example.")
        return

    browser_config = BrowserConfig(
        headless=True,
        text_mode=True,
        javascript_enabled=True,
        wait_for_network_idle=True
    )

    extra_args = {"temperature": 0, "top_p": 0.9, "max_tokens": 4000}
    if extra_headers:
        extra_args["extra_headers"] = extra_headers

    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        page_timeout=120000,  # Increased timeout
        excluded_tags=['script', 'style', 'meta', 'link', 'noscript', 'iframe'],
        exclude_external_links=True,
        exclude_external_images=True,
        check_robots_txt=True,
        css_selector="body",  # Get the entire body content
        scraping_strategy=LXMLWebScrapingStrategy(),
        extraction_strategy=LLMExtractionStrategy(
            provider=provider,
            api_token=api_token,
            schema=ConversationStructure.model_json_schema(),
            extraction_type="schema",
            chunk_token_threshold=8000,
            overlap_rate=0.2,
            word_token_rate=0.75,
            apply_chunking=True,
            verbose=True,
            instruction="""Extract the dialogue from this earnings call transcript. Focus on:

            1. Title: Create a descriptive title that includes the company name and main topic
            2. Participants: List all speakers (executives and analysts)
            3. Relationships: Note each speaker's role (CEO, CFO, Analyst, etc.)
            4. Dialogue: Extract each message in sequence, including:
               - Speaker name and role
               - Exact message content
               - Sequence number
            5. Summary: Provide a concise summary of key points
            6. Topics: List main discussion topics

            Important:
            - Include ALL dialogue messages
            - Keep messages in chronological order
            - Don't skip any parts of the conversation
            - Maintain accurate sequence numbers
            - Ignore website navigation/footer content
            
            Format the output as a valid JSON object with these fields:
            {
                "title": "string",
                "participants": ["string"],
                "relationships": ["string"],
                "dialogue": [
                    {
                        "speaker": "string",
                        "message": "string",
                        "sequence": number
                    }
                ],
                "summary": "string",
                "topics": ["string"]
            }""",
            extra_args={
                "temperature": 0,
                "top_p": 0.9,
                "max_tokens": 8000,
                "chunk_merge_strategy": "append",
                "stream": False,
            },
        ),
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        try:
            # First, try to get the raw HTML
            result = await crawler.arun(
                # url="https://www.fool.com/earnings/call-transcripts/2025/02/13/zebra-technologies-zbra-q4-2024-earnings-call-tran/",
                url="https://dialoguefrog.com/practice-english-conversation-planning-a-trip-100/",
                config=crawler_config
            )
            
            # Print the raw HTML first to check what we're getting
            print("\nRaw HTML Content (first 1000 chars):")
            print(result.cleaned_html[:1000] if result.cleaned_html else "No HTML content")
            
            # Save both the raw HTML and extracted content
            with open("raw_content.txt", "w", encoding="utf-8") as file:
                file.write(result.cleaned_html if result.cleaned_html else "No content")
                
            # Try to parse the content if it's a string
            content_to_save = None
            if result.extracted_content:
                print("\nExtracted Content Structure:")
                print(f"Content type: {type(result.extracted_content)}")
                
                print("\nExtracted Content:")
                print(result.extracted_content)
                
                if isinstance(result.extracted_content, str):
                    try:
                        parsed_content = json.loads(result.extracted_content)
                        print("\nParsed Content:")
                        print(json.dumps(parsed_content, indent=2))
                        content_to_save = parsed_content
                    except json.JSONDecodeError as e:
                        print(f"Error parsing content as JSON: {str(e)}")
                        content_to_save = result.extracted_content
                else:
                    content_to_save = result.extracted_content
            else:
                print("Warning: No extracted content!")
                content_to_save = {
                    "title": "Error: No Content",
                    "participants": [],
                    "relationships": [],
                    "dialogue": [],
                    "summary": "Failed to extract content from the webpage",
                    "topics": [],
                    "error": True
                }
            
            # Save the content
            with open("extracted_content.json", "w", encoding="utf-8") as file:
                if isinstance(content_to_save, str):
                    file.write(content_to_save)
                else:
                    json.dump(content_to_save, file, indent=2, ensure_ascii=False)
                    
            # Enhanced debug information
            print("\nDebug Information:")
            print(f"Total HTML length: {len(result.cleaned_html) if result.cleaned_html else 0}")
            if hasattr(result, 'chunks'):
                print(f"Number of chunks processed: {len(result.chunks)}")
            if hasattr(result, 'extraction_error'):
                print(f"Extraction error: {result.extraction_error}")
            
        except Exception as e:
            print(f"Error during crawling: {str(e)}")
            raise

if __name__ == "__main__":
    # Use ollama with llama3.3
    # asyncio.run(
    #     extract_structured_data_using_llm(
    #         provider="ollama/llama3.3", api_token="no-token"
    #     )
    # )

    asyncio.run(
        extract_structured_data_using_llm(
            provider="gemini/gemini-1.5-flash", api_token=os.getenv("GEMINI_API_KEY")
        )
    )


############# data extraction working with gemini 1.5 flash ################ **Working**

############## Dynamic Content Example #####################
