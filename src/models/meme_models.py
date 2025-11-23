"""Pydantic models for meme and trends analysis."""

from typing import List

from pydantic import BaseModel, Field


class ViralExample(BaseModel):
    """A single viral content example."""

    url: str = Field(description="URL to the viral content")
    platform: str = Field(description="Platform (tiktok, twitter, bluesky)")
    engagement_metrics: str = Field(description="Likes, views, shares, etc.")
    hook_or_format: str = Field(description="The hook line or format used")


class TrendsAnalysis(BaseModel):
    """Structured analysis of social media trends."""

    viral_examples: List[ViralExample] = Field(
        description="3-5 viral content examples", min_length=3, max_length=5
    )
    common_hooks: List[str] = Field(
        description="Common opening lines or hooks", min_length=3
    )
    trending_formats: List[str] = Field(description="Popular content formats or memes")
    recommendations: List[str] = Field(
        description="Specific recommendations for content creation"
    )


class SlangTerm(BaseModel):
    """A slang term with its meaning and usage."""

    term: str = Field(description="The slang term or expression")
    meaning: str = Field(description="What the term means")
    usage_example: str = Field(description="Example of how to use it")


class LanguageSlang(BaseModel):
    """Current slang and language trends."""

    language: str = Field(description="Target language")
    slang_terms: List[SlangTerm] = Field(
        description="List of current slang terms with meanings and examples",
        min_length=5,
    )
    trending_phrases: List[str] = Field(
        description="Currently trending phrases or expressions"
    )
    cultural_context: str = Field(description="Brief cultural context for the slang")


class HookConcept(BaseModel):
    """Hook concepts for short-form content."""

    ideas: List[str] = Field(
        description="List of hook ideas", min_length=3, max_length=5
    )


class MemeConceptDetails(BaseModel):
    """Details for a single meme concept."""

    meme_name_reference: str = Field(description="The name or reference of the meme")
    text_to_add: List[str] = Field(description="The text to add to the meme")


class MemeConcept(BaseModel):
    """Collection of meme concepts."""

    meme_concepts: List[MemeConceptDetails] = Field(
        description="List of meme name/reference and its additional text",
        min_length=3,
        max_length=5,
    )
