from django.shortcuts import render
from django.views import View
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from asgiref.sync import sync_to_async
import json
import asyncio
# import logging
from pydantic import BaseModel, Field
from typing import List
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode, LXMLWebScrapingStrategy
from crawl4ai.extraction_strategy import LLMExtractionStrategy, JsonCssExtractionStrategy
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import BM25ContentFilter
from client.mixins import FinancialAnalyzerAccessMixin


# Configure logging
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class DialogueMessage(BaseModel):
    speaker: str = Field(..., description="Name of the Participant")
    message: str = Field(..., description="The message/presentation/dialogue spoken by this Participant")
    sequence: int = Field(..., description="Order in the conversation")

class ConversationStructure(BaseModel):
    title: str = Field(..., description="Title of the conversation")
    participants: List[str] = Field(..., description="List of Participants in the conversation")
    role: List[str] = Field(..., description="Roles of participants in the conversation (CEO, CTO, etc.)")
    dialogue: List[DialogueMessage] = Field(..., description="List of presentation/dialogue/messages by the Participants")
    relationships: List[str] = Field(..., description="Relationships between Participants")
    summary: str = Field(..., description="Brief Summary of the conversations")
    topics: List[str] = Field(..., description="Main topics discussed")

async def extract_conversation(url: str, api_token: str):
    browser_config = BrowserConfig(
        headless=True,
        text_mode=True,
        java_script_enabled=True,
        # viewport_width=1920, 
        # viewport_height=1080
    )

    # bm25 filter before making the mnarkdown from html
    bm25_filter = BM25ContentFilter(
        user_query="Earnings call transcript content (Presentations with Questions and answers) and participants present with conversation structure",
        bm25_threshold=1.0
    )

    # Mardown generator for fit_markdown
    md_generator = DefaultMarkdownGenerator(
        content_filter=bm25_filter,
        options={
            "ignore_links": True,
            "ignore_images": True,
            "escape_html": True,
            "skip_internal_links": True,
            "body_width": 80,
        }
    )

    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.ENABLED,
        # wait_for="css:#site-content",
        excluded_tags=['script', 'style', 'meta', 'link', 'noscript', 'iframe'],
        exclude_external_images=True,
        exclude_external_links=True,
        exclude_social_media_links=True,
        markdown_generator=md_generator,
        # exclude_external_links=True,
        # exclude_external_images=True,
        check_robots_txt=True,
        page_timeout=80000,
        wait_until="networkidle",
        # simulate_user=True,
        # css_selector="#site-content",
        scraping_strategy=LXMLWebScrapingStrategy(),
        extraction_strategy=LLMExtractionStrategy(
            provider="gemini/gemini-1.5-flash",
            api_token=api_token,
            schema=ConversationStructure.model_json_schema(),
            extraction_type="schema",
            chunk_token_threshold=2048,
            overlap_rate=0.4,
            word_token_rate=0.75,
            apply_chunking=True,
            # verbose=True,
            instruction="""Given the earnings call transcript markdown content, 
            extract and structure the information into a valid JSON object with the following format:
        {
            "title": "Title of the earnings call",
            "participants": [
                {"name": "Corporate Participant Name"}
            ],
            "role": [
                {"role": "The Corporate Participant Role (CEO, CTO, Worker etc.)"}
            ],
            "dialogue": [
                {
                    "speaker": "participant Name",
                    "message": "Exact message/presentation/dialogue by the participant",
                    "sequence": 1
                }
            ],
            "relationships": ["List of Participants and their relationships"],
            "summary": "Brief summary of the conversations",
            "topics": ["List of main topics discussed"]
        }

        Important:
        - start extracting when the chunk contains MENUMENU text in it
        - Extract ALL dialogue messages in chronological order
        - Include Participant names and roles exactly as mentioned
        - Maintain accurate sequence numbers
        - Ensure the output is a valid JSON object
        """,
            input_format="fit_markdown",
            extra_args={
                "temperature": 0.1,
                #"top_p": 0.9,
                "max_tokens": 4096,
                # "chunk_merge_strategy": "append",
                "stream": False,
            },
        ),
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        try:
            result = await crawler.arun(url=url, config=crawler_config)
            print("length of the chunk result :",len(result.fit_markdown))
            print("Fit Markdown Results :",result.fit_markdown)
            if not result.extracted_content:
                return {
                    'error': True,
                    'message': 'No content was extracted from the webpage'
                }
            content = result.extracted_content
            print("Extracted content Results :",content)
            if isinstance(content, str):
                try:
                    content = json.loads(content)
                    print("json load :",content)
                except json.JSONDecodeError:
                    return {
                        'error': True,
                        'message': 'Failed to parse the extracted content'
                    }
            return content
        except Exception as e:
            return {
                'error': True,
                'message': f'Error during crawling: {str(e)}'
            }

class ConversationView(LoginRequiredMixin, FinancialAnalyzerAccessMixin, View):
    def get(self, request):
        return render(request, 'financial_analyzer/stock_input.html')

    def post(self, request):
        try:
            url = request.POST.get('url')
            
            if not url:
                return JsonResponse({
                    'status': 'error',
                    'message': 'URL is required'
                })

            api_token = settings.GEMINI_API_KEY
            
            # Run the async function in a synchronous context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(extract_conversation(url, api_token))
            finally:
                loop.close()
            
            # Check if result is None or empty
            if not result:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No content was extracted from the URL'
                })
            
            # Handle case where result is a string (error message)
            if isinstance(result, str):
                return JsonResponse({
                    'status': 'error',
                    'message': result
                })
            
            # Handle case where result is a list
            if isinstance(result, list):
                if not result:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'No content was extracted'
                    })
                
                result = result[0]  # Take the first item if it's a list
            
            # Handle case where result is a dict with error
            if isinstance(result, dict) and result.get('error'):
                return JsonResponse({
                    'status': 'error',
                    'message': result.get('message', 'Failed to analyze content')
                })
            
            # Ensure we have the expected data structure
            response_data = {
                'status': 'success',
                'data': {
                    'title': result.get('title', 'No Title Available'),
                    'participants': result.get('participants', []),
                    'role': result.get('role', []),
                    'dialogue': result.get('dialogue', []),
                    'relationships': result.get('relationships', []),
                    'summary': result.get('summary', 'No summary available'),
                    'topics': result.get('topics', [])
                }
            }
            
            return JsonResponse(response_data)
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
