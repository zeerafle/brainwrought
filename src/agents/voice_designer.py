"""
Voice Design integration with ElevenLabs for persona-driven custom voice generation.
Supports multi-language voice generation based on content language.
"""

import os
from typing import Any, Dict, Optional

from elevenlabs import ElevenLabs
from pydantic import BaseModel, Field

from src.states import AudienceProfile


class VoiceDesignConfig(BaseModel):
    """Configuration for voice design generation."""

    voice_description: str = Field(
        description="Detailed description of the desired voice characteristics"
    )
    text_sample: Optional[str] = Field(
        default=None,
        description="Sample text for voice preview (100-1000 chars). Auto-generated if None.",
    )
    model_id: str = Field(
        default="eleven_multilingual_ttv_v2",
        description="Model to use for voice generation",
    )
    loudness: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="Volume level: -1 quietest, 0 normal (~-24 LUFS), 1 loudest",
    )
    quality: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Quality vs variety tradeoff: higher = better quality, less variety",
    )
    guidance_scale: float = Field(
        default=2.0,
        ge=0.0,
        le=5.0,
        description="Prompt adherence: lower = more creative, higher = more literal",
    )
    seed: Optional[int] = Field(default=None, description="Seed for reproducibility")
    num_previews: int = Field(
        default=3, ge=1, le=5, description="Number of voice previews to generate"
    )


