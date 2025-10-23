from PIL import Image
import os

# Define directories
input_dir = r"C:\Users\GB\Desktop\FS Trainer Web\static\Randoms"
output_dir = r"C:\Users\GB\Desktop\Adjusted Images"

# Get all PNG files sorted alphabetically (so we have a consistent first image)
png_files = [f for f in os.listdir(input_dir) if f.lower().endswith(".png")]
png_files.sort()

if not png_files:
    raise FileNotFoundError("No PNG files found in the input directory.")

# Get the dimensions of the first image
first_image_path = os.path.join(input_dir, png_files[0])
with Image.open(first_image_path) as first_img:
    target_width, target_height = first_img.size
    print(f"Reference image: {png_files[0]} ({target_width}x{target_height})")

# Process each PNG image
for filename in png_files:
    input_path = os.path.join(input_dir, filename)
    output_path = os.path.join(output_dir, filename)

    with Image.open(input_path) as img:
        width, height = img.size

        # Step 1: Resize proportionally to at least target size
        img_ratio = width / height
        target_ratio = target_width / target_height

        if img_ratio > target_ratio:
            # Image is relatively wider than target → match height first
            new_height = target_height
            new_width = int(height * img_ratio)
        else:
            # Image is relatively taller than target → match width first
            new_width = target_width
            new_height = int(width / img_ratio)

        resized = img.resize((new_width, new_height), Image.LANCZOS)

        # Step 2: Crop to exact target size
        left = 0
        top = 0

        if new_width > target_width:
            # Too wide → crop from left
            left = new_width - target_width
        if new_height > target_height:
            # Too tall → crop from top
            top = new_height - target_height

        right = left + target_width
        bottom = top + target_height
        cropped = resized.crop((left, top, right, bottom))

        # Step 3: Save output
        cropped.save(output_path)

print("✅ All images resized and cropped to match the first image’s dimensions.")