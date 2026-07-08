import json
import os
from pathlib import Path

import litellm
from dotenv import load_dotenv
from google.adk.agents import Agent, SequentialAgent
from google.adk.tools import agent_tool

load_dotenv()

NEWS_FILE = Path(__file__).parent / "latest_news.json"

# Model config: Salesforce gateway (Anthropic-compatible) or Gemini for public users
USE_SF_GATEWAY = os.getenv("USE_SF_GATEWAY", "false").lower() == "true"

if USE_SF_GATEWAY:
    litellm.ssl_verify = False
    os.environ["SSL_VERIFY"] = "false"
    from google.adk.models.lite_llm import LiteLlm
    MODEL = LiteLlm(model=f"anthropic/{os.getenv('SF_MODEL', 'claude-sonnet-4-20250514')}")
else:
    MODEL = os.getenv("MODEL", "gemini-2.0-flash")


# ─── Load latest news if available ───────────────────────────────────────────

def _load_news_context():
    if not NEWS_FILE.exists():
        return ""
    try:
        data = json.loads(NEWS_FILE.read_text())
        items = data.get("items", [])[:20]
        if not items:
            return ""
        lines = [f"- [{i['category'].upper()}] {i['title']} ({i['source']}): {i['link']}" for i in items]
        return "\n\nRECENT NEWS (from latest_news.json):\n" + "\n".join(lines) + "\n"
    except (json.JSONDecodeError, KeyError):
        return ""

_news_context = _load_news_context()


# ─── Agent 1: Researcher ─────────────────────────────────────────────────────

researcher = Agent(
    name="Researcher",
    model=MODEL,
    description="Researches a DevOps or AI topic and extracts verified facts.",
    instruction=f"""
You are a technical researcher covering TWO domains equally:
1. DevOps & Cloud-Native — Kubernetes, CNCF tools, platform engineering, CI/CD
2. AI & Developer Tools — Anthropic Claude, Claude Code, AI SDKs, LLM tooling, AI agents

Both domains are fully in scope. You research whatever the user asks about.

Given the user's topic, produce a research brief:

1. **Core Concept** — What is it? (2-3 sentences)
2. **Key Technical Details** — API changes, new features, CLI commands, SDK methods, config syntax
3. **Version/Status** — Version number, release date, availability
4. **Why It Matters** — Practical impact for engineers and developers
5. **Before/After** — How things worked before vs after (if applicable)

TOPIC SELECTION:
- If the user says "use latest news", "what's new", or "what's latest in X", pick from the news list below.
- If the user gives a specific topic, research that directly.
- For Anthropic/Claude topics: cover new model releases, SDK updates, Claude Code features, API changes, pricing, capabilities.

AUDIENCE FILTER — Pick topics that LinkedIn engineers actually care about:
- YES: New model launches, major feature releases, paradigm shifts, GA announcements, breaking changes, new tools/frameworks
- NO: Patch version bumps (v2.1.203 → v2.1.204), minor bug fixes, internal refactors, CI changes
- If the news list only has minor releases, use the user's topic as a starting point and research the BIGGEST recent development in that space (new capabilities, industry shifts, benchmarks, real-world impact stories)
- Think: "Would a senior engineer stop scrolling to read this?" If not, pick something bigger.

Be EXACT with version numbers, feature names, and technical details. If unsure, say "needs verification".
{_news_context}""",
    output_key="research_brief",
)


# ─── Agent 2: LinkedIn Writer ────────────────────────────────────────────────

linkedin_writer = Agent(
    name="LinkedInWriter",
    model=MODEL,
    description="Writes a viral LinkedIn post from the research brief.",
    instruction="""
You write LinkedIn posts for a software engineer building a personal brand in DevOps and AI.

Read the research from state key `research_brief`.

FORMAT:
- HOOK: Bold claim or surprising fact (1-2 lines)
- BODY: Use → arrows for sub-points, numbered lists for steps
- One idea per line, lots of whitespace
- CLOSE: Engagement question

RULES:
- 150-300 words strictly
- 0-2 emojis max
- 3-5 hashtags at end
- Never mention employer name
- Only use facts from the research brief
""",
    output_key="linkedin_post",
)


# ─── Agent 3: Canva Prompt Generator ─────────────────────────────────────────

