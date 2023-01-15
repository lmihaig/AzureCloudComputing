import json
import os
import sys
from flask import Flask, render_template, request
from azure.storage.blob import BlobServiceClient, ContentSettings
import uuid
from azure.storage.queue import QueueClient, TextBase64EncodePolicy, TextBase64DecodePolicy


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import config


app = Flask(__name__)

blob_service_client = BlobServiceClient.from_connection_string(config.STORE_CONN)
queue_client = QueueClient.from_connection_string(
    config.STORE_CONN,
    config.QUEUE_NAME,
    message_encode_policy=TextBase64EncodePolicy(),
    message_decode_policy=TextBase64DecodePolicy(),
)


@app.route("/", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        user_email = request.form.get("user-email")
        lang_id = request.form.get("lang-id")
        audio_file = request.files.get("audio-file")
        # audio_file.filename = secure_filename(audio_file.filename)
        try:
            blob_name = uuid.uuid4().hex
            file_name = blob_name + ".wav"
            blob_client = blob_service_client.get_blob_client(container=config.BLOB_NAME, blob=file_name)
            blob_client.upload_blob(
                audio_file, content_settings=ContentSettings(content_disposition=f'attachment;filename="{file_name}"')
            )
            blob_url = blob_client.url
        except Exception:
            print("ERROR UPLOADING BLOB")
        else:
            try:
                new_job = {"id": blob_name, "user_email": user_email, "lang_id": lang_id, "blob_url": blob_url}
            except Exception:
                print("ERROR ADDING TO DB")
            else:
                try:
                    new_job = {"id": blob_name, "user_email": user_email, "lang_id": lang_id, "blob_url": blob_url}
                    new_job = json.dumps(new_job)
                    # TODO: Update TTL for job? Default is 7 days
                    queue_client.send_message(new_job)

                except Exception:
                    print("ERROR ADDING TO QUEUE")

    return render_template("web.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
