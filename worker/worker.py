import os
import sys
import azure.cognitiveservices.speech as speechsdk
from azure.storage.queue import QueueClient, TextBase64EncodePolicy, TextBase64DecodePolicy
from azure.communication.email import EmailClient, EmailContent, EmailAddress, EmailMessage, EmailRecipients
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import json
import requests
import io
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import config


def send_email(user_email, job_result):
    content = EmailContent(
        subject="Test1",
        plain_text="Test2",
        html=f"<html><h1>{job_result}</h1></html>",
    )
    # TODO: make html pretty and detail explaination


    address = EmailAddress(email=user_email, display_name="Customer Name")
    message = EmailMessage(
        sender="DoNotReply@dda96197-e05a-4d60-95eb-5adc518c42fb.azurecomm.net",
        content=content,
        recipients=EmailRecipients(to=[address]),
    )
    response = email_client.send(message)

    return response


def speech_to_text(id, lang_id, container_client):
    filename = id + ".wav"
    blob_client = container_client.get_blob_client(filename)

    with open(filename, "wb") as audio_file:
        audio_file.write(container_client.download_blob(filename).readall())

    speech_config.speech_recognition_language = lang_id
    audio_config = speechsdk.audio.AudioConfig(filename=filename)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    result = ""

    def result_callback(event_type, evt):
        nonlocal result
        result += evt.result.text

    done = False

    def stop_cb(evt):
        nonlocal done
        done = True

    speech_recognizer.recognized.connect(lambda evt: result_callback('RECOGNIZED', evt))
    speech_recognizer.session_stopped.connect(stop_cb)
    speech_recognizer.canceled.connect(stop_cb)

    speech_recognizer.start_continuous_recognition()
    while not done:
        time.sleep(.5)

    speech_recognizer.stop_continuous_recognition()

    return result


if __name__ == "__main__":
    speech_config = speechsdk.SpeechConfig(subscription=config.SPEECH_SUBSCRIPTION, region=config.SPEECH_REGION)
    queue_client = QueueClient.from_connection_string(
        config.STORE_CONN,
        config.QUEUE_NAME,
        message_encode_policy=TextBase64EncodePolicy(),
        message_decode_policy=TextBase64DecodePolicy(),
    )
    email_client = EmailClient.from_connection_string(config.EMAIL_CON)
    blob_service_client = BlobServiceClient.from_connection_string(config.STORE_CONN)
    container_client = blob_service_client.get_container_client(config.BLOB_NAME)

    # while True:
    job = queue_client.receive_message()
    if not job:
        print("AAAAAAA")

    job_details = json.loads(job.content)
    print(job_details)
    id = job_details.get("id", 0)
    user_email = job_details.get("user_email", 0)
    lang_id = job_details.get("lang_id", 0)
    blob_url = job_details.get("blob_url", 0)

    # TODO: if succesful delete audio file, clear job from queue, clear file from blob, implement while loop to run endlessly, make service
    result = speech_to_text(id, lang_id, container_client)
    send_email(user_email, result)

    # queue_client.delete_message(job.id, job.pop_receipt)
