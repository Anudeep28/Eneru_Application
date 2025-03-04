from typing import List, Dict
import logging
from langchain.text_splitter import MarkdownTextSplitter
from sentence_transformers import SentenceTransformer
from ..models import WebsiteData, DocumentChunk
from django.db import transaction
import numpy as np
import json
from pgvector.django import L2Distance
import google.generativeai as genai
from django.conf import settings

logger = logging.getLogger(__name__)

def split_markdown_into_chunks(markdown_text: str, 
                               chunk_size: int = 1024, 
                               chunk_overlap: int = 50) -> List[str]:
    """
    Split markdown text into chunks using LangChain's MarkdownTextSplitter
    """
    try:
        text_splitter = MarkdownTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        chunks = text_splitter.split_text(markdown_text)
        logger.info(f"Successfully split markdown into {len(chunks)} chunks")
        return chunks
    except Exception as e:
        logger.error(f"Error splitting markdown: {str(e)}")
        raise

def create_embeddings(text_chunks: List[str], model_name: str = 'all-MiniLM-L6-v2') -> List[List[float]]:
    """
    Create embeddings for text chunks using SentenceTransformers
    """
    try:
        model = SentenceTransformer(model_name)
        embeddings = model.encode(text_chunks)
        logger.info(f"Successfully created embeddings for {len(text_chunks)} chunks")
        return embeddings.tolist()
    except Exception as e:
        logger.error(f"Error creating embeddings: {str(e)}")
        raise

def process_website_data(website_data, url: str, user_id: int) -> None:
    """
    Process website data: split markdown and create embeddings
    Checks if the website has been scraped before by the user
    If new, stores website data, chunks, and embeddings in the database
    
    Args:
        website_data: The dictionary containing crawler_result and extracted data
        url: The URL of the website being processed
        user_id: The ID of the user who initiated the scraping
    """
    try:
        # Check if this website has been scraped before by the user
        existing_website = WebsiteData.objects.filter(url=url, user_id=user_id).first()
        
        if existing_website:
            logger.info(f"Website {url} has already been scraped by this user. Using existing data.")
            return existing_website
        
        # Extract necessary data from the crawler result
        result = website_data.get('crawler_result')
        markdown_content = result.fit_markdown
        
        # The extracted_content is already a dictionary, no need to parse it
        # Remove the crawler_result to make it JSON serializable
        serializable_content = website_data.copy()
        if 'crawler_result' in serializable_content:
            del serializable_content['crawler_result']
            
        company = website_data.get('company', 'Unknown')
        year = website_data.get('year', 0)
        try:
            year = int(year)
        except (ValueError, TypeError):
            year = 0
            
        quarter = website_data.get('quarter', 'Q1')
        title = website_data.get('title', 'No Title')
        
        # Create a new WebsiteData entry
        with transaction.atomic():
            # Create website data record
            new_website = WebsiteData.objects.create(
                user_id=user_id,
                url=url,
                title=title,
                company=company,
                year=year,
                quarter=quarter,
                extracted_content=serializable_content,
                fit_markdown=markdown_content
            )
            
            # Split markdown into chunks
            chunks = split_markdown_into_chunks(markdown_content)
            
            # Create embeddings for chunks
            embeddings = create_embeddings(chunks)
            
            # Store chunks and embeddings in the database
            chunk_objects = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_objects.append(DocumentChunk(
                    website=new_website,
                    sequence=i,
                    content=chunk,
                    embedding=np.array(embedding)
                ))
            
            # Bulk create chunks
            DocumentChunk.objects.bulk_create(chunk_objects)
            
            logger.info(f"Successfully processed and stored website data for {company} ({year} Q{quarter})")
            
            # # Print first few chunks for verification (debug only)
            # print("\nFirst 3 chunks of the document:")
            # for i, chunk in enumerate(chunks[:3]):
            #     print(f"\nChunk {i+1}:")
            #     print("-" * 50)
            #     print(chunk)
            #     print("-" * 50)
                
            # # Print first embedding for verification (debug only)
            # print("\nFirst 1 embedding:")
            # print(embeddings[0])
            
            return new_website
            
    except Exception as e:
        logger.error(f"Error processing website data: {str(e)}")
        raise

def retrieve_similar_chunks(query: str, website_id, top_k: int = 3) -> List[DocumentChunk]:
    """
    Retrieve the top k most similar chunks for a given query
    
    Args:
        query: The user query
        website_id: The ID of the website to search within
        top_k: Number of chunks to retrieve (default: 3)
        
    Returns:
        List of DocumentChunk objects that are most similar to the query
    """
    try:
        # Create embedding for the query
        model = SentenceTransformer('all-MiniLM-L6-v2')
        query_embedding = np.array(model.encode([query])[0])
        
        # Retrieve the most similar chunks using pgvector
        similar_chunks = DocumentChunk.objects.filter(
            website_id=website_id
        ).order_by(
            L2Distance('embedding', query_embedding)
        )[:top_k]
        
        logger.info(f"Retrieved {len(similar_chunks)} similar chunks for query: {query}")
        return similar_chunks
    except Exception as e:
        logger.error(f"Error retrieving similar chunks: {str(e)}")
        raise

def generate_response_with_gemini(query: str, context_chunks: List[DocumentChunk]) -> str:
    """
    Generate a response using Gemini model based on the user query and retrieved context chunks
    
    Args:
        query: The user query
        context_chunks: List of DocumentChunk objects containing relevant context
        
    Returns:
        Generated response from Gemini
    """
    try:
        # Configure Gemini
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Prepare context from chunks
        context_text = "\n\n".join([chunk.content for chunk in context_chunks])
        
        # Create prompt with query and context
        prompt = f"""
        You are a helpful financial analyst assistant. Answer the following question based ONLY on the provided context.
        If you don't know the answer or if the context doesn't contain relevant information, say so.
        
        CONTEXT:
        {context_text}
        
        QUESTION:
        {query}
        
        ANSWER:
        """
        
        # Generate response
        response = model.generate_content(prompt)
        
        if response.text:
            logger.info(f"Successfully generated response for query: {query}")
            return response.text
        else:
            logger.warning(f"Empty response from Gemini for query: {query}")
            return "I couldn't generate a response based on the provided information. Please try a different question."
    
    except Exception as e:
        logger.error(f"Error generating response with Gemini: {str(e)}")
        return f"An error occurred while generating the response: {str(e)}"