import asyncio
import os
import threading
import time
import wave

import edge_tts
import pyaudio
import pygame
import whisper

# ── 設定 ─────────────────────────────────────────
VOICE    = "en-US-JennyNeural"  # 読み上げ音声
RATE     = 16000                # 録音サンプルレート
CHANNELS = 1                    # モノラル
CHUNK    = 1024                 # 録音バッファサイズ
FORMAT   = pyaudio.paInt16      # 録音フォーマット


def _temp_path(filename: str) -> str:
    """tempフォルダのパスを返す（なければ作成）"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    temp_dir = os.path.join(base_dir, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    return os.path.join(temp_dir, filename)


def _safe_unlink(path: str) -> None:
    """ファイルを安全に削除する"""
    try:
        os.unlink(path)
    except Exception:
        pass


# ── Whisper ──────────────────────────────────────
_whisper_model = None


def _get_whisper_model() -> whisper.Whisper:
    global _whisper_model
    if _whisper_model is None:
        print("Whisperモデルを読み込み中...")
        _whisper_model = whisper.load_model("small")
        print("Whisperモデル読み込み完了")
    return _whisper_model


def _transcribe(wav_path: str) -> str:
    model  = _get_whisper_model()
    result = model.transcribe(wav_path, language="en", fp16=False)
    return result["text"].strip()


# ── 録音 ──────────────────────────────────────────
_frames:    list  = []
_recording: bool  = False
_stream           = None
_audio            = None


def start_recording() -> None:
    global _frames, _recording, _stream, _audio
    _frames.clear()
    _recording = True
    _audio     = pyaudio.PyAudio()
    _stream    = _audio.open(
        format=FORMAT, channels=CHANNELS,
        rate=RATE, input=True,
        frames_per_buffer=CHUNK
    )

    def _loop() -> None:
        while _recording:
            _frames.append(_stream.read(CHUNK, exception_on_overflow=False))

    threading.Thread(target=_loop, daemon=True).start()


def stop_recording() -> str:
    global _recording, _stream, _audio
    _recording = False

    if _stream:
        _stream.stop_stream()
        _stream.close()
    if _audio:
        _audio.terminate()

    if not _frames:
        return ""

    wav_path = _temp_path("rec.wav")
    with wave.open(wav_path, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(pyaudio.PyAudio().get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b"".join(_frames))

    _frames.clear()

    try:
        text = _transcribe(wav_path)
        print(f"認識結果: {text}")
        return text
    except Exception as e:
        print(f"Whisper error: {e}")
        return ""
    finally:
        _safe_unlink(wav_path)


# ── 読み上げ ──────────────────────────────────────
_tts_lock = threading.Lock()


def speak(text: str) -> None:
    def _run() -> None:
        with _tts_lock:
            asyncio.run(_speak_async(text))

    threading.Thread(target=_run, daemon=True).start()


async def _speak_async(text: str) -> None:
    tts_path = _temp_path("tts.mp3")
    try:
        await edge_tts.Communicate(text, voice=VOICE).save(tts_path)
        _play(tts_path)
    except Exception as e:
        print(f"TTS error: {e}")


def _play(path: str) -> None:
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        pygame.mixer.music.unload()
        pygame.mixer.quit()
    except Exception as e:
        print(f"再生エラー: {e}")
    finally:
        _safe_unlink(path)
