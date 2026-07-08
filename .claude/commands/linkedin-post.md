# LinkedIn Post Generator with Canva Visual

Generate a LinkedIn post with a verified, technically accurate Canva image prompt for Shubham Arora's DevOps & AI personal brand.

## Weekly News Fetch

Run `fetch_news.py` every Monday to pull fresh topics:
```
cd ~/Downloads/content_creator && .venv/bin/python fetch_news.py
```
This fetches from: Claude Code releases, Anthropic SDK releases, Kubernetes Blog, CNCF Blog.
Output lands in `latest_news.json` — the ADK agent reads it automatically.

A durable cron is configured (Mondays 8:23 AM) but only fires while Claude Code is running. If stale, run manually before generating posts.

## Workflow

### Step 1: Topic Selection

If the user hasn't specified a topic, check `latest_news.json` first for fresh items, then fall back to:
- https://kubernetes.io/blog/
- https://www.cncf.io/blog/
- GitHub releases for Anthropic tools
- Trending DevOps/Platform Engineering/AI discussions

Pick ONE concept that's timely and relevant to DevOps, Platform Engineering, or AI tooling.

### Step 2: Verify Technical Claims

BEFORE writing the post, verify every technical claim against official sources:

- Kubernetes features: check the actual KEP, release notes, or API docs
- YAML/code snippets: verify field names, nesting, and API version against official docs
- Version numbers: confirm the feature's actual graduation status (alpha/beta/GA)
- Tool claims: verify against the tool's actual documentation

**Do NOT rely on memory for API fields, CLI flags, or config syntax. Always verify.**

Common traps to avoid:
- Wrong YAML nesting (e.g., `hostUsers` goes under `spec:`, NOT under `spec.securityContext:`)
- Invented field names (e.g., `userNamespaceMode` does not exist)
- Wrong graduation status (alpha vs beta vs GA)
- Outdated version requirements

### Step 3: Write the Post

**Style (modeled after Vishakha Sadhwani, 167K followers at NVIDIA):**

Format:
- HOOK: Bold claim, surprising fact, or relatable observation (1-2 lines)
- BODY: Structured breakdown using → arrows and numbered lists
- One idea per line, lots of whitespace for scannability
- CLOSE: Clear takeaway or engagement question

Tone:
- Educational, confident, approachable
- Like explaining to a smart colleague over coffee
- Write as if sharing from hands-on experience, not summarizing docs

Rules:
- 150-300 words
- 0-2 emojis max (minimal, intentional)
- 3-5 relevant hashtags at the end
- Do NOT mention Salesforce internal tools or proprietary systems
- Do NOT claim personal experience you can't back up — use "here's how it works" not "I did this"

### Step 4: Generate Canva Image Prompt

**What works (learned from iteration):**

The prompt should be ONE paragraph, dense with specifics. Canva's AI responds best to:

1. **State the background color with hex code first** — e.g., "#0F1923 dark navy background"
2. **Name the layout structure** — "two-column comparison layout" or "vertical stack with flow diagram"
3. **Describe each section with exact text content** — don't say "bullet points about security", say the actual bullet text
4. **Specify color coding** — red (#FF6B6B) for "before/bad", green (#69F0AE) for "after/good"
5. **Name the style** — "minimal developer aesthetic, monospace font for code, no gradients"
6. **Include code blocks verbatim** — write the exact YAML/code that should appear

**Template structure that works:**

```
Dark navy tech infographic (#0F1923 background), title "[TITLE]" in white monospace bold at top. [LAYOUT DESCRIPTION]: left side "[LEFT HEADER]" in red with [describe left content with exact text]. Right side "[RIGHT HEADER]" in green with [describe right content with exact text]. [BULLET POINTS with exact text]. Bottom section: dark code box with [EXACT CODE]. Clean minimal developer aesthetic, no gradients, [relevant icons].
```

**Dimensions:** Always 1080x1350 (portrait, optimized for LinkedIn feed)

**Do NOT:**
- Use vague descriptions like "some bullet points about the topic"
- Leave placeholder text — write the ACTUAL content for the image
- Suggest complex layouts Canva can't generate (keep to 2-3 sections max)
- Include more than ~10 lines of code in the code block (keep it focused)

### Step 5: Final Verification Checklist

Before presenting to the user, confirm:

- [ ] All YAML/code is valid and uses correct field names
- [ ] Feature graduation status matches the actual K8s version
- [ ] UID ranges, port numbers, or version numbers are accurate
- [ ] The post doesn't contradict official documentation
- [ ] The Canva prompt includes exact text (not placeholders)
- [ ] The code in the Canva prompt matches the code in the post text

## Output Format

Present the final output as:

```
## LinkedIn Post: [Topic]

### Post Text (copy-paste ready)

[full post text]

### Canva Prompt (paste into Canva's template generator)

[single paragraph prompt]

### Sources Verified
- [link 1] — [what was confirmed]
- [link 2] — [what was confirmed]
```
