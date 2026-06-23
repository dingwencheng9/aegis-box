# Hacker News Launch Post

## Title Option A (Direct & Technical)

**Show HN: Aegis Box – AI audit engine that watches AI code, with Git sandbox & AST compression**

## Title Option B (Provocative & Problem-Focused)

**Show HN: I built an AI to audit Claude/Cursor's code changes before they wreck your codebase**

## Title Option C (Curiosity-Driven)

**Show HN: Aegis Box – Self-evolving audit engine for AI-assisted development (The Ouroboros Protocol)**

---

## Post Body

Hey HN,

I'm launching **Aegis Box** – an intelligent audit and auto-healing engine for AI-assisted development tools like Cursor and Claude Code.

### The Problem

If you've used Claude/Cursor on a non-trivial codebase (10K+ LOC), you've hit this:

1. **Context explosion**: You paste 3,000 lines of boilerplate → model hallucinates because 90% is noise
2. **Silent corruption**: AI suggests a "fix" that looks good but breaks 3 other files you forgot about
3. **No rollback safety**: By the time you realize the change was wrong, you've lost 20 minutes and your git history is a mess

I got tired of babysitting AI code changes, so I built Aegis Box to do it for me.

### What It Does

Aegis Box sits between you and your AI IDE, acting as an intelligent gatekeeper:

**1. Architecture Reducer (90% token reduction via AST)**

- Uses tree-sitter to extract only the structural skeleton of your code (function signatures, class definitions, imports)
- Strips comments, docstrings, implementation details
- Result: A 3,000-line file compresses to 300 lines that actually matter for reasoning
- The LLM sees the "what" without drowning in the "how"

**2. Smart Patcher with Git Sandbox**

- Every AI-suggested change runs in an isolated Git branch first
- Validates syntax, runs your test suite, checks for breaking changes
- **Only applies the patch if it passes** – no more "oops, the build is broken"
- Full rollback on Ctrl+C or validation failure

**3. Three-Tier Model Routing (70% cost savings)**

- Tier 1 (Haiku): Fast, cheap tasks (file scanning, simple analysis)
- Tier 2 (Sonnet): Main workload (code review, refactoring suggestions)
- Tier 3 (Opus): Deep reasoning (architectural decisions, complex bugs)
- Automatically routes each task to the right model tier

**4. The Ouroboros Protocol (Self-Evolution)**

- Aegis can audit **its own source code** and propose improvements to itself
- I ran this during development – it found 3 bugs in its own Git sandbox logic
- Meta-level: An AI that improves the AI that improves your code

### Why It's Different

Most "AI code tools" are wrappers around API calls. Aegis Box is an **audit engine** – it doesn't write code for you, it makes sure the code being written is safe.

Think of it as a paranoid senior engineer who:

- Reviews every change before it lands
- Strips out noise so the AI can actually think
- Maintains a safety net (Git sandbox) so you can experiment fearlessly

### Current State

- **Language support**: Python, JavaScript, TypeScript (Rust, Go, Java coming in v0.2.0)
- **LLM support**: Anthropic, OpenAI, 智谱 (Zhipu), any OpenAI-compatible API
- **Local LLM support**: Full Ollama integration (privacy-first, zero cloud dependency)
- **Test coverage**: 80%+ with full CI/CD on GitHub Actions
- **Production-ready**: I've been using it on a 50K LOC codebase for the past month

### Roadmap (v0.2.0 - Q3 2026)

The next version is going to be wild:

1. **Multi-Agent Debate System**: Generator vs Critic vs Judge – adversarial code review to catch edge cases
2. **Pure Local Mode**: Full offline operation with Ollama cluster support (multi-GPU parallel processing)
3. **Native IDE Extensions**: VS Code & Cursor plugins with real-time audit feedback (like a linter, but for AI code)

### Why I Built This

I'm a solo founder working on a SaaS product. I use Claude Code for 80% of my development. But I kept hitting the same issues:

- Pasting huge context dumps that Claude couldn't reason about
- AI making "smart" changes that broke tests
- No systematic way to validate AI suggestions before committing

Aegis Box is the tool I wish I had 6 months ago. I'm open-sourcing it because I think this problem is universal for anyone doing AI-assisted development at scale.

### Try It

```bash
pip install aegis-box
aegis init
aegis run --auto
```

**GitHub**: https://github.com/dingwencheng9/aegis-box  
**PyPI**: https://pypi.org/project/aegis-box/  
**Docs**: See README for full usage guide

### What I'm Looking For

- **Early feedback**: Does this solve a real problem for you?
- **Windows testing**: I developed on macOS/Linux – Windows path handling needs love (there's a `good-first-issue` for this!)
- **Language support requests**: What's your primary language? I'll prioritize based on demand.
- **Contributors**: The first 10 external contributors get permanent recognition in the [Hall of Fame](https://github.com/dingwencheng9/aegis-box/blob/main/HALL_OF_FAME.md) as the "Aegis Vanguard"

### Technical Deep Dive

For the curious, here's how the AST compression works:

1. Parse source with tree-sitter (language-agnostic)
2. Walk the AST, extracting only:
   - Function/method signatures (not bodies)
   - Class definitions (not implementations)
   - Import statements
   - Type annotations
3. Reconstruct a "skeleton" file with placeholders for implementations
4. Send this to the LLM instead of the original file

Example – a 200-line Python file with 10 functions:

- **Before**: 200 lines, 8,000 tokens
- **After**: 35 lines, 800 tokens (90% reduction)
- **LLM output quality**: Often _better_ because it's not distracted by implementation details

The Git sandbox is even simpler:

1. `git stash` your working changes
2. `git checkout -b aegis-patch-<timestamp>`
3. Apply AI-suggested patch
4. Run syntax check + tests
5. If pass: `git checkout main && git apply patch`
6. If fail: `git checkout main && git stash pop` (rollback)

It's basic Git hygiene, but automated and foolproof.

### Open Source & Privacy

- **MIT License**: Use it however you want
- **Local-first**: Your code never leaves your machine unless you explicitly use cloud LLMs
- **Ollama support**: Run 100% offline with local models
- **No telemetry**: We don't collect anything (except GitHub stars, hopefully!)

### Closing Thoughts

AI-assisted development is incredible, but it's also reckless without guardrails. Aegis Box is those guardrails.

I'd love to hear what you think – especially if you've built something similar or have war stories about AI code changes gone wrong.

Thanks for reading!

---

**Links**:

- GitHub: https://github.com/dingwencheng9/aegis-box
- PyPI: https://pypi.org/project/aegis-box/
- Roadmap: https://github.com/dingwencheng9/aegis-box/blob/main/ROADMAP.md

---

_P.S. If you're wondering about the name: "Aegis" is the shield carried by Athena in Greek mythology – a symbol of protection. Aegis Box protects your codebase from AI chaos._
