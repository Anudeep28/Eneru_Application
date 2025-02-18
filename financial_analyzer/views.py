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
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from client.mixins import FinancialAnalyzerAccessMixin


# Configure logging
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class DialogueMessage(BaseModel):
    speaker: str = Field(..., description="Name of the speaker")
    message: str = Field(..., description="The message spoken by this speaker")
    sequence: int = Field(..., description="Order in the conversation")

class ConversationStructure(BaseModel):
    title: str = Field(..., description="Title of the conversation")
    participants: List[str] = Field(..., description="List of participants in the conversation")
    role: List[str] = Field(..., description="Roles of participants in the conversation (CEO, CTO, etc.)")
    dialogue: List[DialogueMessage] = Field(..., description="List of dialogue messages by the speakers")
    relationships: List[str] = Field(..., description="Relationships between speakers")
    summary: str = Field(..., description="Summary of the conversation")
    topics: List[str] = Field(..., description="Main topics discussed")

async def extract_conversation(url: str, api_token: str):
    browser_config = BrowserConfig(
        headless=True,
        # text_mode=True,
        java_script_enabled=True
    )

    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.ENABLED,
        page_timeout=80000,
        # wait_for="css:#site-content",
        excluded_tags=['script', 'style', 'meta', 'link', 'noscript', 'iframe'],
        exclude_external_links=True,
        exclude_external_images=True,
        check_robots_txt=True,
        # css_selector="#site-content",
        scraping_strategy=LXMLWebScrapingStrategy(),
        extraction_strategy=LLMExtractionStrategy(
            provider="gemini/gemini-1.5-flash",
            api_token=api_token,
            schema=ConversationStructure.model_json_schema(),
            extraction_type="schema",
            chunk_token_threshold=2000,
            overlap_rate=0.2,
            word_token_rate=0.75,
            apply_chunking=True,
            # verbose=True,
            instruction="""Given the transcript markdown content, extract and structure the information into a valid JSON object with the following format:
        {
            "title": "Title of the earnings call",
            "participants": [
                {"name": "Person Name"}
            ],
            "role": [
                {"role": "Person Role"}
            ],
            "dialogue": [
                {
                    "speaker": "Speaker Name",
                    "message": "Exact message content",
                    "sequence": 1
                }
            ],
            "relationships": ["List of speaker and their relationships"],
            "summary": "Brief summary of the conversation",
            "topics": ["List of main topics discussed"]
        }

        Important:
        - Extract ALL dialogue messages in chronological order
        - Include speaker names and roles exactly as mentioned
        - Maintain accurate sequence numbers
        - Ensure the output is a valid JSON object
        """,
            input_format="markdown",
            extra_args={
                "temperature": 0.1,
                #"top_p": 0.9,
                "max_tokens": 4000,
                #"chunk_merge_strategy": "append",
                "stream": False,
            },
        ),
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        try:
            result = await crawler.arun(url=url, config=crawler_config)
            print(result.markdown)
            if not result.extracted_content:
                return {
                    'error': True,
                    'message': 'No content was extracted from the webpage'
                }
            content = result.extracted_content
            print("Extracted content:",content)
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
