from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
# from django.utils.decorators import method_decorator
# from asgiref.sync import sync_to_async
import json
import asyncio
import logging
# import logging
from pydantic import BaseModel, Field
from typing import List
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import BM25ContentFilter
from client.mixins import FinancialAnalyzerAccessMixin
# from sentence_transformers import SentenceTransformer
# import numpy as np

# Our own RAG fucntion
from .services.rag_utils import process_website_data, retrieve_similar_chunks, generate_response_with_gemini
from .models import WebsiteData, UserQuery


# Configure logging
logger = logging.getLogger(__name__)

class DialogueMessage(BaseModel):
    speaker: str = Field(..., description="Name of the Participant")
    message: str = Field(..., description="The words spoken by this Participant")
    sequence: int = Field(..., description="Order in the conversation")

class ConversationStructure(BaseModel):
    company: str = Field(..., description="Company Name")
    year: str = Field(..., description="Year of the conversation")
    quarter: str = Field(..., description="which Quarter of year was the conversation recorded")
    title: str = Field(..., description="Title of the conversation")
    participants: List[str] = Field(..., description="List of Participants in the conversation")
    role: List[str] = Field(..., description="Roles of participants in the conversation (Guest, CEO, CTO, etc.)")
    dialogue: List[DialogueMessage] = Field(..., description="List of dialogues/words spoken by the Participants")
    relationships: List[str] = Field(..., description="Relationships between Participants")
    summary: str = Field(..., description="Brief Summary of the conversations")
    topics: List[str] = Field(..., description="Main topics discussed")

