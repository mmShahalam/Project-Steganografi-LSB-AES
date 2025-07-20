from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
import base64
import json

class AESCrypto:
    def __init__(self, password):
        self.password = password.encode('utf-8')

    def _derive_key(self, salt):
        """Derive key from password using PBKDF2"""
        return PBKDF2(self.password, salt, 32, count=100000)

    def encrypt_data(self, data, metadata=None):
        """Encrypt data with optional metadata"""
        # Create data package with metadata
        data_package = {
            'content': data,
            'metadata': metadata or {}
        }

        # Convert to JSON string
        json_data = json.dumps(data_package, ensure_ascii=False)

        # Generate random salt and nonce
        salt = get_random_bytes(16)
        nonce = get_random_bytes(12)

        # Derive key
        key = self._derive_key(salt)

        # Create cipher
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)

        # Encrypt
        ciphertext, tag = cipher.encrypt_and_digest(json_data.encode('utf-8'))

        # Combine salt + nonce + tag + ciphertext
        encrypted_data = salt + nonce + tag + ciphertext

        return base64.b64encode(encrypted_data).decode('utf-8')

    def decrypt_data(self, encrypted_text):
        """Decrypt data and return content with metadata"""
        try:
            # Decode base64
            encrypted_data = base64.b64decode(encrypted_text.encode('utf-8'))

            # Extract components
            salt = encrypted_data[:16]
            nonce = encrypted_data[16:28]
            tag = encrypted_data[28:44]
            ciphertext = encrypted_data[44:]

            # Derive key
            key = self._derive_key(salt)

            # Create cipher
            cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)

            # Decrypt and verify
            plaintext = cipher.decrypt_and_verify(ciphertext, tag)

            # Parse JSON
            data_package = json.loads(plaintext.decode('utf-8'))

            return data_package['content'], data_package.get('metadata', {})

        except Exception as e:
            raise Exception(f"Decryption failed: {str(e)}")

    def encrypt(self, plaintext):
        """Backward compatibility method"""
        return self.encrypt_data(plaintext)

    def decrypt(self, encrypted_text):
        """Backward compatibility method"""
        content, _ = self.decrypt_data(encrypted_text)
