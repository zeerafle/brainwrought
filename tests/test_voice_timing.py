"""
Simple integration tests for voice generation - English and Turkish only.
Uses REAL API calls with Voice Design (no mocks).

Prerequisites:
    - ELEVENLABS_API_KEY environment variable
    - GOOGLE_API_KEY or OPENAI_API_KEY for LLM

Run:
    pytest tests/test_voice_timing_simple.py -v -s

Audio files saved to: test_audio_output/
Files are kept so you can listen to them manually.
"""

import os
from pathlib import Path

import pytest
from src.agents.production_agents import voice_and_timing_node

from src.config import get_llm


@pytest.fixture
def audio_output_dir():
    """Persistent directory for audio output."""
    output_dir = Path("test_audio_output")
    output_dir.mkdir(exist_ok=True)
    print(f"\n📁 Audio directory: {output_dir.absolute()}")
    return str(output_dir)


def test_english_voice_generation(audio_output_dir):
    """
    Test English voice generation with Voice Design.

    Run: pytest tests/test_voice_timing_simple.py::test_english_voice_generation -v -s
    """
    # Check API keys
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        pytest.skip("ELEVENLABS_API_KEY not set")

    llm = get_llm()

    # State matching Scene structure from states.py
    state = {
        "scenes": [
            {
                "scene_number": 1,
                "on_screen_action": "Camera zooms into a floating apple",
                "dialogue_vo": "Did you know gravity isn't actually a force?",
            },
            {
                "scene_number": 2,
                "on_screen_action": "Einstein appears with curved spacetime visualization",
                "dialogue_vo": "Einstein showed us it's actually curved spacetime!",
            },
        ],
        "audience_profile": {
            "core_persona": {
                "name": "Curious Student",
                "age_range": "16-24",
            },
            "voice_tone_description": "energetic, friendly, clear",
            "production_style": {
                "audio_style": "dynamic and engaging",
                "pacing": "moderate",
            },
        },
        "language": "en",
    }

    print("\n🇺🇸 Testing English voice generation with Voice Design...")

    # Generate audio WITH voice design
    result = voice_and_timing_node(
        state=state,
        llm=llm,
        elevenlabs_api_key=api_key,
        output_dir=audio_output_dir,
        use_voice_design=True,  # Enable voice design
        voice_design_preview_index=0,  # Use first preview
    )

    # Verify results
    assert "voice_timing" in result
    assert len(result["voice_timing"]) == 2

    print("\n✅ English audio generated:")
    for scene_result in result["voice_timing"]:
        if "error" in scene_result:
            pytest.fail(f"❌ Error: {scene_result['error']}")

        print(f"\n   Scene {scene_result['scene_id']}:")
        print(f"   📝 Text: {scene_result['text']}")
        print(f"   ⏱️  Duration: {scene_result.get('duration_seconds', 0):.2f}s")
        print(f"   🎵 File: {scene_result.get('audio_path', 'N/A')}")

        # Show voice config
        voice_config = scene_result.get("voice_config", {})
        if voice_config:
            print(f"   🎙️  Voice: {voice_config.get('source', 'unknown')}")
            if voice_config.get("description"):
                print(f"   💬 Description: {voice_config['description'][:80]}...")

        # Verify file
        if scene_result.get("audio_path"):
            audio_path = Path(scene_result["audio_path"])
            assert audio_path.exists(), f"Audio file not found: {audio_path}"
            assert audio_path.stat().st_size > 0, "Audio file is empty"
            print(f"   💾 Size: {audio_path.stat().st_size:,} bytes")

    # Print play instructions
    first_audio = Path(result["voice_timing"][0]["audio_path"])
    print("\n🔊 Play manually:")
    print(f"   macOS:   afplay '{first_audio}'")
    print(f"   Linux:   mpg123 '{first_audio}'")
    print(f"   Windows: start '{first_audio}'")


