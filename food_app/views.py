from django.shortcuts import render, redirect
from django.views import generic
from .models import FoodOrder, MenuItem
from client.mixins import FoodAppAccessMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
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


class MenuListView(FoodAppAccessMixin, generic.ListView):
    template_name = "food_app/menu_list.html"
    context_object_name = "menu_items"

    def get_queryset(self):
        return MenuItem.objects.all()

class OrderListView(FoodAppAccessMixin, generic.ListView):
    template_name = "food_app/order_list.html"
    context_object_name = "orders"

    def get_queryset(self):
        return FoodOrder.objects.filter(user=self.request.user)

class OrderCreateView(FoodAppAccessMixin, generic.CreateView):
    template_name = "food_app/order_create.html"
    model = FoodOrder
    fields = ['items', 'delivery_address', 'notes']

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return "/food/orders"

class FoodIndexView(FoodAppAccessMixin, generic.TemplateView):
    template_name = "food_app/index.html"

class AnalyzeImageView(FoodAppAccessMixin, generic.View):
    def post(self, request, *args, **kwargs):
        if 'image' not in request.FILES:
            return JsonResponse({'error': 'No image uploaded'}, status=400)

        image_file = request.FILES['image']
        
        try:
            # Open and transform image
            print("Opening image...")
            image = Image.open(io.BytesIO(image_file.read())).convert('RGB')
            print("Transforming image...")
            transformed_image = transforms(image).unsqueeze(0).to(device)
            
            # Make prediction
            print("Making prediction...")
            model.eval()
            with torch.inference_mode():
                pred_logits = model(transformed_image)
                pred_probs = torch.softmax(pred_logits, dim=1)
                pred_label = torch.argmax(pred_probs, dim=1)
                pred_class = class_names[pred_label]
                confidence = pred_probs[0][pred_label].item()
            
            print(f"Prediction: {pred_class}, Confidence: {confidence:.2%}")
            return JsonResponse({
                'prediction': pred_class,
                'confidence': f"{confidence:.2%}"
            })
            
        except Exception as e:
            import traceback
            print(f"Error in AnalyzeImageView: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({'error': str(e)}, status=500)

# URL mappings
index = FoodIndexView.as_view()
analyze_image = csrf_exempt(AnalyzeImageView.as_view())
menu_list = MenuListView.as_view()
order_list = OrderListView.as_view()
order_create = OrderCreateView.as_view()