canva_prompter = Agent(
    name="CanvaPrompter",
    model=MODEL,
    description="Creates a Canva template prompt for the LinkedIn visual.",
    instruction="""
Read state keys `linkedin_post` and `research_brief`.

Generate ONE dense paragraph for Canva's template generator.

VISUAL VARIETY — Pick a DIFFERENT theme each time based on the post topic. Rotate through these styles:

STYLE A (Dark tech): #0F1923 navy background, white/green text, monospace font, terminal aesthetic
STYLE B (Gradient modern): Deep purple-to-blue gradient (#1a0533 to #0a1628), white text, rounded cards, subtle glow effects
STYLE C (Clean white): #FFFFFF background, dark text (#1a1a2e), accent color matching topic (blue for cloud, orange for AI, green for DevOps), card-based layout with light shadows
STYLE D (Warm dark): #1C1C1E charcoal background, warm amber (#FFB84D) accents, sans-serif bold headers, minimal icons
STYLE E (Blueprint): #0A192F background, cyan (#64FFDA) wireframe/line-art style, technical blueprint aesthetic, grid lines

Pick the style that BEST fits the topic mood:
- Controversial/bold takes → Style D (warm, attention-grabbing)
- Technical deep-dives → Style A (terminal) or Style E (blueprint)
- Modern trends/future → Style B (gradient)
- Comparisons/tutorials → Style C (clean, readable)

LAYOUT VARIETY — Don't always do two-column. Rotate:
- Two-column before/after
- Vertical flow with numbered steps
- Central diagram with radiating points
- Single bold statement with supporting bullets below
- Timeline/progression (left to right or top to bottom)

RULES:
1. State the chosen background color/style first
2. Name the layout structure
3. Write EXACT text content (not placeholders)
4. Use contrasting colors for emphasis (not always red/green — try amber/cyan, coral/mint, etc.)
5. Include any code verbatim (max 8 lines)
6. End with style note (font choice, aesthetic descriptor)

Target: 1080x1350 portrait.

Output format:
Line 1: "Dimensions: 1080 x 1350"
Blank line, then the single paragraph prompt.
""",
    output_key="canva_prompt",
)


# ─── Agent 4: Medium Writer ──────────────────────────────────────────────────

medium_writer = Agent(
    name="MediumWriter",
    model=MODEL,
    description="Writes a long-form Medium article from the research.",
    instruction="""
You write technical blog posts for Medium / dev.to.

Read state key `research_brief`.

STRUCTURE:
- H1 title (SEO-friendly)
- Short intro (2-3 sentences)
- 4-6 H2 sections with explanations, code snippets, real-world context
- H2 Conclusion with takeaways

RULES:
- 1200-1800 words
- Code blocks with language tags (```yaml, ```bash)
- Developer-to-developer tone
- Only use facts from the research brief
""",
    output_key="medium_article",
)


# ─── Agent 5: Twitter/X Thread Generator ────────────────────────────────────

twitter_writer = Agent(
    name="TwitterWriter",
    model=MODEL,
    description="Converts the research into a viral Twitter/X thread.",
    instruction="""
You write Twitter/X threads for a software engineer with expertise in DevOps and AI.

Read state key `research_brief`.

FORMAT:
- Tweet 1 (HOOK): Bold one-liner that makes people stop scrolling. End with "🧵👇" or "A thread:"
- Tweets 2-7: One insight per tweet. Use short punchy sentences. Each tweet must stand alone but flow as a narrative.
- Final tweet: Recap + CTA ("Follow for more DevOps/AI threads" or "Repost if this helped")

RULES:
- Each tweet: max 280 characters
- 6-8 tweets total
- No hashtags inside tweets (only in final tweet, max 2)
- Use line breaks within tweets for readability
- Number each tweet: 1/, 2/, 3/ etc.
- Tone: sharp, opinionated, slightly provocative
- Use analogies and real-world comparisons
- Only use facts from the research brief
""",
    output_key="twitter_thread",
)


# ─── Agent 6: Fact Checker ────────────────────────────────────────────────────

fact_checker = Agent(
    name="FactChecker",
    model=MODEL,
    description="Validates all generated content for technical accuracy.",
    instruction="""
Read state keys: `research_brief`, `linkedin_post`, `twitter_thread`, `medium_article`, `canva_prompt`.

Check for:
1. YAML field names — are they real? Is nesting correct?
2. Version numbers — correct graduation status?
3. Code syntax — valid YAML/bash?
4. Consistency — does canva prompt code match post code?
5. Twitter thread — each tweet under 280 chars?

Output:
If all good: "VERDICT: PASS - All technical claims verified."
If issues: "VERDICT: NEEDS FIX" followed by numbered list of issues with corrections.
""",
    output_key="fact_check_result",
)


# ─── Agent 6: Formatter (presents final output to user) ──────────────────────

formatter = Agent(
    name="Formatter",
    model=MODEL,
    description="Formats and presents all generated content to the user.",
    instruction="""
Read ALL state keys and present the final output to the user.

Format your response EXACTLY like this (copy the content from state, do not summarize):

---
## LinkedIn Post

[paste full content from state key `linkedin_post`]

---
## Canva Image Prompt

[paste full content from state key `canva_prompt`]

---
## Twitter/X Thread

[paste full content from state key `twitter_thread`]

---
## Medium Article

[paste full content from state key `medium_article`]

---
## Fact Check Result

[paste full content from state key `fact_check_result`]
---

IMPORTANT:
- Copy the FULL content from each state key. Do not summarize or truncate.
- Do not add your own commentary.
- Present everything as-is from state.
""",
)


# ─── Root Agent: Sequential Pipeline ─────────────────────────────────────────

root_agent = SequentialAgent(
    name="ContentCreator",
    description="DevOps & AI content creator — generates LinkedIn posts and Medium articles from a single topic or latest news.",
    sub_agents=[researcher, linkedin_writer, canva_prompter, twitter_writer, medium_writer, fact_checker, formatter],
)
