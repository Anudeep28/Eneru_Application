# Standard library imports
import os
import json
import base64
import logging
import tempfile
import traceback
import warnings

# Audio processing imports
import librosa
import numpy as np
import torch
from transformers import WhisperProcessor, WhisperForConditionalGeneration, pipeline, AutoFeatureExtractor

# Django imports
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views import generic
from client.mixins import TranscribeAppAccessMixin

# Gemini imports
import google.generativeai as genai

# Logging configuration
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('transcription.log')
    ]
)
logger = logging.getLogger(__name__)

# Suppress specific warnings
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

# Lazy initialization to prevent import-time errors
transcriber = None
model = None
feature_extractor = None
tokenizer = None

# Initialize Gemini with the same configuration as chatbot
API_KEY = settings.GEMINI_API_KEY
genai.configure(api_key=API_KEY)

def Proofread(text, proof):
    """Proofread the given text."""
    try:
        error_free_text = proof.proofread(text)
        return error_free_text
    except Exception as e:
        logger.error(f"Proofreading error: {e}")
        return text  # Return original text if proofreading fails

def initialize_transcriber():
    """Initialize the Whisper model with optimal settings."""
    global transcriber, model, feature_extractor, tokenizer
    
    if transcriber is None:
        try:
            # Use the base Whisper model which is more robust
            model_id = "Anudeep28/whisper-Tiny-India_eng"
            
            # Load feature extractor and model explicitly
            feature_extractor = AutoFeatureExtractor.from_pretrained(model_id)
            model = WhisperForConditionalGeneration.from_pretrained(model_id)
            
            # Move model to GPU if available
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model = model.to(device)
            
            # Use tiny.en for tokenizer
            processor = WhisperProcessor.from_pretrained("openai/whisper-tiny.en")
            tokenizer = processor.tokenizer
            
            # Set pad_token_id to be different from eos_token_id
            if tokenizer.pad_token_id == tokenizer.eos_token_id:
                tokenizer.pad_token = '<pad>'
                tokenizer.pad_token_id = tokenizer.convert_tokens_to_ids('<pad>')
            
            # Create pipeline with proper configuration
            transcriber = pipeline(
                "automatic-speech-recognition",
                model=model,
                tokenizer=tokenizer,
                feature_extractor=feature_extractor,
                chunk_length_s=30,
                stride_length_s=5,
                return_timestamps=False,
                device=device,
                framework="pt"
            )
            
            logger.info("Transcriber initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize transcriber: {e}")
            return False
    return True

def process_with_gemini(text):
    """Process transcribed text with Gemini for corrections."""
    try:
        chat = genai.GenerativeModel(model_name='gemini-1.5-flash')
        prompt = f"""As an expert text editor, review and correct the following transcribed text.
        Do not add anything other than corrections. Just correct the text. 
        Focus on:
        Main read through the text and understand the geographic location
        context of the text and and which region the speaker is from
        then do the following:
        1. Correct the spelling of names, locations, places, addresses as per the speaker's background.
        2. Fix number formatting (dates, phone numbers, etc.)
        3. Correct currency mentions
        4. Improve text formatting and punctuation.
        5. Remove any unnecessary words or phrases.
        6. Do not remove any words or text just correct the text.
        7. Just do points 1, 2, 3, 4 without changing whisper output.
        
        Text to process: {text}
        
        Provide only the corrected text without any explanations or markdown."""

        result = chat.generate_content(prompt)
        corrected_text = result.text.strip()
        return corrected_text
    except Exception as e:
        print(f"Gemini processing error: {str(e)}")
        return text  # Return original text if Gemini processing fails

