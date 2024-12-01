from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from . import model_selection
import torch
import torchvision
from torch import nn
from PIL import Image
import io

# Load class names
with open('food_app/models/indian_class_names.txt', 'r') as f:
    class_names = [line.strip() for line in f.readlines()]


# Setup device
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Create model and load weights
### 2. Model and transforms preparation ###    

# Create model
model, transforms = model_selection.create_model(model_name="vit_b_16",
    out_features=len(class_names), # could also use len(class_names)
    device=device
)

# Load saved weights
model.load_state_dict(
    torch.load(
        f="food_app/models/indian_food_model_v3.pth",
        map_location=device,  # load to CPU
    )
)




@login_required
def index(request):
    return render(request, 'food_app/index.html')

@login_required
@csrf_exempt
def analyze_image(request):
    if request.method == 'POST' and request.FILES.get('image'):
        try:
            # Read and transform the image
            image_file = request.FILES['image']
            image_bytes = image_file.read()
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            img = transforms(image).unsqueeze(0).to(device)
            
            # Get prediction
            model.eval()
            with torch.inference_mode():
                # Get model predictions and probabilities
                pred_logits = model(img)
                pred_probs = torch.softmax(pred_logits, dim=1)
                
                # Get top prediction and its probability
                pred_label_idx = torch.argmax(pred_probs, dim=1).item()
                confidence = pred_probs[0][pred_label_idx].item()
                
                return JsonResponse({
                    'food_name': class_names[pred_label_idx],
                    'confidence': confidence
                })
                
        except Exception as e:
            print(f"Error in analyze_image: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)
            
    return JsonResponse({'error': 'No image provided'}, status=400)
