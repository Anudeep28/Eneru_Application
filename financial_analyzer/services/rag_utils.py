from typing import List, Dict
import logging
from langchain.text_splitter import MarkdownTextSplitter
from sentence_transformers import SentenceTransformer
from ..models import WebsiteData, DocumentChunk

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

def process_website_data(website_data: WebsiteData) -> None:
    """
    Process website data: split markdown and create embeddings
    For now, just print chunks for verification
    """
    try:
        # Split markdown into chunks
        chunks = split_markdown_into_chunks(website_data)
        
        # Print first few chunks for verification
        print("\nFirst 3 chunks of the document:")
        for i, chunk in enumerate(chunks[:3]):
            print(f"\nChunk {i+1}:")
            print("-" * 50)
            print(chunk)
            print("-" * 50)
            
        logger.info(f"Successfully processed website data") #{website_data.company}")
        embeddings = create_embeddings(chunks)
        print("\nFirst 1 embedding:")
        print(embeddings[0])
        
    except Exception as e:
        logger.error(f"Error processing website data: {str(e)}")
        raise