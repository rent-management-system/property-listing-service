# app/utils/object_storage.py
import uuid
from fastapi import UploadFile
from typing import List
from supabase import create_client, Client
from app.config import settings

# Initialize Supabase client
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

async def upload_file_to_object_storage(file: UploadFile) -> str:
    """
    Uploads a file to Supabase Storage and returns its public URL.
    """
    try:
        # Generate a unique filename
        file_extension = file.filename.split(".")[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        
        # Read file content
        contents = await file.read()

        # Upload to Supabase Storage
        response = supabase.storage.from_(settings.BUCKET_NAME).upload(unique_filename, contents, {"content-type": file.content_type})
        
        # Check if upload was successful
        if response.get("statusCode") == 200 or response.get("Key"): # Supabase client might return different structures
            # Get the public URL
            public_url_response = supabase.storage.from_(settings.BUCKET_NAME).get_public_url(unique_filename)
            return public_url_response
        else:
            # Handle upload error
            print(f"Supabase upload error: {response}")
            raise Exception("Failed to upload file to Supabase Storage")

    except Exception as e:
        print(f"Error uploading file to Supabase: {e}")
        raise e

async def upload_multiple_files_to_object_storage(files: List[UploadFile]) -> List[str]:
    """
    Uploads multiple files to Supabase Storage and returns their public URLs.
    """
    urls = []
    for file in files:
        url = await upload_file_to_object_storage(file)
        urls.append(url)
    return urls
