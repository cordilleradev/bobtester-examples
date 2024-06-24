import requests

def upload_file_to_0x0(file_path: str, secret: bool = False, expires: int | str | None = None) -> str:
    """
    Uploads a file to 0x0.st and returns the URL.

    Args:
    file_path (str): The path to the file to be uploaded.
    secret (bool): If True, the file will be uploaded with a secret flag making the URL hard to guess.
    expires (int or str, optional): Number of hours or a specific epoch timestamp after which the file should expire.

    Returns:
    str: The URL of the uploaded file or an error message.
    """
    url = "http://0x0.st"
    files = {'file': open(file_path, 'rb')}

    data: dict[str, int | str] = {}
    if secret:
        data['secret'] = ''
    if expires:
        data['expires'] = expires

    try:
        response = requests.post(url, files=files, data=data)
        if response.status_code == 200:
            return response.text.strip()  # URL to the uploaded file
        else:
            return f"Failed to upload file: {response.status_code}"
    except Exception as e:
        return str(e)
    finally:
        files['file'].close()  # Ensure the file is closed after the upload

# Example Usage:
# Assuming 'path/to/your/file.txt' is the path to the file you want to upload
# upload_file_to_0x0('path/to/your/file.txt', secret=True, expires=24)
