import quiz
import audio
import asyncio
from street_view_collector import get_path_coordinates, fetch_street_view_images, create_stop_motion

def main():
    openai_api_key = "sk-..."  # Replace with your OpenAI View API key
    google_api_key = "..." # Replace with your Google Street View API key
    city = "Zurich"  # Replace with your starting city
    host_voice = "nova"

    city_quiz = quiz.create_quiz(city, openai_api_key)
    print("\n CLUES: " + city_quiz.get_all_clues())
    print("\n Explanations: " + city_quiz.get_all_explanation())

    print("Generating audio...")
    sound = asyncio.run(audio.quiz_2_speech_openai(city_quiz, host_voice, openai_api_key))
    host = quiz.QuizHost("What city is our destination?...", f"... And the correct answer is... {city}")
    sound_intro = asyncio.run(audio.text_2_speech_openai(host.intro, host_voice, openai_api_key))
    sound_outro = asyncio.run(audio.text_2_speech_openai(host.outro, host_voice, openai_api_key))

    sound = sound_intro + sound + sound_outro
    sound.export(f"./data/{city}.mp3", format="mp3")

    duration = sound.duration_seconds
    path_coordinates = get_path_coordinates(city, "", google_api_key, duration/0.1)
    if len(path_coordinates) < 10:
        raise ValueError("Too few or no images found for the given city.")
    images = fetch_street_view_images(google_api_key, path_coordinates)
    if len(images) < 10:
        raise ValueError("Too few or no images found for the given city.")

    create_stop_motion(images, f"data/{city}.mp4", f"./data/{city}.mp3")


if __name__ == "__main__":
    main()
