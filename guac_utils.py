import sys
import hashlib
import hmac
import json
import time
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import base64
import urllib.parse

# Generate the raw, unencrypted json for guacamole (expires in 5 minutes)
def generate_raw_json(username: str, vm_name: str, port: int) -> bytes:
    expires_timestamp = str(int((time.time() + 300) * 1000))

    data = {
        "username": username,
        "connections": {
            vm_name: {
                "protocol": "vnc",
                "parameters": {
                    "hostname": "192.168.1.177",
                    "port": str(port)
                }
            }
        },
        "expires": expires_timestamp
    }

    # Convert the dictionary to json
    json_string = json.dumps(data, separators=(',', ':'))

    return json_string.encode('utf-8')


# Generate HMAC signature payload
def generate_HMAC_signed_payload(message: bytes, secret_key: bytes) -> bytes:
    signature = hmac.new(secret_key, msg=message, digestmod=hashlib.sha256)
    return signature.digest() + message


# Pad the data for encryption, PKCS7
def pad_payload_PKCS7(payload: bytes) -> bytes:
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(payload) + padder.finalize()

    return padded_data


# Encrypt the padded payload, AES-128-CBC
def encrypt_payload(payload: bytes, secret_key: bytes) -> bytes:
    # Guacamole uses 16 zero-bytes for its IV
    iv = b'\x00' * 16

    # Set up the cipher
    cipher = Cipher(algorithms.AES(secret_key), modes.CBC(iv))
    encryptor = cipher.encryptor()

    # Encrypt the padded data
    ciphertext = encryptor.update(payload) + encryptor.finalize()

    return ciphertext


# Base64 encode the ciphertext, then URL encode it
def url_encode_encrypted_payload(payload: bytes) -> str:
    # 1. Base64 encode the binary ciphertext
    b64_str = base64.b64encode(payload).decode('utf-8')

    # safe='' ensures '+', '/', and '=' are encoded
    url_safe_token = urllib.parse.quote(b64_str, safe='')

    return url_safe_token


# Generate a signed, encrypted guacamole link that connects to the given VM's VNC port
def generate_vm_guacamole_link(username: str, vm_name: str, port: int, signature_key: bytes, encryption_key: bytes, baseURL: str) -> str:
    raw_json = generate_raw_json(username, vm_name, port)

    signed_json = generate_HMAC_signed_payload(raw_json, signature_key)

    padded_json = pad_payload_PKCS7(signed_json)
    encrypted_json = encrypt_payload(padded_json, encryption_key)

    url_encrypted_json = url_encode_encrypted_payload(encrypted_json)

    return baseURL + url_encrypted_json
