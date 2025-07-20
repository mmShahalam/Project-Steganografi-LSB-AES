import os
import base64
import numpy as np
from PIL import Image
from .aes_crypto import AESCrypto
from .lsb_stego import LSBSteganography
from .file_processor import FileProcessor

class SteganographyAES:
    def __init__(self, password):
        self.aes = AESCrypto(password)
        self.lsb = LSBSteganography()
        self.file_processor = FileProcessor()

    def hide_message_from_text(self, image_path, secret_message, output_path):
        """Hide plain text message"""
        metadata = {
            'type': 'text',
            'original_filename': 'user_input.txt'
        }

        print("Encrypting message...")
        encrypted_message = self.aes.encrypt_data(secret_message, metadata)
        print(f"Encrypted message length: {len(encrypted_message)} characters")

        print("Hiding message in image...")
        result_path = self.lsb.hide_data(image_path, encrypted_message, output_path)
        print(f"Success! Steganographic image saved at: {result_path}")

        return result_path

    def hide_message_from_file(self, image_path, file_path, output_path):
        """Hide content from uploaded file"""
        print(f"Reading file: {file_path}")

        content, file_type = self.file_processor.read_file_content(file_path)
        file_size = len(base64.b64decode(content))  # Real file size in bytes

        metadata = {
            'type': 'file',
            'original_filename': os.path.basename(file_path),
            'file_type': file_type,
            'file_size': file_size,
            'content_size': len(content)  # Size after encoding/processing
        }

        print(f"File info:")
        print(f"   - Name: {metadata['original_filename']}")
        print(f"   - Type: {file_type}")
        print(f"   - Original file size: {file_size} bytes")
        print(f"   - Encoded data size: {len(content)} characters")

        print("Encrypting file data...")
        encrypted_message = self.aes.encrypt_data(content, metadata)
        print(f"Encrypted data length: {len(encrypted_message)} characters")

        print("Hiding data in image...")
        result_path = self.lsb.hide_data(image_path, encrypted_message, output_path)
        print(f"Success! Steganographic image saved at: {result_path}")

        return result_path

    def extract_message(self, stego_image_path):
        """Extract and decrypt message/file from image"""
        print("Extracting data from image...")
        try:
            encrypted_message = self.lsb.extract_data(stego_image_path)
            print(f"Extracted encrypted data length: {len(encrypted_message)} characters")

            print("Decrypting data...")
            decrypted_content, metadata = self.aes.decrypt_data(encrypted_message)
            print("Success! Data extracted and decrypted!")

            # Display metadata info
            if metadata:
                print(f"Extracted data info:")
                print(f"   - Type: {metadata.get('type', 'unknown')}")
                print(f"   - Original file: {metadata.get('original_filename', 'unknown')}")
                if 'file_type' in metadata:
                    print(f"   - File type: {metadata.get('file_type')}")
                if 'file_size' in metadata:
                    print(f"   - Original size: {metadata.get('file_size')} bytes")

            return decrypted_content, metadata

        except Exception as e:
            print(f"Error detail: {str(e)}")
            raise e

    def create_downloadable_file(self, content, metadata):
        """Create downloadable file from extracted content"""
        output_file = self.file_processor.create_download_file(content, metadata)
        return output_file

    def analyze_image_quality(self, original_path, stego_path):
        """Analyze quality difference between original and steganographic image"""
        # Load images
        original = np.array(Image.open(original_path).convert('RGB'))
        stego = np.array(Image.open(stego_path).convert('RGB'))

        # Calculate MSE (Mean Squared Error)
        mse = np.mean((original - stego) ** 2)

        # Calculate PSNR (Peak Signal-to-Noise Ratio)
        if mse == 0:
            psnr = float('inf')
        else:
            max_pixel = 255.0
            psnr = 20 * np.log10(max_pixel / np.sqrt(mse))

        return mse, psnr