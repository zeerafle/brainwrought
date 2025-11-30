"""Test script for meme generation using imgflip MCP."""

import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from assets import generate_meme_assets_node

# Load environment variables from .env file
load_dotenv()


def main():
    """Run a simple test of meme generation."""

    # Check for required environment variables
    if not os.getenv("IMGFLIP_USERNAME") or not os.getenv("IMGFLIP_PASSWORD"):
        print(
            "❌ Please set IMGFLIP_USERNAME and IMGFLIP_PASSWORD environment variables"
        )
        print("   You can create a free account at https://imgflip.com/signup")
        return

    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Please set OPENAI_API_KEY environment variable")
        return

    # Initialize the LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # Mock meme concepts input (matching the format from MemeConceptDetails)
    mock_meme_concepts = [
        {
            "meme_name_reference": "Drake Hotline Bling (reject/approve)",
            "text_to_add": [
                "Guessing random weights",
                "Using backpropagation",
            ],
        },
        {
            "meme_name_reference": "Distracted Boyfriend (choice/confusion)",
            "text_to_add": [
                "Me",
                "New JavaScript framework",
                "My current project",
            ],
        },
        {
            "meme_name_reference": "Expanding Brain",
            "text_to_add": [
                "Print debugging",
                "Using a debugger",
                "Writing unit tests",
                "Reading the error message",
            ],
        },
    ]

    # Create the mock state
    mock_state = {
        "meme_concepts": mock_meme_concepts,
    }

    print("=" * 60)
    print("🧪 Testing Meme Generation with imgflip MCP")
    print("=" * 60)
    print(f"\n📋 Input meme concepts: {len(mock_meme_concepts)}")
    for i, concept in enumerate(mock_meme_concepts, 1):
        print(f"\n   {i}. {concept['meme_name_reference']}")
        for text in concept["text_to_add"]:
            print(f"      - {text}")

    print("\n" + "-" * 60)
    print("🚀 Starting meme generation...")
    print("-" * 60 + "\n")

    # Run the meme generation
    result = generate_meme_assets_node(mock_state, llm)

    # Display results
    print("\n" + "=" * 60)
    print("📊 Results")
    print("=" * 60)

    generated_memes = result.get("generated_memes", [])

    if not generated_memes:
        print("\n❌ No memes were generated")
        return

    for meme in generated_memes:
        print(f"\n🖼️  {meme.get('meme_name_reference', 'Unknown')}")
        if meme.get("success"):
            print(f"   ✅ URL: {meme.get('meme_url')}")
        else:
            print(f"   ❌ Error: {meme.get('error', 'Unknown error')}")
            if meme.get("raw_response"):
                print(f"   📝 Response: {meme.get('raw_response')[:200]}...")

    # Summary
    successful = sum(1 for m in generated_memes if m.get("success"))
    print(
        f"\n📈 Summary: {successful}/{len(generated_memes)} memes generated successfully"
    )


if __name__ == "__main__":
    main()
