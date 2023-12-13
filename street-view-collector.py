import google_streetview.api
import moviepy.editor as mpy
import requests
import polyline
import math
from PIL import Image
import numpy as np
from io import BytesIO

def is_gray_image(image_data):
    """Check if the image is predominantly gray."""
    image = Image.open(BytesIO(image_data))
    np_image = np.array(image)

    # Calculate the standard deviation of the color channels
    std_dev = np_image.std(axis=(0, 1))
    return all(x < 20 for x in std_dev)  # Threshold for grayness, might need adjustment

def calculate_heading(lat1, lng1, lat2, lng2):
    # Convert degrees to radians
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])

    # Calculate the change in coordinates
    delta_lng = lng2 - lng1

    # Calculate the heading
    x = math.sin(delta_lng) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(delta_lng))
    heading = math.atan2(x, y)

    # Convert heading to degrees and adjust to compass heading
    heading = math.degrees(heading)
    heading = (heading + 360) % 360
    return heading
def get_path_coordinates(destination, start_location="", api_key="", num_points=10):
    destination_coord = get_coordinates_from_city(destination)

    if(start_location == ""):
        # Randomly generate a start location
        lat_random = np.random.uniform(-1, 1)
        lng_random = np.random.uniform(-1, 1)
        start_coord = destination_coord[0] + lat_random , destination_coord[1] + lng_random  # Slightly offset the start location
    else:
        start_coord = get_coordinates_from_city(start_location)

    print(f"Start Location: {start_coord}")
    print(f"\nDestination: {destination_coord}")

    # Set up the request to the Google Directions API
    base_url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        'origin': f'{start_coord[0]},{start_coord[1]}',
        'destination': f'{destination_coord[0]},{destination_coord[1]}',
        'key': api_key
    }

    # Make the request
    response = requests.get(base_url, params=params)
    if response.status_code != 200:
        raise ConnectionError("Failed to connect to the Directions API")

    directions = response.json()

    if not directions['routes']:
        raise ValueError("No routes found for the given locations.")

    # Extract the polyline from the first route
    encoded_polyline = directions['routes'][0]['overview_polyline']['points']

    # Decode the polyline
    full_path = polyline.decode(encoded_polyline)

    # Select evenly spaced points from the path
    path_coordinates = []
    for i in range(0, min(num_points, len(full_path))):
        path_coordinates.append(full_path[i])

    # Trim or extend the list to match the desired number of points
    if len(path_coordinates) > num_points:
        path_coordinates = path_coordinates[:num_points]
    while len(path_coordinates) < num_points:
        path_coordinates.append(path_coordinates[-1])

    return path_coordinates
def fetch_street_view_images(api_key, path_coordinates):
    images = []

    for i in range(len(path_coordinates) - 1):
        lat, lng = path_coordinates[i]
        next_lat, next_lng = path_coordinates[i + 1]

        # Calculate heading towards the next point
        heading = calculate_heading(lat, lng, next_lat, next_lng)

        params = [{
            'size': '600x300',  # Image size
            'location': f'{lat},{lng}',
            'heading': heading,  # Adjust if needed to face the direction of the path
            'pitch': '0',
            #'source': 'outdoor',  # Outdoor images only
            'key': api_key
        }]
        results = google_streetview.api.results(params)

        # Download the image
        response = requests.get(results.links[0])
        if response.status_code == 200:
            image_data = response.content
            if not is_gray_image(image_data):
                images.append(image_data)

    return images

def create_stop_motion(images, output_file='data/stop_motion_movie.mp4'):
    clips = []
    for image_data in images:
        with Image.open(BytesIO(image_data)) as img:
            np_image = np.array(img)
            clip = mpy.ImageClip(np_image).set_duration(0.2)  # 0.2 seconds per image
            clips.append(clip)

    movie = mpy.concatenate_videoclips(clips, method="compose")
    movie.write_videofile(output_file, fps=24)

def get_coordinates_from_city(city):
    base_url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': city,
        'format': 'json'
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        result = response.json()
        if result:
            return float(result[0]['lat']), float(result[0]['lon'])
        else:
            raise ValueError("No results found for the given city.")
    else:
        raise ConnectionError("Failed to connect to the Nominatim API.")


def main():
    api_key = ''  # Replace with your Google Street View API key
    city = "Zurich"  # Replace with your starting city

    path_coordinates = get_path_coordinates(city, "", api_key, 200)

    if len(path_coordinates) < 10:
        raise ValueError("Too few or no images found for the given city.")

    images = fetch_street_view_images(api_key, path_coordinates)
    # Check if there was images returned. If not, return an error.
    if len(images) < 10:
        raise ValueError("Too few or no images found for the given city.")


    create_stop_motion(images, 'data/stop_motion_' + city + '.mp4')

if __name__ == "__main__":
    main()

