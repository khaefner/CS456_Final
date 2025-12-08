import os
from PIL import Image, ImageDraw, ImageFont

# Ensure folders exist
os.makedirs("static/avatars", exist_ok=True)

colors = [
    "#FF5733", "#33FF57", "#3357FF", "#F033FF", "#FF33A8",
    "#33FFF5", "#F3FF33", "#FF8C33", "#8C33FF", "#33FF99"
]

for i in range(1, 11):
    # Create a 100x100 image
    img = Image.new('RGB', (100, 100), color=colors[i-1])
    d = ImageDraw.Draw(img)
    
    # Draw the number in the center (Simple "Face")
    # You can replace this logic with actual icons if you have them
    d.text((40, 35), str(i), fill=(255, 255, 255))
    
    img.save(f"static/avatars/{i}.png")

print("Created 10 avatar images in static/avatars/")
