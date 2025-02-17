from django.shortcuts import render
from django.views import View
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from asgiref.sync import sync_to_async
import json
import asyncio
from pydantic import BaseModel, Field
from typing import List
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode, LXMLWebScrapingStrategy
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from client.mixins import FinancialAnalyzerAccessMixin


class DialogueMessage(BaseModel):
    speaker: str = Field(..., description="Name of the speaker")
    message: str = Field(..., description="The message spoken by this speaker")
    sequence: int = Field(..., description="Order in the conversation")

class ConversationStructure(BaseModel):
    title: str = Field(..., description="Title of the conversation")
    participants: List[str] = Field(..., description="List of participants")
    dialogue: List[DialogueMessage] = Field(..., description="List of dialogue messages")
    relationships: List[str] = Field(..., description="Relationships between speakers")
    summary: str = Field(..., description="Summary of the conversation")
    topics: List[str] = Field(..., description="Main topics discussed")

async def extract_conversation(url: str, api_token: str):
    browser_config = BrowserConfig(
        headless=True,
        text_mode=True,
        java_script_enabled=True
    )

    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.ENABLED,
        page_timeout=120000,
        excluded_tags=['script', 'style', 'meta', 'link', 'noscript', 'iframe'],
        exclude_external_links=True,
        exclude_external_images=True,
        check_robots_txt=True,
        css_selector="body",
        scraping_strategy=LXMLWebScrapingStrategy(),
        extraction_strategy=LLMExtractionStrategy(
            provider="gemini/gemini-1.5-flash",
            api_token=api_token,
            schema=ConversationStructure.model_json_schema(),
            extraction_type="schema",
            chunk_token_threshold=8000,
            overlap_rate=0.2,
            word_token_rate=0.75,
            apply_chunking=True,
            verbose=True,
            instruction="""Extract the dialogue from this transcript. Focus on:
            1. Title: Create a descriptive title
            2. Participants: List all speakers
            3. Relationships: Note each speaker's role or relationship to others
            4. Dialogue: Extract each message in sequence, including:
               - Speaker name
               - Exact message content
               - Sequence number
            5. Summary: Provide a concise summary of key points
            6. Topics: List main discussion topics

            Important:
            - Include ALL dialogue messages
            - Keep messages in chronological order
            - Don't skip any parts of the conversation
            - Maintain accurate sequence numbers
            - Ignore website navigation/footer content""",
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
            result = await crawler.arun(url=url, config=crawler_config)
            
            if not result.extracted_content:
                return {
                    'error': True,
                    'message': 'No content was extracted from the webpage'
                }
                
            content = result.extracted_content
            if isinstance(content, str):
                try:
                    content = json.loads(content)
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
