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
            print("Markdown Output:", markdown_output)
            
            # Convert markdown to JSON for structured data (used in downloads)
            json_output = markdown_to_json(markdown_output)
            print("JSON Output:", json_output)
            
            json_str = json.dumps(json_output)  # Convert dict to JSON string
            
            # Convert markdown to HTML for display
            html_output = markdown2.markdown(
                markdown_output,
                extras=[
                    'tables',
                    'fenced-code-blocks',
                    'break-on-newline',
                    'header-ids'
                ]
            )
            print("HTML Output:", html_output)
            
            # Save to database
            doc = OCRDocument.objects.create(
                document=filename,
                markdown_output=json_str,  # Store JSON string
                raw_markdown=markdown_output,  # Store raw markdown
                user=request.user
            )
            
            return JsonResponse({
                'json_output': json_output,  # This will be automatically serialized
                'html_output': html_output,
                'markdown_output': markdown_output,
                'doc_id': doc.id,
                'file_url': file_url
            })
            
        except Exception as e:
            print(f"Error in upload_file: {str(e)}")
            return JsonResponse({'error': f'An error occurred: {str(e)}'})
    return JsonResponse({'error': 'Invalid request'})

def json_to_html(json_data, level=0):
    """Convert JSON data to HTML representation with proper markdown rendering"""
    html = []
    
    if not isinstance(json_data, dict) or 'content' not in json_data:
        return str(json_data)
    
    for section in json_data['content']['sections']:
        section_type = section.get('type')
        
        if section_type == 'heading':
            level = section.get('level', 1)
            html.append(f"<h{level}>{section['text']}</h{level}>")
        
        elif section_type == 'paragraph':
            # Convert markdown in paragraph text
            text = markdown2.markdown(section['text'])
            html.append(f"<p>{text}</p>")
        
        elif section_type == 'list':
            items = section.get('items', [])
            if items:
                html.append("<ul>")
                for item in items:
                    # Convert markdown in list items
                    item_html = markdown2.markdown(item)
                    html.append(f"<li>{item_html}</li>")
                html.append("</ul>")
        
        elif section_type == 'table':
            headers = section.get('headers', [])
            rows = section.get('rows', [])
            
            if headers or rows:
                html.append('<table class="min-w-full divide-y divide-gray-200">')
                
                # Table headers
                if headers:
                    html.append('<thead class="bg-gray-50">')
                    html.append('<tr>')
                    for header in headers:
                        html.append(f'<th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{header}</th>')
                    html.append('</tr>')
                    html.append('</thead>')
                
                # Table body
                if rows:
                    html.append('<tbody class="bg-white divide-y divide-gray-200">')
                    for row in rows:
                        html.append('<tr>')
                        for cell in row:
                            # Convert markdown in table cells
                            cell_html = markdown2.markdown(str(cell))
                            html.append(f'<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{cell_html}</td>')
                        html.append('</tr>')
                    html.append('</tbody>')
                
                html.append('</table>')
        
        html.append('<br>')  # Add spacing between sections
    
    return '\n'.join(html)

