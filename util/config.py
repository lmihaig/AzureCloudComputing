from os import environ as env
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

KEYVAULT_NAME = "tts-general-key-vault"
KEYVAULT_URI = f"https://{KEYVAULT_NAME}.vault.azure.net/"

credential = DefaultAzureCredential()

client = SecretClient(vault_url=KEYVAULT_URI, credential=credential)
COSMOS_URI = client.get_secret("COSMOS-URI").value
COSMOS_KEY = client.get_secret("COSMOS-KEY").value

STORE_CONN = client.get_secret("STORE-CONN").value
BLOB_NAME = client.get_secret("BLOB-NAME").value
TEXT_BLOB_CONTAINER = client.get_secret("TEXT-CONTAINER-NAME").value
QUEUE_NAME = client.get_secret("QUEUE-NAME").value

SPEECH_SUBSCRIPTION = client.get_secret("SPEECH-SUBSCRIPTION").value
SPEECH_REGION = client.get_secret("SPEECH-REGION").value

EMAIL_CON = client.get_secret("EMAIL-CON").value
