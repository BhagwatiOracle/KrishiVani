from transformers import AutoImageProcessor, AutoModelForImageClassification
from PIL import Image
import torch

MODEL_NAME = "sanjeevani-04/indian-crop-disease-mobilenetv2"

extractor = AutoImageProcessor.from_pretrained(MODEL_NAME)
model = AutoModelForImageClassification.from_pretrained(MODEL_NAME)

model.eval()

def predict_disease(image_path: str, top_k: int=3):
  image = Image.open(image_path).convert("RGB")
  inputs = extractor(images=image, return_tensors='pt')

  with torch.no_grad():
    logits = model(**inputs).logits

  probs = torch.softmax(logits, dim=-1)[0]
  top_indices = probs.topk(top_k).indices.tolist()

  results = []
  for idx in top_indices:
    label = model.config.id2label[idx]
    confidence = probs[idx].item() * 100
    results.append({
        "disease": label,
        'confidence': round(confidence, 4)
    })

  return results