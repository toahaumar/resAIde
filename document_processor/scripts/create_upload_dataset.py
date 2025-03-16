#!/usr/bin/env python3
import os
import sys
import random
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

def tilt_image(image, angle):
    """Rotate the image by the specified angle."""
    return image.rotate(angle, resample=Image.BICUBIC, expand=True, fillcolor=(255, 255, 255))

def adjust_brightness_contrast(image, brightness_factor, contrast_factor):
    """Adjust brightness and contrast of the image."""
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(brightness_factor)
    enhancer = ImageEnhance.Contrast(image)
    return enhancer.enhance(contrast_factor)

def add_gaussian_noise(image, mean=0, std=15):
    """Add Gaussian noise to the image."""
    np_image = np.array(image)
    noise = np.random.normal(mean, std, np_image.shape)
    noisy_image = np_image + noise
    noisy_image = np.clip(noisy_image, 0, 255).astype(np.uint8)
    return Image.fromarray(noisy_image)

def apply_blur(image, radius=2):
    """Apply Gaussian blur to the image."""
    return image.filter(ImageFilter.GaussianBlur(radius))

def process_image(image_path, output_path, angle, brightness, contrast, noise_std, blur_radius):
    with Image.open(image_path) as img:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img = tilt_image(img, angle)
        img = adjust_brightness_contrast(img, brightness, contrast)
        if noise_std > 0:
            img = add_gaussian_noise(img, std=noise_std)
        if blur_radius > 0:
            img = apply_blur(img, radius=blur_radius)
        img.save(output_path)
    print(f"Processed and saved: {output_path}")

def process_images(input_folder, output_folder,
                   tilt_range, brightness_range, contrast_range,
                   noise_std_range, blur_radius_range):
    os.makedirs(output_folder, exist_ok=True)
    for filename in os.listdir(input_folder):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)
            
            # Randomize each parameter within the provided ranges
            angle = random.uniform(tilt_range[0], tilt_range[1])
            brightness = random.uniform(brightness_range[0], brightness_range[1])
            contrast = random.uniform(contrast_range[0], contrast_range[1])
            noise_std = random.uniform(noise_std_range[0], noise_std_range[1])
            blur_radius = random.uniform(blur_radius_range[0], blur_radius_range[1])
            
            process_image(input_path, output_path, angle, brightness, contrast, noise_std, blur_radius)

if __name__ == "__main__":
    # Load input and output directories from environment variables
    input_folder = os.environ.get("INPUT_FOLDER")
    output_folder = os.environ.get("OUTPUT_FOLDER")
    
    if not input_folder or not output_folder:
        print("Error: Please set the INPUT_FOLDER and OUTPUT_FOLDER in your .env file.")
        sys.exit(1)
    
    try:
        # Read transformation ranges from environment variables (with default values)
        tilt_min = float(os.environ.get("TILT_MIN", "-5.0"))
        tilt_max = float(os.environ.get("TILT_MAX", "5.0"))
        
        brightness_min = float(os.environ.get("BRIGHTNESS_MIN", "0.8"))
        brightness_max = float(os.environ.get("BRIGHTNESS_MAX", "1.2"))
        
        contrast_min = float(os.environ.get("CONTRAST_MIN", "0.8"))
        contrast_max = float(os.environ.get("CONTRAST_MAX", "1.2"))
        
        noise_std_min = float(os.environ.get("NOISE_STD_MIN", "0.0"))
        noise_std_max = float(os.environ.get("NOISE_STD_MAX", "10.0"))
        
        blur_radius_min = float(os.environ.get("BLUR_RADIUS_MIN", "0.0"))
        blur_radius_max = float(os.environ.get("BLUR_RADIUS_MAX", "2.0"))
    except ValueError:
        print("Error: One of the environment variables has an invalid value.")
        sys.exit(1)
    
    # Define ranges as tuples
    tilt_range = (tilt_min, tilt_max)
    brightness_range = (brightness_min, brightness_max)
    contrast_range = (contrast_min, contrast_max)
    noise_std_range = (noise_std_min, noise_std_max)
    blur_radius_range = (blur_radius_min, blur_radius_max)
    
    process_images(input_folder, output_folder,
                   tilt_range, brightness_range, contrast_range,
                   noise_std_range, blur_radius_range)
