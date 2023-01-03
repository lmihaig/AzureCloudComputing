import json
import os
import sys
from flask import Flask, render_template, request
from azure.storage.blob import BlobServiceClient
import uuid
from azure.cosmos import CosmosClient, PartitionKey
from azure.storage.queue import QueueClient, TextBase64EncodePolicy, TextBase64DecodePolicy


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import config


app = Flask(__name__)

blob_service_client = BlobServiceClient.from_connection_string(config.STORE_CONN)
db_client = CosmosClient(url=config.COSMOS_URI, credential=config.COSMOS_KEY)
database = db_client.create_database_if_not_exists(id="stt-jobs")
partitionKeyPath = PartitionKey(path="/user_email")
db_container = database.create_container_if_not_exists(id="jobs", partition_key=partitionKeyPath)
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
            blob_client = blob_service_client.get_blob_client(container=config.BLOB_NAME, blob=blob_name + ".wav")
            blob_client.upload_blob(audio_file)
            blob_url = blob_client.url
        except Exception:
            print("ERROR UPLOADING BLOB")

        try:
            new_job = {"id": blob_name, "user_email": user_email, "lang_id": lang_id, "blob_url": blob_url}
            db_container.create_item(new_job)
        except Exception:
            print("ERROR ADDING TO DB")

        try:
            new_job = {"id": blob_name, "user_email": user_email, "lang_id": lang_id, "blob_url": blob_url}
            new_job = json.dumps(new_job)
            queue_client.send_message(new_job)

        except Exception:
            print("ERROR ADDING TO QUEUE")

    return render_template("web.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0")
