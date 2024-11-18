import os
from PIL import Image

def compress_and_resize_images(input_folder, output_folder, max_width=1024, quality=85):
    """
    Compress and resize images in a folder for web display.
    
    Parameters:
        input_folder (str): Path to the folder containing the images to process.
        output_folder (str): Path to the folder to save the processed images.
        max_width (int): Maximum width of the resized image (default: 1024 pixels).
        quality (int): Quality of the compressed image (default: 85, range 1-100).
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    for filename in os.listdir(input_folder):
        if filename.lower().endswith(('.jpg', '.jpeg')):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)

            with Image.open(input_path) as img:
                # Resize image if it exceeds the maximum width
                if img.width > max_width:
                    new_height = int((max_width / img.width) * img.height)
                    img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

                # Save the compressed image
                img.save(output_path, format="JPEG", optimize=True, quality=quality)
                print(f"Processed: {filename} -> {output_path}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Compress and resize images in a folder for web display.")
    parser.add_argument("-i", "--input_folder", type=str, required=True, help="Path to the folder containing the images to process.")
    parser.add_argument("-o", "--output_folder", type=str, required=True, help="Path to the folder to save the processed images.")
    parser.add_argument("--max_width", type=int, default=1024, help="Maximum width of the resized image (default: 1024 pixels).")
    parser.add_argument("--quality", type=int, default=85, help="Quality of the compressed image (default: 85).")
    args = parser.parse_args()

    compress_and_resize_images(args.input_folder, args.output_folder, args.max_width, args.quality)