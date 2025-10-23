from PIL import Image
import os

output_dir = r"C:\Users\GB\Desktop\FS Trainer Web\static\Randoms"

# Get all PNG files
png_files = [f for f in os.listdir(output_dir) if f.lower().endswith(".png")]
png_files.sort()

dimensions = set()

for filename in png_files:
    path = os.path.join(output_dir, filename)
    with Image.open(path) as img:
        size = img.size
        dimensions.add(size)
        print(f"{filename}: {size}")

if len(dimensions) == 1:
    print("\n✅ All images have identical dimensions.")
else:
    print("\n⚠️ Mismatch detected! Different image sizes found:")
    for d in dimensions:
        print(d)