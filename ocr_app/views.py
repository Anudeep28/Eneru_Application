from django.shortcuts import render
import os
import json
import requests
from django.http import JsonResponse, HttpResponse, FileResponse
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from .models import OCRDocument
import markdown
from together import Together
import base64
import pandas as pd
from io import BytesIO
from bs4 import BeautifulSoup
import markdown2
from django.contrib.auth.decorators import login_required

@login_required
def index(request):
    return render(request, 'ocr_app/index.html')

@login_required
def upload_file(request):
    if request.method == 'POST' and request.FILES.get('file'):
        try:
            file = request.FILES['file']
            fs = FileSystemStorage()
            filename = fs.save(file.name, file)
            file_path = fs.path(filename)
            file_url = fs.url(filename)

            # Process with Together API
            markdown_output = process_with_llm(file_path)
            
            # Save to database
            doc = OCRDocument.objects.create(
                file=filename,
                markdown_output=markdown_output
            )
            
            return JsonResponse({
                'markdown_output': markdown_output,
                'doc_id': doc.id,
                'file_url': file_url
            })
            
        except Exception as e:
            return JsonResponse({'error': f'An error occurred: {str(e)}'})
    return JsonResponse({'error': 'Invalid request'})

def process_with_llm(file_path):
    try:
        # Initialize Together with API key from settings
        client = Together(api_key=settings.TOGETHER_API_KEY)
        
        # Read and encode the image file
        with open(file_path, 'rb') as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Create the chat completion with image
        response = client.chat.completions.create(
            model="meta-llama/Llama-Vision-Free",
            messages=[{
                "role": "system",
                "content": """Convert the provided image into Markdown format. Ensure that all content from the page is included, such as headers, footers, subtexts, images (with all text if possible), tables, and any other elements.
  Requirements:

  - Output Only Markdown: Return solely the Markdown content without any additional explanations or comments.
  - No Delimiters: Do not use code fences or delimiters like \`\`\`markdown.
  - Complete Content: Do not omit any part of the page, including headers, footers, and subtext.
  """,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }],
            max_tokens=512,
            temperature=0.7,
            top_p=0.7,
            top_k=50,
            repetition_penalty=1,
            stop=["<|eot_id|>","<|eom_id|>"]
        )
        
        # Get the response content
        markdown_text = response.choices[0].message.content
        return markdown_text
    except Exception as e:
        return str(e)

@login_required
def download_markdown(request, doc_id):
    try:
        doc = OCRDocument.objects.get(id=doc_id)
        response = HttpResponse(doc.markdown_output, content_type='text/markdown')
        response['Content-Disposition'] = f'attachment; filename="output_{doc_id}.md"'
        return response
    except OCRDocument.DoesNotExist:
        return JsonResponse({'error': 'Document not found'}, status=404)

@login_required
def download_excel(request, doc_id):
    try:
        doc = OCRDocument.objects.get(id=doc_id)
        # Convert markdown to HTML
        html_content = markdown2.markdown(doc.markdown_output)
        
        # Parse HTML content
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract data more comprehensively
        data = []
        
        # Process tables if they exist
        tables = soup.find_all('table')
        if tables:
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cols = row.find_all(['td', 'th'])
                    data.append([col.get_text(strip=True) for col in cols])
        else:
            # If no tables, extract text content
            for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']):
                data.append([element.get_text(strip=True)])
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Determine if it's CSV or Excel download
        format_type = request.GET.get('format', 'excel')
        
        if format_type == 'csv':
            # Create CSV response
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="output_{doc_id}.csv"'
            df.to_csv(response, index=False, header=False)
        else:
            # Create Excel file
            excel_file = BytesIO()
            df.to_excel(excel_file, index=False, header=False, engine='openpyxl')
            excel_file.seek(0)
            
            response = HttpResponse(
                excel_file.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="output_{doc_id}.xlsx"'
            
        return response
    except OCRDocument.DoesNotExist:
        return JsonResponse({'error': 'Document not found'}, status=404)
