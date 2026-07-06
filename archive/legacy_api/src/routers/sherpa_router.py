import base64
import os
import tempfile
import traceback
from typing import Annotated

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, StringConstraints

from src.services.openai_service import openai_client
from src.services.user_intent.user_intent_service import (
    GeneratedIntentsResponse,
    generate_intent_result,
    get_user_intent,
)
from src.utils.context import CurrentProfile, SessionDep
from src.utils.logger import logger

sherpa_router = APIRouter()


class GenerateTextIntentInput(BaseModel):
    content: Annotated[str, StringConstraints(min_length=1)]


@sherpa_router.post("/text")
async def handle_text_input_route(
    session: SessionDep, profile: CurrentProfile, input: GenerateTextIntentInput
) -> GeneratedIntentsResponse:
    try:
        intent = get_user_intent(user_input=input.content, profile_id=profile.id, session=session)
        result = generate_intent_result(intent)

        return result
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        traceback.print_exc()
        logger.error(f"Error generating user intent: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


class AudioUpload(BaseModel):
    filename: str
    """The name of the audio file to be uploaded."""
    audio_data: str
    """The base64 encoded audio data."""


@sherpa_router.post("/audio/transcribe")
async def transcribe_audio(audio: AudioUpload, profile: CurrentProfile) -> str:
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = os.path.join(temp_dir, "temp_audio.m4a")
            # Decode the base64 audio data
            audio_bytes = base64.b64decode(audio.audio_data)

            with open(temp_file_path, "wb") as dst:
                dst.write(audio_bytes)

            with open(temp_file_path, "rb") as audio_file:
                transcription = openai_client.audio.transcriptions.create(
                    model="whisper-1", file=audio_file, response_format="text"
                )

        return str(transcription)
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error transcribing audio: {error_message}")

        if "invalid_request_error" in error_message:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file format. Please ensure you're uploading a supported audio file. Error: {error_message}",
            )
        elif "file_size" in error_message.lower():
            raise HTTPException(
                status_code=400,
                detail=f"File size error. Please ensure your audio file is within the size limit. Error: {error_message}",
            )
        else:
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {error_message}")


@sherpa_router.post("/voice")
async def handle_audio_upload_route(
    session: SessionDep, audio: AudioUpload, profile: CurrentProfile
) -> GeneratedIntentsResponse:
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = os.path.join(temp_dir, "temp_audio.m4a")
            # Decode the base64 audio data
            audio_bytes = base64.b64decode(audio.audio_data)

            with open(temp_file_path, "wb") as dst:
                dst.write(audio_bytes)

            with open(temp_file_path, "rb") as audio_file:
                transcription = openai_client.audio.transcriptions.create(
                    model="whisper-1", file=audio_file, response_format="text"
                )

        intent = get_user_intent(user_input=str(transcription), profile_id=profile.id, session=session)
        result = generate_intent_result(intent)

        return result

    except Exception as e:
        error_message = str(e)
        logger.error(f"Error transcribing audio: {error_message}")

        if "invalid_request_error" in error_message:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file format. Please ensure you're uploading a supported audio file. Error: {error_message}",
            )
        elif "file_size" in error_message.lower():
            raise HTTPException(
                status_code=400,
                detail=f"File size error. Please ensure your audio file is within the size limit. Error: {error_message}",
            )
        else:
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {error_message}")
