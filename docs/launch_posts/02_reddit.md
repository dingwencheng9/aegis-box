# Reddit Launch Post (r/Python & r/LocalLLaMA)

## r/Python Version

### Title

**[Project] I built Aegis Box – An intelligent audit engine for AI-assisted development (with Git sandbox & local LLM support)**

### Post Body

Hey r/Python,

I just launched **Aegis Box** and I'd love to get your feedback!

### What It Is

Aegis Box is an intelligent audit and auto-healing engine for AI coding assistants (Claude Code, Cursor, Copilot, etc.). Think of it as a paranoid senior engineer who reviews every AI-suggested code change before it touches your codebase.

### Why I Built This

**The honest story**: I'm a solo developer building a SaaS product. I rely heavily on Claude Code for development, but I kept running into the same frustrating issues:

1. **Context overload**: I'd paste a 2,000-line file into Claude, and it would hallucinate because 90% of the content was noise (comments, docstrings, implementation details). The model couldn't see the forest for the trees.

2. **Silent breakage**: Claude would suggest a "fix" that looked perfect in isolation, but broke 3 other files I forgot to mention. By the time I caught it, I'd wasted 30 minutes debugging.

3. **No safety net**: AI code changes are risky. One bad suggestion and your test suite is red, your git history is a mess, and you're not sure how to roll back cleanly.

I got tired of babysitting AI, so I spent a month building Aegis Box to do it for me.

### How It Works

**1. Architecture Reducer (AST-Based Compression)**

Instead of sending your entire codebase to the LLM, Aegis uses tree-sitter to extract only the structural skeleton:

```python
# Before (200 lines, 8,000 tokens)
def calculate_user_score(user_id: int, metrics: Dict[str, float]) -> float:
    """
    Calculate a user's composite score based on multiple metrics.

    Args:
        user_id: The user's unique identifier
        metrics: A dictionary of metric names to values

    Returns:
        The calculated score as a float between 0.0 and 100.0

    Raises:
        ValueError: If metrics dictionary is empty
    """
    # Validation logic...
    # Normalization logic...
    # Weighted calculation...
    # Edge case handling...
    return final_score

# After (10 lines, 800 tokens)
def calculate_user_score(user_id: int, metrics: Dict[str, float]) -> float:
    """[implementation details stripped]"""
    ...
```

**Result**: 90% token reduction, and the LLM can actually _reason_ about your code structure instead of drowning in details.

**2. Smart Patcher with Git Sandbox**

Every AI-suggested change runs in an isolated Git branch first:

```bash
# What happens under the hood:
1. git stash                           # Save your work
2. git checkout -b aegis-patch-xyz     # Isolated branch
3. Apply AI patch                      # Test the change
4. Run syntax check + tests            # Validate
5. If pass: apply to main              # Safe to merge
   If fail: rollback, show error       # No damage done
```

**You can Ctrl+C at any point** and Aegis rolls back cleanly. No more "oops, I broke the build."

**3. Three-Tier Model Routing (70% Cost Savings)**

- **Tier 1 (Haiku)**: Fast, cheap tasks (file scanning, quick analysis)
- **Tier 2 (Sonnet)**: Main workload (code review, refactoring)
- **Tier 3 (Opus)**: Deep reasoning (architecture decisions, complex bugs)

Aegis automatically routes each task to the right model. I've been using it for a month – my API costs dropped by 70% while quality stayed the same.

**4. Full Ollama Support (Privacy-First)**

This is the part that matters for r/LocalLLaMA folks:

```bash
# Just set these in .env - no complex YAML editing
TIER1_FAST_PROVIDER=ollama
TIER1_FAST_MODEL=llama3:8b

TIER2_REASONING_PROVIDER=ollama
TIER2_REASONING_MODEL=codellama:34b

TIER3_PATCHING_PROVIDER=ollama
TIER3_PATCHING_MODEL=qwen:72b

OLLAMA_BASE_URL=http://localhost:11434
```

**Zero cloud dependency.** Your code never leaves your machine. Perfect for:

- Proprietary codebases
- Air-gapped environments
- Privacy-conscious developers
- Experimenting with local models

### Current State

- **Languages**: Python, JavaScript, TypeScript (more coming in v0.2.0)
- **LLMs**: Anthropic, OpenAI, 智谱, any OpenAI-compatible API, **Ollama**
- **Test coverage**: 80%+
- **Production-ready**: I've been dogfooding it on a 50K LOC codebase

### Try It