def markdown_to_json(markdown_text):
    """Convert structured markdown to JSON format while preserving table structure."""
    lines = markdown_text.split('\n')
    content = []
    current_section = None
    list_items = []
    in_table = False
    table_headers = []
    table_rows = []
    
    for line in lines:
        line = line.strip()
        if not line:
            if in_table:  # End of table
                content.append({
                    "type": "table",
                    "headers": table_headers,
                    "rows": table_rows
                })
                in_table = False
                table_headers = []
                table_rows = []
            continue
            
        # Handle headings (both # and ** style)
        if line.startswith('#') or (line.startswith('**') and line.endswith('**')):
            if list_items:
                content.append({
                    "type": "list",
                    "items": list_items.copy()
                })
                list_items = []
            
            heading_text = line.strip('#').strip().strip('*').strip()
            if heading_text.lower() not in ['key features:', 'purpose:', 'features:']:
                content.append({
                    "type": "heading",
                    "text": heading_text,
                    "level": 1 if line.startswith('#') else 2
                })
                current_section = heading_text.lower().replace(':', '')
        
        # Handle list items
        elif line.startswith('*') or line.startswith('-'):
            text = line.strip('*').strip('-').strip()
            if text.startswith('**'):  # Handle bold items
                text = text.strip('*').strip()
            list_items.append(text)
        
        # Handle tables (assuming they're marked with | characters)
        elif '|' in line:
            cells = [cell.strip() for cell in line.strip('|').split('|')]
            
            # Skip table formatting lines (containing ---)
            if '-|-' in line or '|-' in line:
                in_table = True
                continue
                
            if not in_table:  # This is a header row
                table_headers = cells
                in_table = True
            else:  # This is a data row
                table_rows.append(cells)
        
        # Handle paragraphs
        else:
            if list_items:
                content.append({
                    "type": "list",
                    "items": list_items.copy()
                })
                list_items = []
            
            if line:
                content.append({
                    "type": "paragraph",
                    "text": line
                })
    
    # Add any remaining items
    if list_items:
        content.append({
            "type": "list",
            "items": list_items
        })
    if in_table:
        content.append({
            "type": "table",
            "headers": table_headers,
            "rows": table_rows
        })
    
    return {
        "metadata": {
            "type": "document_ocr",
            "version": "1.0"
        },
        "content": {
            "sections": content
        }
    }

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
                "content": """You are a specialized table extractor that converts images into structured markdown format.
                Ensure that all content from the page is included, such as headers, footers, subtexts, images (with all text if possible), tables, and any other elements.
                
                Requirements:
                
                CRITICAL INSTRUCTIONS:
                1. Output Only Markdown: Return solely the Markdown content without any additional explanations or comments.
                2. Table Format: Use standard markdown table syntax with aligned columns:
                   | Header 1 | Header 2 | Header 3 |
                   |----------|----------|----------|
                   | Row 1    | Data     | Data     |
                
                3. Headers and Text: Use appropriate markdown for headers (#, ##) and text formatting.
                4. Preserve Layout: Maintain the visual hierarchy and structure of the original document.
                5. Include ALL text from the image, formatted appropriately in markdown.
                """
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Extract all text and tables from this image into properly formatted markdown."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }],
            max_tokens=1024,
            temperature=0.2,  # Lower temperature for more precise table extraction
            top_p=0.9,
            top_k=50,
            repetition_penalty=1,
            stop=["<|eot_id|>","<|eom_id|>"]
        )
        
        # Get the response content
        markdown_output = response.choices[0].message.content.strip()
        print("LLM Raw Output (Markdown):", markdown_output)
        
        return markdown_output
        
    except Exception as e:
        print(f"Error in process_with_llm: {str(e)}")
        raise

@login_required
def download_markdown(request, doc_id):
    """Download JSON output"""
    try:
        doc = OCRDocument.objects.get(id=doc_id)
        response = HttpResponse(doc.markdown_output, content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="output_{doc_id}.json"'
        return response
    except OCRDocument.DoesNotExist:
        return JsonResponse({'error': 'Document not found'}, status=404)

@login_required
def download_excel(request, doc_id):
    try:
        doc = OCRDocument.objects.get(id=doc_id)
        json_data = json.loads(doc.markdown_output)
        
        # Extract tables and other content
        all_data = []
        
        for section in json_data['content']['sections']:
            if section['type'] == 'table':
                # Add an empty row for spacing if we already have data
                if all_data:
                    all_data.append([])
                
                # Add headers
                all_data.append(section['headers'])
                # Add separator row
                all_data.append(['-' * len(str(header)) for header in section['headers']])
                # Add data rows
                all_data.extend(section['rows'])
            elif section['type'] in ['heading', 'paragraph']:
                # Add an empty row for spacing if we already have data
                if all_data:
                    all_data.append([])
                all_data.append([section['text']])
            elif section['type'] == 'list':
                # Add list items as separate rows
                for item in section['items']:
                    all_data.append([f"• {item}"])
        
        # Create DataFrame
        df = pd.DataFrame(all_data)
        
        # Determine if it's CSV or Excel download
        format_type = request.GET.get('format', 'excel')
        
        if format_type == 'csv':
            # Create CSV response
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="output_{doc_id}.csv"'
            df.to_csv(response, index=False, header=False, encoding='utf-8-sig')
        else:
            # Create Excel file with formatting
            excel_file = BytesIO()
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, header=False)
                
                # Get the worksheet
                worksheet = writer.sheets['Sheet1']
                
                # Auto-adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column = [cell for cell in column]
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = (max_length + 2)
                    worksheet.column_dimensions[column[0].column_letter].width = adjusted_width
            
            excel_file.seek(0)
            response = HttpResponse(
                excel_file.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="output_{doc_id}.xlsx"'
            
        return response
    except OCRDocument.DoesNotExist:
        return JsonResponse({'error': 'Document not found'}, status=404)
