import quiz
import audio
import asyncio
from street_view_collector import get_path_coordinates, fetch_street_view_images, duration_to_num_points
from video import images_to_video
import argparse

def main(args):
    openai_api_key = args.openai_api_key
    google_api_key = args.google_api_key
    city = args.city
    host_voice = "echo"

    city_quiz = quiz.create_quiz(city, openai_api_key)
    print("\n CLUES: " + city_quiz.get_all_clues())
    print("\n Explanations: " + city_quiz.get_all_explanation())

    print("Generating audio...")
    sound = asyncio.run(audio.quiz_2_speech_openai(city_quiz, host_voice, openai_api_key))
    host = quiz.QuizHost("What city is our destination?...", f"... And the correct answer is... {city}")
    sound_intro = asyncio.run(audio.text_2_speech_openai(host.intro, host_voice, openai_api_key))

    sound = sound_intro + sound
    sound.export(f"./data/{city}.mp3", format="mp3")

    duration = sound.duration_seconds
    num_points = duration_to_num_points(duration)

    path_coordinates = get_path_coordinates(city, "", google_api_key, num_points)
    if len(path_coordinates) < 10:
        raise ValueError("Too few or no images found for the given city.")
    images = fetch_street_view_images(google_api_key, path_coordinates, args.view)
    if len(images) < 10:
        raise ValueError("Too few or no images found for the given city.")

    movie = images_to_video(images, f"./data/{city}.mp3")
    movie.write_videofile(f"data/{city}.mp4", fps=24)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("openai_api_key", help="OpenAI API key") #"sk-..."
    parser.add_argument("google_api_key", help="Google API key")
    parser.add_argument("city", help="City to generate quiz for")
    parser.add_argument("view", help="Video for mobile or desktop", choices=["mobile", "desktop"], default="mobile")
    args = parser.parse_args()

    main(args)
