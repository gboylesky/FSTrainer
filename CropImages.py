from PIL import Image
import os

InputFolder = r"C:\Users\GB\Desktop\FS Trainer Web\static\Randoms"
OutputFolder = r"C:\Users\GB\Desktop\RandomsCropped"

os.makedirs(OutputFolder, exist_ok=True)

CropPixels = 10  # adjust how much to cut off the top

for File in os.listdir(InputFolder):
    if File.lower().endswith((".png", ".jpg", ".jpeg")):
        ImgPath = os.path.join(InputFolder, File)
        Img = Image.open(ImgPath)
        Width, Height = Img.size
        Cropped = Img.crop((0, CropPixels, Width, Height))
        Cropped.save(os.path.join(OutputFolder, File))

print("✅ Done! Cropped images saved.")