```bash
pip install aegis-box
cp .env.example .env  # Add your API key or Ollama config
aegis init && aegis run --auto
```

### What I Need From You

**1. Early feedback**

- Does this solve a real problem for you?
- What would make it more useful?

**2. Windows testing**

- I developed on macOS/Linux
- Windows path handling has known issues (there's a `good-first-issue` for this!)
- If you're on Windows, please try it and report bugs

**3. Local LLM testing**

- If you run Ollama, please test Aegis with your local models
- I want to make sure the prompt engineering works well with smaller models (< 30B parameters)

**4. Language requests**

- What's your primary language?
- I'll prioritize based on community demand

### Roadmap (v0.2.0 - Q3 2026)

The next version is ambitious:

1. **Multi-Agent Debate System**: Generator vs Critic vs Judge – adversarial code review
2. **Ollama Cluster Support**: Multi-GPU parallel processing, full offline mode
3. **Native IDE Extensions**: VS Code & Cursor plugins with real-time audit feedback

### Contributing

The project is MIT licensed and actively looking for contributors. The first 10 external contributors get permanent recognition in the [Hall of Fame](https://github.com/dingwencheng9/aegis-box/blob/main/HALL_OF_FAME.md) as the "Aegis Vanguard."

There are already 2 issues labeled `good-first-issue`:

- Windows path normalization (high impact, good learning experience)
- AST parsing performance optimization (for Python nerds who like profiling)

### Why Open Source?

I believe the future of development is AI-assisted, but it needs guardrails. Aegis Box is my attempt to build those guardrails in the open.

Also, honestly, I need help. I'm one person, and there are dozens of languages, frameworks, and edge cases to support. If this resonates with you, I'd love your contributions.

### Links

- **GitHub**: https://github.com/dingwencheng9/aegis-box
- **PyPI**: https://pypi.org/project/aegis-box/
- **Documentation**: See README for full usage guide
- **Roadmap**: https://github.com/dingwencheng9/aegis-box/blob/main/ROADMAP.md

### Demo

Here's a terminal recording of Aegis in action (link to demo.gif when uploaded).

### Questions I Expect

**Q: How is this different from just using git branches manually?**  
A: It is just git branches! But automated, with pre-flight checks, and integrated into your AI workflow. The point is to make the safe path the default path.

**Q: Does this work with [my favorite AI tool]?**  
A: If it outputs code suggestions in a parseable format (plain text, diff, SEARCH/REPLACE blocks), yes. Aegis doesn't care _how_ the code was generated.

**Q: Can I use this with commercial codebases?**  
A: Yes! MIT license. And if you use Ollama, your code never leaves your machine.

**Q: Why tree-sitter instead of just parsing with Python's `ast` module?**  
A: Language-agnostic. tree-sitter supports 40+ languages with a unified API. I can add Rust support in 20 lines of code.

---

Thanks for reading! I'd love to hear your thoughts, especially if you've been using AI coding tools and hit similar frustrations.

Cheers,  
– nexo

---

## r/LocalLLaMA Version (Adjusted)

### Title

**I built an AI audit engine with full Ollama support – no cloud, no telemetry, just local LLMs reviewing code**

### Key Changes for r/LocalLLaMA

Add this section after "Full Ollama Support":

### Why This Matters for Local LLM Users

I see a lot of posts here about running models locally for privacy/cost reasons, but most AI coding tools are cloud-only. Aegis Box is built **local-first**:

**Privacy**: Your code never leaves your machine. Even the AST extraction happens locally.

**Cost**: Zero API costs. Run Aegis 24/7 on your own hardware.

**Experimentation**: Test different model combinations without burning credits:

- Fast model (llama3:8b) for scanning
- Code model (codellama:34b) for review
- Reasoning model (qwen:72b) for architecture

**Multi-GPU**: v0.2.0 will support Ollama cluster mode – distribute Tier1/Tier2/Tier3 across multiple GPUs for parallel processing.

The best part? Aegis doesn't care if you use GPT-4 or a 7B model running on your gaming PC. It's model-agnostic by design.

### What I Need From This Community

1. **Test with your local models**: Does Aegis work well with smaller models (< 30B)?
2. **Prompt engineering feedback**: The prompts are optimized for Claude/GPT-4. Do they need adjustment for local models?
3. **Performance tuning**: Any tips for squeezing more performance out of Ollama for code tasks?

I want Aegis to be the go-to tool for privacy-conscious developers using local LLMs. Your feedback is critical.

---

_End of Reddit versions_
