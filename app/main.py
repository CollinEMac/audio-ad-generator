import asyncio
import json
import os
import subprocess
import tempfile
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from openai import AsyncOpenAI
from elevenlabs.client import AsyncElevenLabs
from elevenlabs import VoiceSettings

load_dotenv()

app = FastAPI()

openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
elevenlabs_client = AsyncElevenLabs(api_key=os.getenv("ELEVEN_LABS_KEY"))

BRANDS: list[dict] = json.loads(Path("static/exampleBrands.json").read_text())

OUTPUT_DIR = Path("static/generated")
OUTPUT_DIR.mkdir(exist_ok=True)

DEFAULT_VOICE_ID = "pNInz6obpgDQGcFmaJgB"


def _get_brand(brand_id: int) -> dict:
    """Get the brand by ID"""
    for brand in BRANDS:
        if brand["id"] == brand_id:
            return brand
    raise HTTPException(status_code=404, detail="Brand not found")


async def _generate_ad_script(brand: dict) -> str:
    """Use the given brand info to create a 15 second script"""
    products = ", ".join(brand["products"])
    prompt = (
        f"Write a 15-second radio ad script for the brand named '{brand['brandName']}'.\n"
        f"Brand description: {brand['description']}\n"
        f"Featured products: {products}\n"
        f"Tone/voice: {brand['voice']}\n\n"
        "Write only the spoken words. No stage directions, no sound cues, no labels. "
        "End with a clear call to action."
    )
    response = await openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100,
    )
    return response.choices[0].message.content.strip()


async def _resolve_voice_id(voice_description: str) -> str:
    """Query ElevenLabs voice search with the brand's voice descriptions"""
    try:
        result = await elevenlabs_client.voices.search(
            query=voice_description,
        )
        if result.voices:
            return result.voices[0].voice_id
    except Exception:
        pass
    return DEFAULT_VOICE_ID


async def _text_to_speech(script: str, voice_id: str) -> Path:
    """Create a local mp3 from the given script"""
    audio_generator = elevenlabs_client.text_to_speech.convert(
        voice_id=voice_id,
        text=script,
        model_id="eleven_turbo_v2",
        voice_settings=VoiceSettings(
            stability=0.5,
            similarity_boost=0.75,
            style=0.3,
            use_speaker_boost=True,
        ),
    )
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    async for chunk in audio_generator:
        tmp.write(chunk)
    tmp.close()
    return Path(tmp.name)


def _get_audio_duration(path: Path) -> float:
    """Returns audio duration in seconds."""
    result = subprocess.run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path)
    ], capture_output=True, text=True, check=True)
    return float(result.stdout.strip())


async def _generate_music(brand: dict, duration: float) -> Path:
    """Generate background music via ElevenLabs sound generation"""
    prompt = (
        f"Background music for a 15-second audio advertisement. "
        f"Brand: {brand['brandName']}. "
        f"Tone: {brand['voice']}. "
        "Instrumental only, no vocals, subtle and non-distracting."
    )
    audio_generator = elevenlabs_client.text_to_sound_effects.convert(
        text=prompt,
        duration_seconds=duration,
        prompt_influence=0.4,
    )
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    async for chunk in audio_generator:
        tmp.write(chunk)
    tmp.close()
    return Path(tmp.name)


def _mix_audio(voiceover_path: Path, music_path: Path, duration: float) -> Path:
    """Edit the audio given a music clip and voice clip"""
    out_path = OUTPUT_DIR / f"{uuid.uuid4()}.mp3"
    subprocess.run([
        "ffmpeg",
        "-i", str(music_path),
        "-i", str(voiceover_path),
        "-filter_complex", "[0:a]volume=0.1[music];[music][1:a]amix=inputs=2:duration=first[out]",
        "-map", "[out]",
        "-t", str(duration),
        "-y",
        str(out_path)
    ], check=True, capture_output=True)
    return out_path


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def read_root():
    return FileResponse("static/index.html")


@app.post("/generate-ad")
async def generate_ad(brand_id: int = Form(...)):
    brand = _get_brand(brand_id)

    # Get a voice and script in parallel
    script, voice_id = await asyncio.gather(
        _generate_ad_script(brand),
        _resolve_voice_id(brand["voice"]),
    )

    # Get voice read first so we know how much music we need
    voiceover_path = await _text_to_speech(script, voice_id)
    duration = _get_audio_duration(voiceover_path) + 1.0  # 1s buffer

    # Generate the music for the required duration
    music_path = await _generate_music(brand, duration)

    try:
        final_path = _mix_audio(voiceover_path, music_path, duration)
    finally:
        # Clean up temporary files
        voiceover_path.unlink(missing_ok=True)
        music_path.unlink(missing_ok=True)

    return JSONResponse({
        "audio_url": f"/static/generated/{final_path.name}",
        "script": script,
        "brand": brand["brandName"],
    })
