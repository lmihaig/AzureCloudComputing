from multiprocessing import Process
from datetime import datetime, timedelta
import os
import sys
import azure.cognitiveservices.speech as speechsdk
from azure.storage.queue import QueueClient, TextBase64EncodePolicy, TextBase64DecodePolicy
from azure.communication.email import EmailClient, EmailContent, EmailAddress, EmailMessage, EmailRecipients
from azure.storage.blob import (
    BlobServiceClient,
    ContentSettings,
    generate_blob_sas,
    BlobSasPermissions,
)
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import config


def send_email(user_email, audio_file_link, text_file_link):
    # TODO: schimb emailul, "Your STT request is ready. The links will be available until <data curenta + TTL-ul bloburilor>"
    content = EmailContent(
        subject="Your Speech to Text conversion is ready.",
        plain_text="",
        html=f"""
        <html>
            The links will expire in 7 days. <br/>
            Audio file: <a href="{audio_file_link}">{audio_file_link}</a> <br/>
            Text file:  <a href="{text_file_link}">{text_file_link}</a>
        </html>
        """,
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

    speech_recognizer.recognized.connect(lambda evt: result_callback("RECOGNIZED", evt))
    speech_recognizer.session_stopped.connect(stop_cb)
    speech_recognizer.canceled.connect(stop_cb)

    speech_recognizer.start_continuous_recognition()
    while not done:
        time.sleep(0.5)

    speech_recognizer.stop_continuous_recognition()

    return result


def process_audio(filename, lang_id, container_client, speech_config):
    try:
        with open(filename, "wb") as audio_file:
            print(f"{os.getpid()}: Creating temporary audio file {filename}.")
            audio_data = container_client.download_blob(filename).readall()
            audio_file.write(audio_data)
        print(f"{os.getpid()}: Converting {filename} to text.")
        result = speech_to_text(filename, lang_id, speech_config)
    finally:
        print(f"{os.getpid()}: Removing temporary file {filename}")
        os.remove(filename)

    return result


def generate_blob_link(blob_service_client, container_name, blob_name):
    print(f"{os.getpid()}: Getting delegation key...")
    delegation_key = blob_service_client.get_user_delegation_key(
        key_start_time=datetime.utcnow(), key_expiry_time=datetime.utcnow() + timedelta(days=7)
    )
    print(f"{os.getpid()}: Getting Blob SAS...")
    sas_blob = generate_blob_sas(
        account_name=config.ACCOUNT_NAME,
        user_delegation_key=delegation_key,
        container_name=container_name,
        blob_name=blob_name,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(days=7),
    )

    blob_link = (
        "https://" + config.ACCOUNT_NAME + ".blob.core.windows.net/" + container_name + "/" + blob_name + "?" + sas_blob
    )
    return blob_link


def process_job(job, blob_service_client, audio_container_client, text_container_client, queue_client, speech_config):
    job_details = json.loads(job.content)
    print(f"{os.getpid()}: Processing job ", job_details)
    id = job_details.get("id", 0)
    user_email = job_details.get("user_email", 0)
    lang_id = job_details.get("lang_id", 0)
    blob_url = job_details.get("blob_url", 0)

    filename = id + ".wav"
    result_filename = id + "_result.txt"
    try:
        result = process_audio(filename, lang_id, audio_container_client, speech_config)
        text_container_client.get_blob_client(result_filename).upload_blob(
            result, content_settings=ContentSettings(content_disposition=f'attachment;filename="{result_filename}"')
        )

        audio_file_link = generate_blob_link(blob_service_client, config.BLOB_NAME, filename)
        text_file_link = generate_blob_link(blob_service_client, config.TEXT_BLOB_CONTAINER, result_filename)

    except Exception as e:
        print(f"{os.getpid()}: Failed processing audio file {id}.", e)
    else:
        print(f"{os.getpid()}: Sending email.")
        send_email(user_email, audio_file_link, text_file_link)
    finally:
        print(f"{os.getpid()}: Deleting message from queue.")
        queue_client.delete_message(job)


if __name__ == "__main__":
    account_url = "https://" + config.ACCOUNT_NAME + ".blob.core.windows.net"
    blob_service_client = BlobServiceClient(account_url, credential=config.credential)

    speech_config = speechsdk.SpeechConfig(subscription=config.SPEECH_SUBSCRIPTION, region=config.SPEECH_REGION)
    queue_client = QueueClient.from_connection_string(
        config.STORE_CONN,
        config.QUEUE_NAME,
        message_encode_policy=TextBase64EncodePolicy(),
        message_decode_policy=TextBase64DecodePolicy(),
    )
    email_client = EmailClient.from_connection_string(config.EMAIL_CON)
    audio_container_client = blob_service_client.get_container_client(config.BLOB_NAME)
    text_container_client = blob_service_client.get_container_client(config.TEXT_BLOB_CONTAINER)

    while True:
        job = queue_client.receive_message(visibility_timeout=600)
        if not job:
            time.sleep(5)
            continue
        # Jobul ramane in queue daca nu a putut fi creat un proces nou pentru el.
        p = Process(
            target=process_job,
            args=(job, blob_service_client, audio_container_client, text_container_client, queue_client, speech_config),
        )
        p.start()
