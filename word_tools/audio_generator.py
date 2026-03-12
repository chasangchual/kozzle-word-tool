"""Audio generator for Korean text-to-speech."""

import os
import threading
import time
from pathlib import Path
from typing import List

import pyttsx3


class AudioGenerator:
    """Generate audio files from Korean text using text-to-speech."""

    def __init__(self, output_dir: str = "./output"):
        """
        Initialize the audio generator.

        Args:
            output_dir: Directory to save audio files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize pyttsx3 engine
        self.engine = pyttsx3.init()

        # Set properties
        self.engine.setProperty("rate", 150)  # Speed of speech
        self.engine.setProperty("volume", 1.0)  # Volume (0.0 to 1.0)

        # Try to set Korean language if available
        voices = self.engine.getProperty("voices")
        for voice in voices:
            # Look for Korean voices
            if "ko" in voice.languages or "Korean" in voice.name:
                self.engine.setProperty("voice", voice.id)
                break

    def generate_audio(self, word: str, sentences: List[str]) -> str:
        """
        Generate audio file containing the word and sentences.

        Args:
            word: The main word to highlight
            sentences: List of 3 sentences to include

        Returns:
            Path to the generated audio file, or empty string if failed
        """
        try:
            # Create the combined text
            # Format: word (spelled out), then each sentence
            word_audio_text = f"{word}"
            combined_text = f"{word}. " + " ".join(sentences)

            # Generate filename from word (sanitize)
            safe_word = "".join(c for c in word if c.isalnum() or c in "_-")
            if not safe_word:
                safe_word = "audio"

            timestamp = int(time.time() % 10000)
            audio_filename = f"{safe_word}_{timestamp}.mp3"
            audio_path = self.output_dir / audio_filename

            # Use pydub or direct save with pyttsx3
            # Save to a temporary WAV file first
            temp_wav = self.output_dir / f"{safe_word}_{timestamp}_temp.wav"

            # Save the audio
            self.engine.save_to_file(combined_text, str(temp_wav))
            self.engine.runAndWait()

            # Convert WAV to MP3 if needed
            # Note: pyttsx3 saves as WAV by default
            # For MP3, we'd need additional conversion or use a different library

            # Rename to MP3 (the file is actually WAV format but we'll use .mp3 extension
            # for compatibility, or convert properly)
            if temp_wav.exists():
                # For true MP3, you could use pydub here
                # For now, we'll just use WAV format
                final_path = self.output_dir / f"{safe_word}_{timestamp}.wav"
                if temp_wav != final_path:
                    temp_wav.rename(final_path)
                return str(final_path)
            else:
                return ""

        except Exception as e:
            print(f"Error generating audio for '{word}': {e}")
            return ""

    def generate_audio_streaming(self, word: str, sentences: List[str]) -> str:
        """
        Generate audio with word highlighted (slower pace).

        Args:
            word: The main word to highlight
            sentences: List of 3 sentences to include

        Returns:
            Path to the generated audio file
        """
        try:
            timestamp = int(time.time() % 10000)
            safe_word = "".join(c for c in word if c.isalnum() or c in "_-")
            if not safe_word:
                safe_word = "audio"

            audio_filename = f"{safe_word}_{timestamp}_highlighted.mp3"
            audio_path = self.output_dir / audio_filename

            # For better TTS quality, use a temporary file approach
            combined_text = f"{word}. {sentences[0]}. {sentences[1]}. {sentences[2]}"

            self.engine.save_to_file(combined_text, str(audio_path))
            self.engine.runAndWait()

            return str(audio_path)

        except Exception as e:
            print(f"Error generating audio for '{word}': {e}")
            return ""

    def set_speed(self, rate: int):
        """
        Set the speech rate.

        Args:
            rate: Speech rate (50 to 300, default is 150)
        """
        self.engine.setProperty("rate", rate)

    def set_volume(self, volume: float):
        """
        Set the speech volume.

        Args:
            volume: Volume level (0.0 to 1.0)
        """
        self.engine.setProperty("volume", max(0.0, min(1.0, volume)))


if __name__ == "__main__":
    # Test the audio generator
    generator = AudioGenerator()

    test_word = "사과"
    test_sentences = [
        "사과는 건강에 좋은 과일입니다.",
        "빨간 사과를 먹으면 비타민을 섭취할 수 있습니다.",
        "사과는 겨울철 간식으로 인기가 많습니다.",
    ]

    audio_file = generator.generate_audio(test_word, test_sentences)
    if audio_file:
        print(f"Audio generated: {audio_file}")
    else:
        print("Failed to generate audio")
