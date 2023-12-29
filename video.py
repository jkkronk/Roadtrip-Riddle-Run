from io import BytesIO
from PIL import Image, ImageFont, ImageDraw
import numpy as np
import moviepy.editor as mpy

def crop_bottom_pixels(images, pixels=10):
    cropped_images = []
    for image in images:
        width, height = image.size
        cropped_img = image.crop((0, 0, width, height - pixels))
        cropped_images.append(cropped_img)
    return cropped_images


def add_logo_on_top(images):
    logo = Image.open("./data/logo.png")
    logo_width, logo_height = logo.size
    # Resize the logo to be a bit smaller than the width of the first image in the list
    base_width, base_height = images[0].size
    logo_width = min(base_width - 20, logo_width)  # Adjust 20 to the desired smaller size
    logo_height = int((logo_width / logo.size[0]) * logo.size[1])
    logo = logo.resize((logo_width, logo_height), Image.LANCZOS)

    images_with_logo = []
    for image in images:
        # Calculate the position to place the top image
        position = ((base_width - logo_width) // 2, (base_height // 3) - (logo_height // 3))

        # Paste the top image on the base image
        image.paste(logo, position, logo)
        images_with_logo.append(image)
    return images_with_logo

def images_to_video(images, audio_file=None, image_duration = 0.4, crop_bottom=True, text_to_add=True):
    global audio
    clips = []

    if crop_bottom:
        images = crop_bottom_pixels(images, pixels=30)
    if text_to_add != "":
        images = add_logo_on_top(images)

    # If audio is provided and its duration is shorter than the total image duration, cut excess frames
    if audio_file:
        audio = mpy.AudioFileClip(audio_file)
        audio_duration = audio.duration

        if audio_duration < len(images) * image_duration:
            # Calculate number of frames to keep based on audio duration
            frames_to_keep = int(audio_duration / image_duration)
            images = images[:frames_to_keep]

    for img in images:
        clip = mpy.ImageClip(np.array(img)).set_duration(image_duration)
        clips.append(clip)

    movie = mpy.concatenate_videoclips(clips, method="compose")

    if audio_file:
        movie = movie.set_audio(audio)

    return movie

def is_gray_image(image_data):
    """Check if the image is predominantly gray."""
    image = Image.open(BytesIO(image_data))
    np_image = np.array(image)

    # Calculate the standard deviation of the color channels
    std_dev = np_image.std(axis=(0, 1))
    return all(x < 20 for x in std_dev)  # Threshold for grayness, might need adjustment
