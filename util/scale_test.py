import requests

url = "http://20.103.138.61/"

obj = {
    "user-email": "kzr4u35cy@mozmail.com",
    "lang-id": "ro-RO"

}

file = {
    "audio-file": open("util/romania.wav", "rb")
}

while True:
    requests.post(url, data=obj, files=file)
