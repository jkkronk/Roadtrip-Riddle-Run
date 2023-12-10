import google_streetview.api
import random
import moviepy.editor as mpy
import requests


def get_path_coordinates(start_location, destination, api_key, num_points=10):
    # Set up the request to the Google Directions API
    base_url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        'origin': f'{start_location[0]},{start_location[1]}',
        'destination': f'{destination[0]},{destination[1]}',
        'key': api_key
    }

    # Make the request
    response = requests.get(base_url, params=params)
    if response.status_code != 200:
        raise ConnectionError("Failed to connect to the Directions API")

    directions = response.json()

    if not directions['routes']:
        raise ValueError("No routes found for the given locations.")

    # Extract the steps in the route
    steps = directions['routes'][0]['legs'][0]['steps']

    # Get coordinates from the steps
    path_coordinates = []
    for step in steps:

        path_coordinates.append((step['start_location']['lat'], step['start_location']['lng']))
        if len(path_coordinates) >= num_points:
            break

    # Fill up remaining points if needed
    while len(path_coordinates) < num_points:
        path_coordinates.append(path_coordinates[-1])

    return path_coordinates
def fetch_street_view_images(api_key, path_coordinates):
    images = []
    for lat, lng in path_coordinates:
        params = [{
            'size': '600x300',  # Image size
            'location': f'{lat},{lng}',
            'heading': '0',  # Adjust if needed to face the direction of the path
            'pitch': '0',
            #'source': 'outdoor',  # Outdoor images only
            'key': api_key
        }]
        results = google_streetview.api.results(params)
        images.append(results.links[0])
    return images

def create_stop_motion(images, output_file='data/stop_motion_movie.mp4'):
    clips = [mpy.ImageClip(image).set_duration(0.2) for image in images]  # 0.2 seconds per image
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
    api_key = 'AIzaSyAgjDUz41LJBVJD_6ZV3JF35xhdPQ18w_4'  # Replace with your Google Street View API key
    city = "New York City"  # Replace with your starting city

    destination = get_coordinates_from_city(city)
    start = destination[0], destination[1] - 1  # Slightly offset the start location
    print(f"Start Location: {start}")
    print(f"\nDestination: {destination}")
    path_coordinates = get_path_coordinates(start, destination, api_key, num_points=1000)
    images_url = fetch_street_view_images(api_key, path_coordinates)

    images = []
    for i, img in enumerate(images_url):
        # save image to data folder
        img = requests.get(img)
        images.append('data/img_' + str(i) + '.jpg')
        with open('data/img_' + str(i) + '.jpg', 'wb') as f:
            f.write(img.content)

    create_stop_motion(images)

if __name__ == "__main__":
    main()

