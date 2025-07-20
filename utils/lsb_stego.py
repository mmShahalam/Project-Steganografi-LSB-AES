import numpy as np
from PIL import Image

class LSBSteganography:
    def __init__(self):
        self.delimiter = "<<END_OF_MESSAGE>>"

    def _text_to_binary(self, text):
        """Convert text to binary string"""
        return ''.join([format(ord(i), '08b') for i in text])

    def _binary_to_text(self, binary):
        """Convert binary string to text"""
        text = ''
        for i in range(0, len(binary), 8):
            byte = binary[i:i+8]
            if len(byte) == 8:
                text += chr(int(byte, 2))
        return text

    def hide_data(self, image_path, secret_text, output_path):
        """Hide secret text in image using LSB technique"""
        # Load image
        img = Image.open(image_path)
        img = img.convert('RGB')
        img_array = np.array(img)

        # Add delimiter to secret text
        secret_with_delimiter = secret_text + self.delimiter

        # Convert to binary
        binary_secret = self._text_to_binary(secret_with_delimiter)

        # Check if image can hold the data
        max_capacity = img_array.size
        if len(binary_secret) > max_capacity:
            raise Exception(f"Image too small! Maximum capacity: {max_capacity} bits, data: {len(binary_secret)} bits")

        # Flatten image array
        flat_img = img_array.flatten()

        # Hide data in LSB
        for i in range(len(binary_secret)):
            # Modify LSB of pixel value
            flat_img[i] = (flat_img[i] & 0xFE) | int(binary_secret[i])

        # Reshape back to original dimensions
        stego_img_array = flat_img.reshape(img_array.shape)

        # Save steganographic image as PNG (lossless)
        stego_img = Image.fromarray(stego_img_array.astype('uint8'))

        # Force PNG extension if not already
        if not output_path.lower().endswith('.png'):
            output_path = output_path.rsplit('.', 1)[0] + '.png'

        stego_img.save(output_path, 'PNG')
        print(f"Saved as PNG format: {output_path}")

        return output_path

    def extract_data(self, stego_image_path):
        """Extract secret text from steganographic image"""
        # Load steganographic image
        stego_img = Image.open(stego_image_path)
        stego_img = stego_img.convert('RGB')
        stego_array = np.array(stego_img)

        # Flatten image array
        flat_stego = stego_array.flatten()

        # Extract LSB from each pixel
        binary_data = ''
        for pixel in flat_stego:
            binary_data += str(pixel & 1)

        # Convert binary to text in chunks and look for delimiter
        extracted_text = ''
        for i in range(0, len(binary_data), 8):
            if i + 8 <= len(binary_data):
                byte = binary_data[i:i+8]
                try:
                    char = chr(int(byte, 2))
                    extracted_text += char

                    # Check if found the delimiter
                    if self.delimiter in extracted_text:
                        secret_message = extracted_text.split(self.delimiter)[0]
                        return secret_message
                except ValueError:
                    # Skip invalid characters
                    continue

        # If reach here, delimiter was not found
        raise Exception("Delimiter not found. Possibly no hidden data or corrupted data.")