class VoiceDesigner:
    """
    Designs custom voices based on audience persona and content language.
    Uses ElevenLabs Voice Design API for maximum flexibility.
    """

    # Language-specific voice characteristics
    # Language-specific voice characteristics
    LANGUAGE_CONFIGS = {
        "en": {
            "model": "eleven_multilingual_ttv_v2",
            "accent_descriptors": ["American", "British", "neutral"],
            "sample_text": "Hello! Welcome to this educational content. Let's explore some fascinating concepts together and make learning fun and engaging.",
        },
        "tr": {
            "model": "eleven_multilingual_ttv_v2",
            "accent_descriptors": ["Turkish", "Istanbul", "Ankara"],
            "sample_text": "Merhaba! Bu eğitim içeriğine hoş geldiniz. Birlikte büyüleyici kavramları keşfedelim ve öğrenmeyi eğlenceli ve ilgi çekici hale getirelim.",
        },
        "es": {
            "model": "eleven_multilingual_ttv_v2",
            "accent_descriptors": ["Spanish", "Latin American", "Castilian"],
            "sample_text": "¡Hola! Bienvenido a este contenido educativo. Vamos a explorar conceptos fascinantes juntos y hacer que el aprendizaje sea divertido y atractivo.",
        },
        "fr": {
            "model": "eleven_multilingual_ttv_v2",
            "accent_descriptors": ["French", "Parisian", "neutral"],
            "sample_text": "Bonjour! Bienvenue dans ce contenu éducatif. Explorons ensemble des concepts fascinants et rendons l'apprentissage amusant et engageant.",
        },
        "de": {
            "model": "eleven_multilingual_ttv_v2",
            "accent_descriptors": ["German", "neutral"],
            "sample_text": "Hallo! Willkommen zu diesem Bildungsinhalt. Lassen Sie uns gemeinsam faszinierende Konzepte erkunden und das Lernen unterhaltsam und ansprechend gestalten.",
        },
        "ja": {
            "model": "eleven_multilingual_ttv_v2",
            "accent_descriptors": ["Japanese", "Tokyo", "neutral"],
            "sample_text": "こんにちは！この教育コンテンツへようこそ。魅力的な概念を一緒に探求し、学習を楽しく魅力的にしましょう。",
        },
        "zh": {
            "model": "eleven_multilingual_ttv_v2",
            "accent_descriptors": ["Mandarin", "Beijing", "neutral"],
            "sample_text": "你好！欢迎来到这个教育内容。让我们一起探索一些迷人的概念，让学习变得有趣和吸引人。",
        },
        "ko": {
            "model": "eleven_multilingual_ttv_v2",
            "accent_descriptors": ["Korean", "Seoul", "neutral"],
            "sample_text": "안녕하세요! 이 교육 콘텐츠에 오신 것을 환영합니다. 매혹적인 개념을 함께 탐구하고 학습을 재미있고 매력적으로 만들어 봅시다.",
        },
        "pt": {
            "model": "eleven_multilingual_ttv_v2",
            "accent_descriptors": ["Portuguese", "Brazilian", "European"],
            "sample_text": "Olá! Bem-vindo a este conteúdo educacional. Vamos explorar conceitos fascinantes juntos e tornar o aprendizado divertido e envolvente.",
        },
        # Fallback for any language
        "default": {
            "model": "eleven_multilingual_ttv_v2",
            "accent_descriptors": ["neutral", "international"],
            "sample_text": "Welcome to this educational content. Let's make learning engaging and fun together.",
        },
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        audience_profile: Optional[AudienceProfile] = None,
        language: str = "en",
    ):
        """
        Initialize Voice Designer.

        Args:
            api_key: ElevenLabs API key (defaults to env var)
            audience_profile: Audience profile to base voice on
            language: ISO 639-1 language code (e.g., 'en', 'es', 'ja')
        """
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        self.client = ElevenLabs(api_key=self.api_key) if self.api_key else None
        self.audience_profile = audience_profile
        self.language = language.lower()[:2]  # Ensure 2-letter code

    def generate_voice_description(self) -> str:
        """
        Generate a detailed voice description prompt from audience persona.

        Returns:
            Detailed voice description string for ElevenLabs API
        """
        if not self.audience_profile:
            return (
                "A clear, friendly, and engaging voice perfect for educational content."
            )

        core_persona = self.audience_profile.get("core_persona", {})
        voice_tone = self.audience_profile.get("voice_tone_description", "")
        production_style = self.audience_profile.get("production_style", {})

        # Extract persona characteristics
        age_range = core_persona.get("age_range", "").lower()
        audio_style = production_style.get("audio_style", "").lower()
        pacing = production_style.get("pacing", "").lower()

        # Build description components
        components = []

        # Age/demographic
        if any(term in age_range for term in ["13-17", "teen", "young"]):
            components.append("A youthful, energetic voice")
        elif any(term in age_range for term in ["18-24", "gen-z"]):
            components.append("A young adult voice, relatable and modern")
        elif any(term in age_range for term in ["25-40", "millennial"]):
            components.append("A mature, professional yet approachable voice")
        else:
            components.append("A versatile, engaging voice")

        # Voice tone characteristics
        if voice_tone:
            components.append(f"with a tone that is {voice_tone}")

        # Audio style attributes
        if "energetic" in audio_style or "dynamic" in audio_style:
            components.append("full of energy and enthusiasm")
        if "calm" in audio_style or "soothing" in audio_style:
            components.append("calm and reassuring")
        if "professional" in audio_style or "authoritative" in audio_style:
            components.append("confident and authoritative")
        if "friendly" in audio_style or "warm" in audio_style:
            components.append("warm and friendly")

        # Pacing
        if "fast" in pacing:
            components.append("speaking at a brisk, engaging pace")
        elif "slow" in pacing:
            components.append("speaking deliberately and clearly")
        else:
            components.append("with a comfortable, natural pace")

        # Language/accent
        lang_config = self.LANGUAGE_CONFIGS.get(
            self.language, self.LANGUAGE_CONFIGS["default"]
        )
        accent = lang_config["accent_descriptors"][0]
        components.append(f"with a {accent} accent")

        # Educational context
        components.append("perfect for educational and entertaining content")

        # Join all components
        description = ", ".join(components) + "."

        return description

    def design_voice(
        self,
        custom_description: Optional[str] = None,
        custom_sample_text: Optional[str] = None,
        preview_selection_index: int = 0,
    ) -> Dict[str, Any]:
        """
        Design a custom voice using Voice Design API.

        Args:
            custom_description: Override auto-generated description
            custom_sample_text: Custom sample text for preview
            preview_selection_index: Which preview to select (0-based)

        Returns:
            Dict with voice_id, previews, and configuration info
        """
        if not self.client:
            raise ValueError("ElevenLabs API key not provided")

        # Generate voice description
        voice_description = custom_description or self.generate_voice_description()

        # Get language-specific config
        lang_config = self.LANGUAGE_CONFIGS.get(
            self.language, self.LANGUAGE_CONFIGS["default"]
        )

        # Use custom sample or language-specific default
        sample_text = custom_sample_text or lang_config["sample_text"]

        # Ensure text is within length requirements (100-1000 chars)
        if len(sample_text) < 100:
            sample_text = sample_text * (100 // len(sample_text) + 1)
        sample_text = sample_text[:1000]

        print(f"🎨 Designing voice with description: {voice_description}")
        print(f"🌍 Language: {self.language}")
        print(f"📝 Sample text: {sample_text[:100]}...")

        # Generate voice previews
        try:
            response = self.client.text_to_voice.design(
                model_id=lang_config["model"],
                voice_description=voice_description,
                text=sample_text,
                output_format="mp3_44100_128",
                auto_generate_text=False,
                loudness=0.0,
                quality=0.6,  # Higher quality for educational content
                guidance_scale=2.5,  # Moderate guidance - balanced
            )

            print(f"✅ Generated {len(response.previews)} voice previews")

            # Save previews for review
            previews = []
            for i, preview in enumerate(response.previews):
                preview_data = {
                    "index": i,
                    "generated_voice_id": preview.generated_voice_id,
                    "audio_base64": preview.audio_base_64,
                    "preview_url": getattr(preview, "preview_url", None),
                }
                previews.append(preview_data)

            # Select the specified preview
            selected_preview = previews[preview_selection_index]

            return {
                "success": True,
                "voice_description": voice_description,
                "language": self.language,
                "selected_generated_voice_id": selected_preview["generated_voice_id"],
                "all_previews": previews,
                "model_id": lang_config["model"],
            }

        except Exception as e:
            print(f"❌ Voice design failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "voice_description": voice_description,
            }

    def create_voice_from_design(
        self,
        generated_voice_id: str,
        voice_name: str,
        voice_description: Optional[str] = None,
    ) -> str:
        """
        Create a permanent voice from a generated preview.

        Args:
            generated_voice_id: ID from design() preview
            voice_name: Name for the new voice
            voice_description: Description (defaults to auto-generated)

        Returns:
            Permanent voice_id that can be used for TTS
        """
        if not self.client:
            raise ValueError("ElevenLabs API key not provided")

        description = voice_description or self.generate_voice_description()

        try:
            response = self.client.text_to_voice.create(
                voice_name=voice_name,
                voice_description=description,
                generated_voice_id=generated_voice_id,
            )

            print(f"✅ Created voice '{voice_name}' with ID: {response.voice_id}")

            return response.voice_id

        except Exception as e:
            print(f"❌ Voice creation failed: {e}")
            raise
