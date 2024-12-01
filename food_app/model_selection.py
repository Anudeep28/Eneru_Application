# Let us now functionize the model selection
import torchvision
import torch
from torch import nn
from torchvision import transforms

def create_transforms(model_name: str):
    """Creates transforms without downloading model weights"""
    if model_name == "effnetb2":
        return transforms.Compose([
            transforms.Resize((288, 288)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
    elif model_name == "effnetv2_s":
        return transforms.Compose([
            transforms.Resize((384, 384)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
    elif model_name == "vit_b_16":
        return transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
    else:
        raise ValueError(f"Unknown model name: {model_name}")

def create_model(model_name: str,
                 out_features: int=3,
                 seed: int=42,
                 device: str="cuda" if torch.cuda.is_available() else "cpu"):
    """Creates a model architecture without pretrained weights.

    Args:
        model_name (str): Name of the model (effnetb2, effnetv2_s, or vit_b_16)
        out_features (int): Number of output classes
        seed (int): Random seed for reproducibility
        device (str): Device to put the model on

    Returns:
        model (torch.nn.Module): Model architecture
        transforms: Corresponding transforms
    """
    assert model_name in ["effnetb2", "effnetv2_s", "vit_b_16"], "Model name should be effnetb2 or effnetv2_s or vit_b_16"
    
    # Get transforms without downloading weights
    transforms_func = create_transforms(model_name)
    
    # Create model architecture without pretrained weights
    if model_name == "effnetb2":
        model = torchvision.models.efficientnet_b2(weights=None).to(device)
        dropout = 0.3
        in_features = 1408
    elif model_name == "effnetv2_s":
        model = torchvision.models.efficientnet_v2_s(weights=None).to(device)
        dropout = 0.2
        in_features = 1280
    elif model_name == "vit_b_16":
        model = torchvision.models.vit_b_16(weights=None).to(device)
        in_features = 768

    # Freeze the base layer of the models
    for param in model.parameters():
        param.requires_grad = False

    # Update the classifier head
    if model_name != "vit_b_16":
        torch.manual_seed(seed)
        model.classifier = nn.Sequential(
            nn.Dropout(p=dropout, inplace=True),
            nn.Linear(in_features=in_features, out_features=out_features)
        ).to(device)
    else:
        torch.manual_seed(seed)
        model.heads = nn.Sequential(
            nn.Linear(in_features=in_features, out_features=out_features)
        ).to(device)

    # set the model name
    model.name = model_name
    print(f"[INFO] Creating {model_name} feature extractor model...")
    return model, transforms_func
