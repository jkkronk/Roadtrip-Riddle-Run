import math
import google_streetview.api
import requests
import polyline
import numpy as np
from io import BytesIO
from video import is_gray_image
from PIL import Image

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

def duration_to_num_points(duration, image_duration=0.4):
    num_points = int(duration / image_duration) + 10  # Add 5 points to ensure enough images
    return num_points

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
def fetch_street_view_images(api_key, path_coordinates, view="mobile"):
    images = []

    size = "390x640" if view == "mobile" else "630x400"

    for i in range(len(path_coordinates) - 1):
        lat, lng = path_coordinates[i]
        next_lat, next_lng = path_coordinates[i + 1]

        # Calculate heading towards the next point
        heading = calculate_heading(lat, lng, next_lat, next_lng)

        params = [{
            "size": size,  # Image size
            "fov": "120",  # Field of view
            "radius": "100",  # How far away from the location to capture
            "location": f"{lat},{lng}",
            "heading": heading,  # Adjust if needed to face the direction of the path
            "pitch": "0",
            "source": "outdoor",  # Outdoor images only
            "key": api_key
        }]
        results = google_streetview.api.results(params)

        # Download the image
        response = requests.get(results.links[0])
        if response.status_code == 200:
            image_data = response.content
            if not is_gray_image(image_data):
                img = Image.open(BytesIO(image_data))
                images.append(img)

    return images

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
