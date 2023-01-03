import os
import sys
import azure.cognitiveservices.speech as speechsdk
from azure.storage.queue import QueueClient, BinaryBase64EncodePolicy, BinaryBase64DecodePolicy
from azure.communication.email import EmailClient, EmailContent, EmailAddress, EmailMessage, EmailRecipients
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import config


def send_email(user_email, job_result):
    content = EmailContent(
        subject="Test1",
        plain_text="Test2",
        html=f"<html><h1>Test3 {job_result}</h1></html>",
    )

    address = EmailAddress(email=user_email, display_name="Customer Name")
    message = EmailMessage(
        sender="DoNotReply@dda96197-e05a-4d60-95eb-5adc518c42fb.azurecomm.net",
        content=content,
        recipients=EmailRecipients(to=[address]),
    )
    response = email_client.send(message)

    return response


if __name__ == "__main__":
    speech_config = speechsdk.SpeechConfig(subscription=config.SPEECH_SUBSCRIPTION, region=config.SPEECH_REGION)
    queue_client = QueueClient.from_connection_string(config.STORE_CONN, config.QUEUE_NAME)
    email_client = EmailClient.from_connection_string(config.EMAIL_CON)
    
    blob_service_client = BlobServiceClient.from_connection_string(config.STORE_CONN)
    blob_client.get_blob_client(container=config.BLOB_NAME, blob=file_name)

    while True:
        job = queue_client.receive_message()
        if not job:
            continue

        print(job)

    speech_config.speech_recognition_language = "en-US"
    audio_config = speechsdk.audio.AudioConfig(filename="C:/Users/lmg/Desktop/audio_files_harvard.wav")
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    result = speech_recognizer.recognize_once_async().get()
