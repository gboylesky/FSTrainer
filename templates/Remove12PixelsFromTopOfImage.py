import os
from PIL import Image

# --- Configuration ---
SourceFolder = r"C:\Users\GB\Desktop\Original Randoms"
TargetFolder = r"C:\Users\GB\Desktop\RandomsCropped"
CropTop = 12  # pixels to remove from the top

# --- Ensure target folder exists ---
os.makedirs(TargetFolder, exist_ok=True)

# --- Process each image ---
for filename in os.listdir(SourceFolder):
    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp')):
        src_path = os.path.join(SourceFolder, filename)
        dst_path = os.path.join(TargetFolder, filename)

        # Open the image
        with Image.open(src_path) as img:
            width, height = img.size

            # Define crop box: (left, upper, right, lower)
            crop_box = (0, CropTop, width, height)
            cropped = img.crop(crop_box)

            # Save to destination folder
            cropped.save(dst_path)
            print(f"Cropped {filename} -> saved to {dst_path}")

print("\n✅ Done! All images cropped and saved to:", TargetFolder)
input("Press Enter to exit...")