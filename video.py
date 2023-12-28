from io import BytesIO
from PIL import Image
import numpy as np
import moviepy.editor as mpy


def crop_to_mobile_format(images):
    # This function should crop all images to the correct aspect ratio for TikTok/Instagram
    # There should be no black bars on the sides of the image
    # The image should be cropped from the top and bottom if necessary
    cropped_images = []
    for img in images:
        # Define the dimensions for TikTok/Instagram mobile format (e.g., 9:16 aspect ratio)
        target_width = img.width
        target_height = int(target_width * 16 / 9)  # Assuming 9:16 aspect ratio

        # Calculate cropping dimensions
        left = 0
        if img.height < target_height:
            # If image height is smaller than the target height, adjust dimensions
            target_height = img.height
            top = 0
        else:
            top = (img.height - target_height) // 2  # Use floor division to get an integer value

        right = img.width
        bottom = top + target_height

        # Crop the image
        cropped_img = img.crop((left, top, right, bottom))

        # Resize the image to ensure it fits TikTok/Instagram format
        cropped_img = cropped_img.resize((target_width, target_height))

        # Append the cropped and resized image to the list
        cropped_images.append(cropped_img)

    return cropped_images


def crop_bottom_pixels(images, pixels=10):
    cropped_images = []
    for img in images:
        width, height = img.size
        cropped_img = img.crop((0, 0, width, height - pixels))
        cropped_images.append(cropped_img)
    return cropped_images

def images_to_video(images, audio_file=None, image_duration = 0.4, crop_bottom=True, crop_mobile_format=True):
    global audio
    clips = []

    if crop_bottom:
        images = crop_bottom_pixels(images, pixels=10)
    if crop_mobile_format:
        images = crop_to_mobile_format(images)

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
