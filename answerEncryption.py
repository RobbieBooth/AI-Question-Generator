import base64
import binascii
from os import environ as env
from dotenv import find_dotenv, load_dotenv

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

hard_coded_key = env.get("ANSWER_ENCRYPTION_KEY")  # Get a 32-byte key

# Convert the hexadecimal key to bytes
key = binascii.unhexlify(hard_coded_key)

# Ensure the key length is appropriate for the algorithm
# For AES, the key should be 16, 24, or 32 bytes long
if len(key) not in [16, 24, 32]:
    raise ValueError("The key length must be 16, 24, or 32 bytes.")


def xor_encrypt(data, key):
    # Ensure both data and key are bytes
    if isinstance(data, str):
        data = data.encode('utf-8')
    # Extend the key to match the length of the data
    extended_key = (key * ((len(data) // len(key)) + 1))[:len(data)]
    return bytes(a ^ b for a, b in zip(data, extended_key))


def encrypt_data(data):
    encrypted_data = xor_encrypt(data, key)
    return base64.b64encode(encrypted_data).decode('utf-8')



def xor_decrypt(encrypted_data, key):
    # Ensure encrypted_data is bytes
    if isinstance(encrypted_data, str):
        encrypted_data = encrypted_data.encode('utf-8')
    # Repeat the key to match the length of the encrypted data
    extended_key = (key * ((len(encrypted_data) // len(key)) + 1))[:len(encrypted_data)]
    return bytes(a ^ b for a, b in zip(encrypted_data, extended_key))


def decrypt_data(encrypted_data):
    encrypted_data = base64.b64decode(encrypted_data)
    decrypted_data = xor_decrypt(encrypted_data, key)
    return decrypted_data.decode('utf-8')