def process_audio_data(audio_data, sample_rate=16000):
    try:
        # Create a temporary file to save the audio data
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
            temp_audio.write(audio_data)
            temp_audio_path = temp_audio.name
        
        try:
            # Load audio file
            y, sr = librosa.load(temp_audio_path, sr=sample_rate, mono=True)
            
            # Normalize audio
            y = librosa.util.normalize(y)
            
            # Initialize transcriber if not already initialized
            if not initialize_transcriber():
                raise Exception("Failed to initialize transcriber")
            
            # Use the transcriber pipeline
            transcribed_text = transcriber(
                {"array": y, "sampling_rate": 16000},
                chunk_length_s=30,
                stride_length_s=5,
                batch_size=8,
                return_timestamps=False,
            )["text"]

            logging.info(f"Transcription result: {transcribed_text}")
            return transcribed_text
            
        except Exception as e:
            logging.error(f"Error processing audio file: {str(e)}", exc_info=True)
            raise
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_audio_path)
            except Exception as cleanup_error:
                logging.error(f"Error cleaning up temp audio file: {str(cleanup_error)}")
    
    except Exception as e:
        logging.error(f"Error in process_audio_data: {str(e)}", exc_info=True)
        raise

class TranscribeIndexView(TranscribeAppAccessMixin, generic.TemplateView):
    template_name = 'transcribe_app/index.html'

class TranscribeAudioView(TranscribeAppAccessMixin, generic.View):
    def post(self, request, *args, **kwargs):
        try:
            # Check if this is a reinitialization request (application/json)
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                if data.get('action') == 'reinitialize':
                    global transcriber, model, feature_extractor, tokenizer
                    transcriber = None
                    model = None
                    feature_extractor = None
                    tokenizer = None
                    success = initialize_transcriber()
                    return JsonResponse({'status': 'success' if success else 'error'})

            # Handle audio file upload (multipart/form-data)
            audio_file = request.FILES.get('audio')
            is_final_chunk = request.POST.get('is_final_chunk', 'false').lower() == 'true'
            
            logging.info(f"Received audio file, size: {audio_file.size if audio_file else 'No file'}")
            
            if not audio_file:
                return JsonResponse({
                    'success': False,
                    'error': 'No audio file provided'
                }, status=400)

            try:
                # Read audio file binary data
                audio_binary = audio_file.read()
                
                # Process audio data
                transcribed_text = process_audio_data(audio_binary, 16000)
                
                # Optional: Process with Gemini for corrections
                corrected_text = process_with_gemini(transcribed_text) if is_final_chunk else transcribed_text
                
                logging.info(f"Final transcription: {corrected_text}")
                
                return JsonResponse({
                    'success': True,
                    'text': corrected_text or transcribed_text  # Use original text if correction fails
                })
                
            except Exception as e:
                logging.error(f"Audio processing error: {str(e)}", exc_info=True)
                return JsonResponse({
                    'success': False,
                    'error': f'Error processing audio: {str(e)}'
                }, status=500)
                
        except Exception as e:
            logger.error(f"Error in transcribe_audio: {e}\n{traceback.format_exc()}")
            return JsonResponse({'error': str(e)}, status=500)
            
        return JsonResponse({
            'success': False,
            'error': 'Invalid request method'
        }, status=405)

class DownloadMarkdownView(TranscribeAppAccessMixin, generic.View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            text = data.get('text', '')
            
            # Create markdown content
            markdown_content = f"# Transcription\n\n{text}\n"
            
            # Create the response with markdown content
            response = HttpResponse(markdown_content, content_type='text/markdown')
            response['Content-Disposition'] = 'attachment; filename="transcription.md"'
            return response
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

class DownloadWordView(TranscribeAppAccessMixin, generic.View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            text = data.get('text', '')
            
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
                from docx import Document
                document = Document()
                document.add_paragraph(text)
                document.save(tmp_file.name)
            
            # Read the temporary file and create response
            with open(tmp_file.name, 'rb') as docx_file:
                response = HttpResponse(docx_file.read(), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                response['Content-Disposition'] = 'attachment; filename="transcription.docx"'
            
            # Clean up the temporary file
            os.unlink(tmp_file.name)
            return response
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

# URL mappings
index = TranscribeIndexView.as_view()
transcribe_audio = csrf_exempt(TranscribeAudioView.as_view())
download_markdown = DownloadMarkdownView.as_view()
download_word = DownloadWordView.as_view()