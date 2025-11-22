import os
import random
from pathlib import Path
from typing import Any, Dict, List

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_tavily import TavilySearch
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field

from agents.llm_utils import structured_llm_call


# Shared MCP client initialization
def _get_mcp_client() -> MultiServerMCPClient:
    """Initialize MCP client with all social media servers."""
    project_root = Path(__file__).parent.parent.parent
    tiktok_mcp_path = project_root / "mcp-servers" / "tiktok-mcp" / "build" / "index.js"

    if not tiktok_mcp_path.exists():
        raise FileNotFoundError(
            f"TikTok MCP not found at {tiktok_mcp_path}. "
            "Please build it first: cd mcp-servers/tiktok-mcp && npm run build"
        )

    return MultiServerMCPClient(
        {  # pyright: ignore[reportArgumentType]
            "bsky-mcp-server": {
                "transport": "stdio",
                "command": "npx",
                "args": [
                    "-y",
                    "@smithery/cli@latest",
                    "run",
                    "@brianellin/bsky-mcp-server",
                    "--key",
                    os.getenv("SMITHERY_API_KEY"),
                    "--profile",
                    "icy-dingo-7Py8Pi",
                ],
            },
            "tiktok-mcp": {
                "transport": "stdio",
                "command": "node",
                "args": [str(tiktok_mcp_path)],
                "env": {
                    "TIKNEURON_MCP_API_KEY": os.getenv("TIKNEURON_MCP_API_KEY", "")
                },
            },
            "x-twitter-mcp-server": {
                "transport": "stdio",
                "command": "npx",
                "args": [
                    "-y",
                    "@smithery/cli@latest",
                    "run",
                    "@rafaljanicki/x-twitter-mcp-server",
                    "--key",
                    os.getenv("SMITHERY_API_KEY"),
                    "--profile",
                    "icy-dingo-7Py8Pi",
                ],
            },
        },
    )


# Structured output models
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


class LanguageSlang(BaseModel):
    """Current slang and language trends."""

    language: str = Field(description="Target language")
    slang_terms: List[Dict[str, str]] = Field(
        description="List of dicts with keys: term, meaning, usage_example",
        min_length=5,
    )
    trending_phrases: List[str] = Field(
        description="Currently trending phrases or expressions"
    )
    cultural_context: str = Field(description="Brief cultural context for the slang")


# Extended state to hold structured outputs
class TrendsAgentState(MessagesState):
    """State for trends analysis agent."""

    final_analysis: TrendsAnalysis | None


class SlangAgentState(MessagesState):
    """State for slang analysis agent."""

    final_slang: LanguageSlang | None


async def social_media_trends_node(
    state: Dict[str, Any], llm: BaseChatModel
) -> Dict[str, Any]:
    """
    Analyze current social media trends using tools, then return structured output.
    """
    pages = state.get("pages", [])
    summary = state.get("summary", "")

    pages_snippets = [page for page in random.sample(pages, min(len(pages), 5))]
    content_snippets = ". ".join([p[:200] for p in pages_snippets])
    topic_context = summary[:500] if summary else content_snippets[:500]

    # Initialize tools
    tavily_tool = TavilySearch(max_results=5, topic="general")
    mcp_client = _get_mcp_client()

    mcp_tools = await mcp_client.get_tools()
    all_tools = [tavily_tool, *mcp_tools]

    # Step 1: Tool-calling agent (collects data)
    def call_model(agent_state: TrendsAgentState):
        """Agent that uses tools to research trends."""
        response = llm.bind_tools(all_tools).invoke(agent_state["messages"])
        return {"messages": [response]}

    # Step 2: Structured output node (formats the response)
    def respond_structured(agent_state: TrendsAgentState):
        """Convert tool results into structured output."""
        # Get all the conversation history with tool results
        llm_with_structure = llm.with_structured_output(TrendsAnalysis)

        # Create a prompt to structure the gathered information
        structure_prompt = HumanMessage(
            content="""Based on the research above, provide a structured analysis with:
            - 3-5 viral examples (with URLs, platform, metrics, and hooks)
            - Common hooks found
            - Trending formats
            - Specific recommendations

            Use ONLY information from the tool results above."""
        )

        response = llm_with_structure.invoke(
            agent_state["messages"] + [structure_prompt]
        )
        return {"final_analysis": response}

    # Step 3: Routing logic
    def should_continue(agent_state: TrendsAgentState):
        """Decide if we need more tools or can respond."""
        messages = agent_state["messages"]
        last_message = messages[-1]
        # If no tool calls, move to structured response
        if not last_message.tool_calls:
            return "respond"
        # Otherwise continue with tools
        return "continue"

    # Build the graph
    builder = StateGraph(TrendsAgentState)
    builder.add_node("agent", call_model)
    builder.add_node("tools", ToolNode(all_tools))
    builder.add_node("respond", respond_structured)

    builder.add_edge(START, "agent")
    builder.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "tools",
            "respond": "respond",
        },
    )
    builder.add_edge("tools", "agent")
    builder.add_edge("respond", END)

    graph = builder.compile()

    # Initial messages
    system_msg = SystemMessage(
        content="""You are a social media trend analyst for educational content.

Use the available tools to research current trends:
1. Search TikTok for viral educational videos
2. Get details on the most viral ones
3. Search web for meme trends

When done researching, say "I have completed my research" and I'll ask you to structure it."""
    )

    user_msg = HumanMessage(
        content=f"""Research viral trends for educational content about: {topic_context}

Find at least 3 viral examples with their URLs and metrics."""
    )

    try:
        # Invoke the graph
        result = await graph.ainvoke(
            {"messages": [system_msg, user_msg]}, {"recursion_limit": 15}
        )

        # Return the structured output
        final_analysis = result.get("final_analysis")

        return {
            "trends_analysis": final_analysis,
            "trends_analysis_complete": True,
        }

    except Exception as e:
        print(f"❌ Error during trend analysis: {e}")
        import traceback

        traceback.print_exc()
        return {
            "trends_analysis": None,
            "trends_analysis_complete": False,
            "error": str(e),
        }


