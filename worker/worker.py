import speech_recognition as sr


def recognise_speech_from_file(recognizer, path, lang):
    with sr.AudioFile(path) as audio_file:
        audio = recognizer.record(audio_file)

    response = {"success": True, "error": None, "transcription": None}

    try:
        response["transcription"] = recognizer.recognize_google(audio, language=lang)
    except sr.RequestError:
        response["success"] = False
        response["error"] = "API unavailable"
    except sr.UnknownValueError:
        response["error"] = "Unable to recognize speech"

    return response


if __name__ == "__main__":
    r = sr.Recognizer()

    resp = recognise_speech_from_file(r, "C:/Users/lmg/Desktop/audio_files_harvard.wav", "en-US")
    print(resp)