def test_turkish_voice_generation(audio_output_dir):
    """
    Test Turkish voice generation with Voice Design.

    Run: pytest tests/test_voice_timing_simple.py::test_turkish_voice_generation -v -s
    """
    # Check API keys
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        pytest.skip("ELEVENLABS_API_KEY not set")

    llm = get_llm()

    # Turkish state matching Scene structure
    state = {
        "scenes": [
            {
                "scene_number": 1,
                "on_screen_action": "Yere düşen elma görseli",
                "dialogue_vo": "Yerçekimi aslında bir kuvvet değil, biliyor muydunuz?",
            },
            {
                "scene_number": 2,
                "on_screen_action": "Einstein'ın eğri uzay-zaman görselleştirmesi",
                "dialogue_vo": "Einstein bize bunun aslında eğri uzay-zaman olduğunu gösterdi!",
            },
        ],
        "audience_profile": {
            "core_persona": {
                "name": "Meraklı Öğrenci",
                "age_range": "16-24",
            },
            "voice_tone_description": "enerjik, samimi, açık",
            "production_style": {
                "audio_style": "dinamik ve ilgi çekici",
                "pacing": "orta",
            },
        },
        "language": "tr",
    }

    print("\n🇹🇷 Testing Turkish voice generation with Voice Design...")

    # Generate audio WITH voice design
    result = voice_and_timing_node(
        state=state,
        llm=llm,
        elevenlabs_api_key=api_key,
        output_dir=audio_output_dir,
        use_voice_design=True,  # Enable voice design
        voice_design_preview_index=0,  # Use first preview
    )

    # Verify results
    assert "voice_timing" in result
    assert len(result["voice_timing"]) == 2

    print("\n✅ Turkish audio generated:")
    for scene_result in result["voice_timing"]:
        if "error" in scene_result:
            pytest.fail(f"❌ Hata: {scene_result['error']}")

        print(f"\n   Sahne {scene_result['scene_id']}:")
        print(f"   📝 Metin: {scene_result['text']}")
        print(f"   ⏱️  Süre: {scene_result.get('duration_seconds', 0):.2f}s")
        print(f"   🎵 Dosya: {scene_result.get('audio_path', 'N/A')}")

        # Show voice config
        voice_config = scene_result.get("voice_config", {})
        if voice_config:
            print(f"   🎙️  Ses: {voice_config.get('source', 'bilinmiyor')}")
            if voice_config.get("description"):
                print(f"   💬 Açıklama: {voice_config['description'][:80]}...")

        # Verify file
        if scene_result.get("audio_path"):
            audio_path = Path(scene_result["audio_path"])
            assert audio_path.exists(), f"Ses dosyası bulunamadı: {audio_path}"
            assert audio_path.stat().st_size > 0, "Ses dosyası boş"
            print(f"   💾 Boyut: {audio_path.stat().st_size:,} bytes")

    # Print play instructions
    first_audio = Path(result["voice_timing"][0]["audio_path"])
    print("\n🔊 Manuel olarak dinleyin:")
    print(f"   macOS:   afplay '{first_audio}'")
    print(f"   Linux:   mpg123 '{first_audio}'")
    print(f"   Windows: start '{first_audio}'")


def test_both_languages_with_voice_design(audio_output_dir):
    """
    Test both English and Turkish with Voice Design for comparison.

    Run: pytest tests/test_voice_timing_simple.py::test_both_languages_with_voice_design -v -s
    """
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        pytest.skip("ELEVENLABS_API_KEY not set")

    llm = get_llm()

    results = {}

    # Test both languages with voice design
    languages = {
        "en": {
            "flag": "🇺🇸",
            "scene_action": "Gravity demonstration",
            "dialogue": "Gravity is fascinating!",
            "on_screen": "🍎 GRAVITY",
            "persona_name": "Curious Student",
            "voice_tone": "energetic and clear",
            "audio_style": "engaging",
            "pacing": "moderate",
        },
        "tr": {
            "flag": "🇹🇷",
            "scene_action": "Yerçekimi gösterimi",
            "dialogue": "Yerçekimi büyüleyici!",
            "on_screen": "🍎 YERÇEKİMİ",
            "persona_name": "Meraklı Öğrenci",
            "voice_tone": "enerjik ve açık",
            "audio_style": "ilgi çekici",
            "pacing": "orta",
        },
    }

    for lang, content in languages.items():
        print(
            f"\n{content['flag']} Generating {lang.upper()} audio with Voice Design..."
        )

        state = {
            "scenes": [
                {
                    "scene_number": 1,
                    "on_screen_action": content["scene_action"],
                    "dialogue_vo": content["dialogue"],
                }
            ],
            "audience_profile": {
                "core_persona": {"name": content["persona_name"], "age_range": "16-24"},
                "voice_tone_description": content["voice_tone"],
                "production_style": {
                    "audio_style": content["audio_style"],
                    "pacing": content["pacing"],
                },
            },
            "language": lang,
        }

        result = voice_and_timing_node(
            state=state,
            llm=llm,
            elevenlabs_api_key=api_key,
            output_dir=audio_output_dir,
            use_voice_design=True,  # Enable voice design
            voice_design_preview_index=0,
        )

        if result["voice_timing"] and "error" not in result["voice_timing"][0]:
            results[lang] = result["voice_timing"][0]
            print(
                f"   ✅ Success! Duration: {results[lang].get('duration_seconds', 0):.2f}s"
            )

            # Show voice design info
            voice_config = results[lang].get("voice_config", {})
            if voice_config.get("source") == "designed":
                print("   🎨 Custom voice designed and cached!")

    # Summary
    print(f"\n{'=' * 60}")
    print("📊 Comparison Summary:")
    print(f"{'=' * 60}")

    for lang, scene_result in results.items():
        audio_path = scene_result.get("audio_path")
        duration = scene_result.get("duration_seconds", 0)
        voice_config = scene_result.get("voice_config", {})

        print(f"\n{languages[lang]['flag']} {lang.upper()}:")
        print(f"   Duration: {duration:.2f}s")
        print(f"   Voice: {voice_config.get('source', 'unknown')}")
        print(f"   File: {audio_path}")

    # Verify both succeeded
    assert len(results) == 2, f"Expected 2 languages, got {len(results)}"

    print(f"\n{'=' * 60}")
    print("✅ Both languages generated successfully with Voice Design!")
    print(f"{'=' * 60}")

    # Print play instructions
    print("\n🔊 Listen to them manually:")
    for lang, scene_result in results.items():
        audio_path = scene_result.get("audio_path")
        if audio_path:
            print(f"   {languages[lang]['flag']} {lang.upper()}: afplay '{audio_path}'")

    print("\n💡 Tip: Custom voices are cached in .voice_cache/")
    print("    Next run will be faster!")


if __name__ == "__main__":
    import sys

    pytest.main([__file__, "-v", "-s"] + sys.argv[1:])
