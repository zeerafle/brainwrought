"""Caching utilities for the pipeline."""

import json
from pathlib import Path
from typing import Any, Dict, Optional


class VoiceCache:
    """Simple file-based cache for designed voices."""

    def __init__(self, cache_dir: str = ".voice_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / "voice_cache.json"
        self._cache = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        """Load cache from disk."""
        if self.cache_file.exists():
            with open(self.cache_file, "r") as f:
                return json.load(f)
        return {}

    def _save_cache(self):
        """Save cache to disk."""
        with open(self.cache_file, "w") as f:
            json.dump(self._cache, f, indent=2)

    def get_cached_voice(self, voice_description: str, language: str) -> Optional[str]:
        """
        Get cached voice ID if available.

        Args:
            voice_description: Voice description used for design
            language: Language code

        Returns:
            Voice ID string if cached, None otherwise
        """
        cache_key = f"{language}:{voice_description}"
        cached_data = self._cache.get(cache_key)
        if cached_data and isinstance(cached_data, dict):
            return cached_data.get("voice_id")
        return None

    def cache_voice(self, voice_description: str, language: str, voice_id: str):
        """
        Cache a designed voice.

        Args:
            voice_description: Voice description used for design
            language: Language code
            voice_id: ElevenLabs voice ID
        """
        cache_key = f"{language}:{voice_description}"
        self._cache[cache_key] = {
            "voice_id": voice_id,
            "description": voice_description,
            "language": language,
        }
        self._save_cache()
        print(f"💾 Cached voice: {cache_key} -> {voice_id}")
