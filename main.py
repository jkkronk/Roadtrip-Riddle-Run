import os.path

import quiz
import audio
import asyncio
import street_view_collector
import video
import argparse


def create_new_video(args):
    data_dir = args.data_dir
    path_coordinates = []
    while len(path_coordinates) == 0:
        num_points, city, path_coordinates = create_new_quiz(data_dir, args.city)

    # Create the video
    images = street_view_collector.fetch_street_view_images(path_coordinates, "desktop")
    movie = video.images_to_video(images, os.path.join(data_dir, "quiz.mp3"), add_logo=False)
    movie.write_videofile(os.path.join(data_dir, "quiz.mp4"), fps=24, codec="libx264", audio_codec="aac")


def create_new_quiz(data_dir="/var/data/", city=""):
    # Create a new quiz
    if city == "":
        city = quiz.random_destination(data_dir)
    city_quiz = quiz.create_quiz(city)
    #city_quiz = QuizClues.open("static/quiz.json")
    city_quiz.save(city, os.path.join(data_dir, "quiz.json"))

    # Create the audio
    host_voice = "echo"
    sound = asyncio.run(audio.quiz_2_speech_openai(city_quiz, host_voice))
    host = quiz.QuizHost("What city is our destination?...", f"... And the correct answer is... {city}")
    sound_intro = asyncio.run(audio.text_2_speech_openai(host.intro, host_voice))
    sound = sound_intro + sound
    sound.export(os.path.join(data_dir, "quiz.mp3"), format="mp3")
    #sound = AudioSegment.from_mp3("static/quiz.mp3")

    # Create the video
    duration = sound.duration_seconds
    num_points = street_view_collector.duration_to_num_points(duration)

    path_coordinates = []
    for i in range(50):
        print(f"Attempt {i} to get a path with {num_points} points")
        # Try to get a path with the correct number of points
        path_coordinates = street_view_collector.get_path_coordinates(city, "", num_points)
        print(f"Got {len(path_coordinates)} points")
        if len(path_coordinates) == num_points:
            break

    return num_points, city, path_coordinates

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("city", help="City to generate quiz for", default="")
    parser.add_argument("data_dir", help="Path to data folder", default="./data/")
    args = parser.parse_args()

    create_new_video(args)