async def extract_conversation(url: str, api_token: str):

    # api_provider = "gemini/gemini-1.5-flash"
    # api_provider = "together/deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free"
    api_provider = "gemini/gemini-2.0-flash"

    browser_config = BrowserConfig(
        headless=True,
        text_mode=True,
        java_script_enabled=True,
        # viewport_width=1920, 
        # viewport_height=1080
    )

    # bm25 filter before making the mnarkdown from html
    bm25_filter = BM25ContentFilter(
        # user_query="Earnings transcript containing Participants with their Roles and Questions and answers, also participants spoken dialogue and conversation structure",
        # bm25_threshold=1.2
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

    # Extraction Strategy
    llm_extraction_strategy = LLMExtractionStrategy(
            provider=api_provider,
            api_token=api_token,
            schema=ConversationStructure.model_json_schema(),
            extraction_type="schema",
            chunk_token_threshold=2048,
            overlap_rate=0.1,
            # word_token_rate=0.75,
            apply_chunking=True,
            # verbose=True,
            instruction="""Given the company earnings call transcript, 
            extract and structure the information in order (ex. presentation/conference call session, then Question
            and Answers session) with the following format:
        {
            "company": "Company Name",
            "year": "Year of the conversation",
            "quarter": "which Quarter of year was the conversation recorded",
            "title": "Title of the earnings call",
            "participants": [
                {"name": "Participant Name"}
            ],
            "role": [
                {"role": "The Participant Role (CEO, CTO, Worker etc.)"}
            ],
            "dialogue": [
                {
                    "speaker": "Present Participant Name",
                    "message": "Exact dialogue by the participant",
                    "sequence": 1
                }
            ],
            "relationships": ["List of Participants and their relationships"],
            "summary": "Brief summary of the conversations",
            "topics": ["List of main topics discussed"]
        }

        Important:
        - Extract ALL dialogue messages in chronological order
        - Include Participant names and roles exactly as mentioned
        - Maintain accurate sequence numbers and order
        - Ensure the output is a valid JSON object
        """,
            input_format="fit_markdown",
            extra_args={
                "temperature": 0.1,
                #"top_p": 0.9,
                "max_tokens": 4096,
                "chunk_merge_strategy": "ordered_append",
                "stream": False,
            },
        )

    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        # wait_for="css:#site-content",
        excluded_tags=['script', 'style', 'meta', 'link', 'noscript', 'iframe'],
        exclude_external_images=True,
        exclude_external_links=True,
        exclude_social_media_links=True,
        markdown_generator=md_generator,
        # exclude_external_links=True,
        # exclude_external_images=True,
        check_robots_txt=True,
        page_timeout=60000,
        wait_until="networkidle",
        # simulate_user=True,
        # css_selector="#site-content",
        # scraping_strategy=LXMLWebScrapingStrategy(),
        extraction_strategy=llm_extraction_strategy,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        try:
            result = await crawler.arun(url=url, config=crawler_config)
            # print("fit markdown result :",result.fit_markdown)
            # Store the original crawler result for later use in processing
            crawler_result = result
            
            # The process_website_data function will be called later in the ConversationView

            # print("Fit Markdown Results :",result.fit_markdown)
            if not result.extracted_content:
                return {
                    'error': True,
                    'message': 'No content was extracted from the webpage',
                    'crawler_result': None
                }
            content = result.extracted_content
            # print("Extracted content Results :",content[0])
            # print("length of the chunk result :", len(content))
            # full_content = " ".join([
            #     str(chunk) for chunk in result.extracted_content
            # ]) 
            llm_extraction_strategy.show_usage()
            # if result.success:
            #     with open("extraction_result.json", "w", encoding="utf-8") as f:
            #         json.dump(content, f, ensure_ascii=False, indent=2)
            
            if isinstance(content, str):
                try:
                    parsed_content = json.loads(content)
                    if isinstance(parsed_content, list):
                        # Initialize merged structure
                        merged_content = {
                            "company": "",
                            "year": "",
                            "quarter": "",
                            "title": "",
                            "participants": [],
                            "role": [],
                            "dialogue": [],
                            "relationships": [],
                            "summary": "",
                            "topics": []
                        }
                        
                        for chunk in parsed_content:
                            # No need for json.loads here since it's already parsed
                            if isinstance(chunk, dict):
                                # Company name
                                if not merged_content["company"] and "company" in chunk:
                                    merged_content["company"] = chunk["company"]
                                # year
                                if not merged_content["year"] and "year" in chunk:
                                    merged_content["year"] = chunk["year"]
                                # quarter
                                if not merged_content["quarter"] and "quarter" in chunk:
                                    merged_content["quarter"] = chunk["quarter"]
                                # Merge the data
                                if not merged_content["title"] and "title" in chunk:
                                    merged_content["title"] = chunk["title"]
                                
                                # Merge participants and roles (avoid duplicates)
                                if "participants" in chunk:
                                    merged_content["participants"].extend(p for p in chunk["participants"] 
                                                                    if p not in merged_content["participants"])
                                if "role" in chunk:
                                    merged_content["role"].extend(r for r in chunk["role"] 
                                                            if r not in merged_content["role"])
                                
                                # Append dialogue messages in order
                                if "dialogue" in chunk:
                                    merged_content["dialogue"].extend(chunk["dialogue"])
                                
                                # Merge relationships (avoid duplicates)
                                if "relationships" in chunk:
                                    merged_content["relationships"].extend(r for r in chunk["relationships"] 
                                                                        if r not in merged_content["relationships"])
                                
                                # Combine summaries
                                if "summary" in chunk:
                                    merged_content["summary"] += " " + chunk["summary"] if merged_content["summary"] else chunk["summary"]
                                
                                # Merge topics (avoid duplicates)
                                if "topics" in chunk:
                                    merged_content["topics"].extend(t for t in chunk["topics"] 
                                                                if t not in merged_content["topics"])
                        
                        # print("Merged content Results:", merged_content)
                        # Add the crawler result to the merged content for later use
                        merged_content['crawler_result'] = crawler_result
                        return merged_content
                    else:
                        # If it's not a list, return the parsed content
                        parsed_content['crawler_result'] = crawler_result
                        return parsed_content
                        
                except json.JSONDecodeError:
                    return {
                        'error': True,
                        'message': 'Failed to parse the extracted content',
                        'crawler_result': None
                    }
            else:
                return {
                    'error': True,
                    'message': 'Unexpected content format',
                    'crawler_result': None
                }
        except Exception as e:
            return {
                'error': True,
                'message': f'An error occurred while extracting the content: {str(e)}',
                'crawler_result': None
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
            # api_token = settings.TOGETHER_API_KEY
            
            # Run the async function in a synchronous context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(extract_conversation(url, api_token))
            finally:
                loop.close()
            
            # print("Result before display to the frontend :",result)
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
            
            # Handle case where result is a dict with error
            if isinstance(result, dict):
                if result.get('error'):
                    return JsonResponse({
                        'status': 'error',
                        'message': result.get('message', 'Failed to analyze content')
                    })
                
                # Get the crawler result from the merged content
                crawler_result = result.get('crawler_result')
                
                # Process website data and store in database if crawler_result exists
                if crawler_result:
                    try:
                        # Pass the crawler result, URL, and user ID to process_website_data
                        website_data = process_website_data(
                            website_data=result,
                            url=url,
                            user_id=request.user.id
                        )
                        
                        logger.info(f"Successfully processed website data for URL: {url}")
                    except Exception as e:
                        logger.error(f"Error processing website data: {str(e)}")
                        # Continue with the response even if there's an error with storing data
                else:
                    logger.warning(f"No crawler result available for processing URL: {url}")
                
                # Remove crawler_result from the response data to avoid sending large objects
                if 'crawler_result' in result:
                    del result['crawler_result']
                
                # If it's a valid result dict (with our conversation structure)
                # Ensure we have the expected data structure
                response_data = {
                    'status': 'success',
                    'data': {
                        'company': result.get('company', 'No Company Name Available'),
                        'year': result.get('year', 'No Year Available'),
                        'quarter': result.get('quarter', 'No Quarter Available'),
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

            # If we get here, something unexpected happened
            return JsonResponse({
                'status': 'error',
                'message': 'Unexpected response format'
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })

class QueryView(LoginRequiredMixin, FinancialAnalyzerAccessMixin, View):
    def post(self, request):
        try:
            # Get the user query and URL from the form
            user_query = request.POST.get('query')
            url = request.POST.get('url')
            
            if not user_query or not url:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Both query and URL are required'
                })
            
            # Find the website data for this URL
            website_data = WebsiteData.objects.filter(url=url, user_id=request.user.id).first()
            
            if not website_data:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No data found for this URL. Please analyze the content first.'
                })
            
            # Retrieve the top 3 most similar chunks using RAG
            similar_chunks = retrieve_similar_chunks(user_query, website_data.id)
            
            # Generate a response using Gemini based on the query and retrieved context
            response = generate_response_with_gemini(user_query, similar_chunks)
            
            # Store the query and response
            user_query_obj = UserQuery.objects.create(
                user=request.user,
                query=user_query,
                response=response,
                website=website_data
            )
            
            return JsonResponse({
                'status': 'success',
                'response': user_query_obj.response,
                'message': 'Query processed successfully'
            })
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
