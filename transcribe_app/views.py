from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from transformers import (
    WhisperProcessor, 
    WhisperForConditionalGeneration, 
    AutoFeatureExtractor,
    pipeline
)
import tempfile
import os
import base64
import json
import numpy as np
import io
import torch
from datasets import Audio, Dataset, Features, Value
import warnings
import librosa
import google.generativeai as genai
from django.conf import settings

# Suppress specific warnings
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

# Lazy initialization to prevent import-time errors
transcriber = None
processor = None
model = None

# Initialize Gemini with the same configuration as chatbot
API_KEY = settings.GEMINI_API_KEY
genai.configure(api_key=API_KEY)

def initialize_transcriber():
    global transcriber, processor, model
    if transcriber is None:
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
        
        # Set pad_token_id to be different from eos_token_id
        tokenizer = processor.tokenizer
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

def process_with_gemini(text):
    """Process transcribed text with Gemini for corrections."""
    try:
        chat = genai.GenerativeModel(model_name='gemini-1.5-flash')
        prompt = f"""As an expert text editor, review and correct the following transcribed text.
        Do not add anything other than corrections. Just correct the text. 
        Focus on:
        Main read through the text and understand the context of the text and
        then do the following:
        1. Correct spelling of names, locations, places, addresses.
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

def index(request):
    return render(request, 'transcribe_app/index.html')

@csrf_exempt
def transcribe_audio(request):
    # Ensure transcriber is initialized
    initialize_transcriber()
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            audio_data = data.get('audio', '')
            
            if not audio_data:
                return JsonResponse({
                    'success': False,
                    'error': 'No audio data provided'
                }, status=400)

            try:
                # Remove the data URL prefix if present
                if ',' in audio_data:
                    audio_data = audio_data.split(',')[1]
                
                # Decode base64 to binary
                audio_binary = base64.b64decode(audio_data)
                
                # Convert to numpy array (assuming float32 format)
                audio_np = np.frombuffer(audio_binary, dtype=np.float32)
                
                # Normalize audio to [-1, 1] range
                if abs(audio_np).max() > 0:
                    audio_np = audio_np / abs(audio_np).max()
                
                # Add error checking for empty or corrupted audio
                if len(audio_np) == 0:
                    return JsonResponse({
                        'success': False,
                        'error': 'Empty audio data received'
                    }, status=400)
                
                if np.isnan(audio_np).any() or np.isinf(audio_np).any():
                    return JsonResponse({
                        'success': False,
                        'error': 'Invalid audio data: contains NaN or Inf values'
                    }, status=400)
                
                # Use the transcriber pipeline
                transcribed_text = transcriber(
                    {"array": audio_np, "sampling_rate": 16000},
                    chunk_length_s=30,
                    stride_length_s=5,
                    batch_size=8,
                    return_timestamps=False,
                )["text"]
                
                # Process transcribed text with Gemini
                corrected_text = process_with_gemini(transcribed_text)
                
                return JsonResponse({
                    'success': True,
                    'text': corrected_text,
                    'original_text': transcribed_text  # Optional: include original text for comparison
                })
            
            except Exception as e:
                print(f"Error processing audio: {str(e)}")
                import traceback
                traceback.print_exc()
                return JsonResponse({
                    'success': False,
                    'error': f"Audio processing error: {str(e)}"
                }, status=400)
                
        except Exception as e:
            print(f"Transcription error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def download_markdown(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            text = data.get('text', '')
            response = HttpResponse(text, content_type='text/markdown')
            response['Content-Disposition'] = 'attachment; filename="transcription.md"'
            return response
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def download_word(request):
    if request.method == 'POST':
        try:
            from docx import Document
            data = json.loads(request.body)
            text = data.get('text', '')
            
            doc = Document()
            doc.add_paragraph(text)
            
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_doc:
                doc.save(temp_doc.name)
                with open(temp_doc.name, 'rb') as f:
                    response = HttpResponse(f.read(), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                    response['Content-Disposition'] = 'attachment; filename="transcription.docx"'
                os.unlink(temp_doc.name)
                return response
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)