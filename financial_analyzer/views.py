from django.shortcuts import render
from django.views import View
from django.http import JsonResponse, HttpResponse
from django.conf import settings
import json
from pydantic import BaseModel, Field
from typing import List
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode, LXMLWebScrapingStrategy
from crawl4ai.extraction_strategy import LLMExtractionStrategy

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
            
            # Handle case where content is a list
            if isinstance(content, list):
                if not content:
                    return {
                        'error': True,
                        'message': 'No content was extracted'
                    }
                content = content[0]  # Take the first item if it's a list
            
            return {
                'error': False,
                'data': content
            }
            
        except Exception as e:
            return {
                'error': True,
                'message': f'Error during crawling: {str(e)}'
            }

class ConversationView(View):
    async def get(self, request):
        from asgiref.sync import sync_to_async
        from django.template.loader import render_to_string
        
        template = await sync_to_async(render_to_string)(
            'financial_analyzer/stock_input.html',
            {'request': request}
        )
        from django.http import HttpResponse
        return HttpResponse(template)
    
    async def post(self, request):
        from asgiref.sync import sync_to_async
        
        url = await sync_to_async(request.POST.get)('url')
        if not url:
            return JsonResponse({
                'status': 'error',
                'message': 'URL is required'
            })
        
        api_token = await sync_to_async(lambda: settings.GEMINI_API_KEY)()
        if not api_token:
            return JsonResponse({
                'status': 'error',
                'message': 'API token not configured'
            })
        
        try:
            result = await extract_conversation(url, api_token)
            if result.get('error'):
                return JsonResponse({
                    'status': 'error',
                    'message': result.get('message', 'Failed to extract content')
                })
            
            return JsonResponse({
                'status': 'success',
                'data': result.get('data', {})
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
