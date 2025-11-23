"""Node functions for meme and trends analysis."""

import random
from typing import Any, Dict

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from models.meme_models import (
    HookConcept,
    LanguageSlang,
    MemeConcept,
    TrendsAnalysis,
)
from tools import get_mcp_tools, get_tavily_search
from utils.llm_utils import structured_llm_call


# Extended state classes for internal graph use
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

    Args:
        state: Pipeline state containing pages, summary, and other context.
        llm: Language model for analysis.

    Returns:
        Dict with trends_analysis and trends_analysis_complete status.
    """
    pages = state.get("pages", [])
    summary = state.get("summary", "")

    # Prepare context
    pages_snippets = [page for page in random.sample(pages, min(len(pages), 5))]
    content_snippets = ". ".join([p[:200] for p in pages_snippets])
    topic_context = summary[:500] if summary else content_snippets[:500]

    # Initialize tools
    tavily_tool = get_tavily_search(max_results=5, topic="general")
    mcp_tools = await get_mcp_tools()
    all_tools = [tavily_tool, *mcp_tools]

    # Build the research graph
    def call_model(agent_state: TrendsAgentState):
        """Agent that uses tools to research trends."""
        response = llm.bind_tools(all_tools).invoke(agent_state["messages"])
        return {"messages": [response]}

    def respond_structured(agent_state: TrendsAgentState):
        """Convert tool results into structured output."""
        llm_with_structure = llm.with_structured_output(TrendsAnalysis)

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

    def should_continue(agent_state: TrendsAgentState):
        """Decide if we need more tools or can respond."""
        messages = agent_state["messages"]
        last_message = messages[-1]
        if not last_message.tool_calls:
            return "respond"
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

    Args:
        state: Pipeline state containing language and summary context.
        llm: Language model for analysis.

    Returns:
        Dict with slang_analysis and slang_analysis_complete status.
    """
    language = state.get("language", "English")
    topic_context = state.get("summary", "")[:500]

    # Initialize tools
    tavily_tool = get_tavily_search(max_results=5, topic="general")
    mcp_tools = await get_mcp_tools()
    all_tools = [tavily_tool, *mcp_tools]

    # Build the research graph
    def call_model(agent_state: SlangAgentState):
        response = llm.bind_tools(all_tools).invoke(agent_state["messages"])
        return {"messages": [response]}

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


def hook_concept_node(state: Dict[str, Any], llm: BaseChatModel) -> Dict[str, Any]:
    """
    Generate hook concepts based on audience, style, and trends.

    Args:
        state: Pipeline state with audience_profile, style_profile, summary, and analyses.
        llm: Language model for generation.

    Returns:
        Dict with hook_ideas list.
    """
    audience_profile = state.get("audience_profile")
    style_profile = state.get("style_profile")
    summary = state.get("summary")
    trend_analysis = state.get("trend_analysis")
    slang_analysis = state.get("slang_analysis")

    # TODO: include current time for recent searches
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


def meme_concept_node(state: Dict[str, Any], llm: BaseChatModel) -> Dict[str, Any]:
    """
    Generate meme concepts based on audience, style, and trends.

    Args:
        state: Pipeline state with audience_profile, style_profile, summary, and analyses.
        llm: Language model for generation.

    Returns:
        Dict with meme_concepts.
    """
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

    # TODO: fix nested meme_concepts output
    return {"meme_concepts": memes}
