from multiprocessing import Process
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


def speech_to_text(filename, lang_id, speech_config):
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


def process_audio(filename, lang_id, container_client, speech_config):
    with open(filename, "wb") as audio_file:
        print(f'{os.getpid()}: Creating temporary audio file {filename}.')
        audio_file.write(container_client.download_blob(filename).readall())

    try:
        print(f'{os.getpid()}: Converting {filename} to text.')
        result = speech_to_text(filename, lang_id, speech_config)
    finally:
        print(f'{os.getpid()}: Removing temporary file {filename}')
        os.remove(filename)

    return result


def process_job(job, container_client, queue_client, speech_config):
    job_details = json.loads(job.content)
    print(f'{os.getpid()}: Processing job ', job_details)
    id = job_details.get("id", 0)
    user_email = job_details.get("user_email", 0)
    lang_id = job_details.get("lang_id", 0)
    blob_url = job_details.get("blob_url", 0)

    filename = id + ".wav"
    # TODO: make service
    try:
        result = process_audio(filename, lang_id, container_client, speech_config)
    except Exception as e:
        print(f"{os.getpid()}: Failed processing audio file {id}.")
    else:
        print(f'{os.getpid()}: Sending email.')
        send_email(user_email, result)
    finally:
        print(f'{os.getpid()}: Deleting message from queue.')
        queue_client.delete_message(job)
        try:
            print(f'{os.getpid()}: Deleting blob.')
            container_client.delete_blob(filename)
        except Exception as e:
            print(f'{os.getpid()}: Could not delete blob. Error: ', e)


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

    while True:
        job = queue_client.receive_message(visibility_timeout=600)
        if not job:
            continue
        # Jobul ramane in queue daca nu a putut fi creat un proces nou pentru el.
        p = Process(target=process_job, args=(job, container_client, queue_client, speech_config))
        p.start()