async def language_slang_node(
    state: Dict[str, Any], llm: BaseChatModel
) -> Dict[str, Any]:
    """
    Search for language-specific slang with structured output.
    """
    language = state.get("language", "English")
    topic_context = state.get("summary", "")[:500]

    # Initialize tools
    tavily_tool = TavilySearch(max_results=5, topic="general")
    mcp_client = _get_mcp_client()

    mcp_tools = await mcp_client.get_tools()
    all_tools = [tavily_tool, *mcp_tools]

    # Tool-calling agent
    def call_model(agent_state: SlangAgentState):
        response = llm.bind_tools(all_tools).invoke(agent_state["messages"])
        return {"messages": [response]}

    # Structured output node
    def respond_structured(agent_state: SlangAgentState):
        llm_with_structure = llm.with_structured_output(LanguageSlang)

        structure_prompt = HumanMessage(
            content=f"""Based on the research above, provide structured {language} slang analysis with:
            - Language: {language}
            - At least 5 slang terms (each with term, meaning, usage_example)
            - Trending phrases
            - Cultural context

            Use ONLY information from the tool results above."""
        )

        response = llm_with_structure.invoke(
            agent_state["messages"] + [structure_prompt]
        )
        return {"final_slang": response}

    # Routing
    def should_continue(agent_state: SlangAgentState):
        if not agent_state["messages"][-1].tool_calls:
            return "respond"
        return "continue"

    # Build graph
    builder = StateGraph(SlangAgentState)
    builder.add_node("agent", call_model)
    builder.add_node("tools", ToolNode(all_tools))
    builder.add_node("respond", respond_structured)

    builder.add_edge(START, "agent")
    builder.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "tools",
            "respond": "respond",
        },
    )
    builder.add_edge("tools", "agent")
    builder.add_edge("respond", END)

    graph = builder.compile()

    # Messages
    system_msg = SystemMessage(
        content=f"""You are a {language} language expert researching current internet slang.

Use tools to research current {language} slang and meme expressions.
When done, say "Research complete" and I'll ask you to structure it."""
    )

    user_msg = HumanMessage(
        content=f"""Research current {language} slang for educational content about: {topic_context}

Find at least 5 slang terms with meanings and examples."""
    )

    try:
        result = await graph.ainvoke(
            {"messages": [system_msg, user_msg]}, {"recursion_limit": 15}
        )

        final_slang = result.get("final_slang")

        return {
            "slang_analysis": final_slang,
            "slang_analysis_complete": True,
        }

    except Exception as e:
        print(f"❌ Error during slang analysis: {e}")
        import traceback

        traceback.print_exc()
        return {
            "slang_analysis": None,
            "slang_analysis_complete": False,
            "error": str(e),
        }


class HookConcept(BaseModel):
    ideas: List[str] = Field(
        description="List of hook ideas", min_length=3, max_length=5
    )


def hook_concept_node(state: Dict[str, Any], llm: BaseChatModel) -> Dict[str, Any]:
    audience_profile = state.get("audience_profile")
    style_profile = state.get("style_profile")
    summary = state.get("summary")
    trend_analysis = state.get("trend_analysis")
    slang_analysis = state.get("slang_analysis")

    hooks = structured_llm_call(
        llm,
        "You write viral hooks concepts for short-form educational content",
        f"Using the following audience, style profile, lecture summary, social media trend, and slang analysis, propose 5 opening hook lines."
        f"\n\nAudience profile: \n{audience_profile}\n\n"
        f"Style profile: \n{style_profile}\n\n"
        f"Summary:\n{summary}\n\n"
        f"Trend analysis: \n{trend_analysis}"
        f"Slang analysis: \n{slang_analysis}",
        HookConcept,
    )

    return {"hook_ideas": hooks.ideas}


class MemeConceptDetails(BaseModel):
    meme_name_reference: str = Field(description="The name or reference of the meme")
    text_to_add: List[str] = Field(description="The text to add to the meme")


class MemeConcept(BaseModel):
    meme_concepts: List[MemeConceptDetails] = Field(
        description="List of meme name/reference and its additional text",
        min_length=3,
        max_length=5,
    )


def meme_concept_node(state: Dict[str, Any], llm: BaseChatModel) -> Dict[str, Any]:
    audience_profile = state.get("audience_profile")
    style_profile = state.get("style_profile")
    summary = state.get("summary")
    trend_analysis = state.get("trend_analysis")
    slang_analysis = state.get("slang_analysis")

    memes = structured_llm_call(
        llm,
        "You write viral hooks concepts for short-form educational content",
        f"Using the following audience, style profile, lecture summary, social media trend, and slang analysis, propose 5 meme "
        f"reference concepts. \n\nAudience profile: \n{audience_profile}\n\n"
        f"Style profile: \n{style_profile}\n\n"
        f"Summary:\n{summary}\n\n"
        f"Trend analysis: \n{trend_analysis}"
        f"Slang analysis: \n{slang_analysis}",
        MemeConcept,
    )

    return {"meme_concepts": memes}
