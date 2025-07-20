import os
import base64

class FileProcessor:
    def __init__(self):
        self.supported_formats = ['.txt', '.pdf', '.doc', '.docx', '.xlsx', '.xls']

    def read_file_content(self, file_path):
        """Read content from various file formats in binary mode (preserve original format)"""
        return self._read_binary(file_path)

    def _read_binary(self, file_path):
        """Read file as binary data"""
        try:
            with open(file_path, 'rb') as file:
                binary_data = file.read()

            # Encode binary data as base64 string for JSON compatibility
            encoded_data = base64.b64encode(binary_data).decode('utf-8')
            file_extension = os.path.splitext(file_path)[1].lower()

            # Determine MIME type
            mime_types = {
                '.pdf': 'application/pdf',
                '.doc': 'application/msword',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.txt': 'text/plain',
                '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                '.xls': 'application/vnd.ms-excel'
            }

            mime_type = mime_types.get(file_extension, 'application/octet-stream')
            return encoded_data, mime_type

        except Exception as e:
            raise Exception(f"Error reading binary file: {str(e)}")

    def create_download_file(self, content, metadata):
        """Create downloadable file from extracted content"""
        original_filename = metadata.get('original_filename', 'extracted_file')
        file_type = metadata.get('file_type', 'text/plain')
        data_type = metadata.get('type', 'unknown')

        # Handle plain text differently from binary files
        if data_type == 'text':
            # For plain text, content is already the text string
            base_name = os.path.splitext(original_filename)[0]
            output_filename = f"extracted_{base_name}.txt"

            try:
                with open(output_filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Plain text file created: {output_filename}")
                return output_filename
            except Exception as e:
                print(f"Error creating text file: {str(e)}")
                return None

        else:
            # For binary files, restore original format
            try:
                # Decode base64 back to binary
                binary_data = base64.b64decode(content)

                # Create output filename with original extension
                output_filename = f"extracted_{original_filename}"

                # Write binary data
                with open(output_filename, 'wb') as f:
                    f.write(binary_data)

                print(f"Binary file created: {output_filename}")
                return output_filename

            except Exception as e:
                print(f"Error creating binary file: {str(e)}")
                # Fallback to text file with error info
                base_name = os.path.splitext(original_filename)[0]
                output_filename = f"extracted_{base_name}_error.txt"
                with open(output_filename, 'w', encoding='utf-8') as f:
                    f.write(f"Error restoring file: {str(e)}\n\nBase64 data:\n{content}")
                return output_filename
        return content
