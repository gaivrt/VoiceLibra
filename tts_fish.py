import requests
import ormsgpack

TTS_API_URL = "http://127.0.0.1:8888/v1/tts"

def synthesize_text(text: str, reference_audio_path: str = None, reference_text: str = None, output_format: str = "wav") -> bytes:
    """
    Synthesize speech from text using the Fish-Speech TTS API.
    If reference_audio_path and reference_text are provided, use them for voice cloning.
    Returns the synthesized audio content as bytes in the specified format.
    """
    # Prepare request payload
    if reference_audio_path:
        # Read reference audio file
        with open(reference_audio_path, "rb") as f:
            audio_bytes = f.read()
        # Construct request with reference (use MessagePack)
        payload = {
            "text": text,
            "format": output_format
        }
        # Use a list of references
        payload["references"] = [
            {"audio": audio_bytes, "text": reference_text or ""}
        ]
        headers = {"Content-Type": "application/msgpack"}
        data = ormsgpack.packb(payload, option=ormsgpack.OPT_SERIALIZE_PYDANTIC)
        response = requests.post(TTS_API_URL, data=data, headers=headers)
    else:
        # Simple JSON payload without reference
        json_payload = {"text": text, "format": output_format}
        response = requests.post(TTS_API_URL, json=json_payload)
    if response.status_code != 200:
        raise RuntimeError(f"TTS API call failed (status {response.status_code}): {response.text}")
    return response.content
