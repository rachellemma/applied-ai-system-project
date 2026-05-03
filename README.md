# VibeMatch 1.0 — AI-Powered Music Recommender

## Original Project

This project builds on **VibeMatch 1.0**, a scoring-based music recommendation system developed in Modules 1–3 as a classroom simulation. The original system scored a 25-song catalog against a user's stated preferences — favorite genre, current mood, target energy level, and acousticness — using a weighted formula to rank and return the top 5 matches. Its goal was to model how real recommender systems turn preference data into ranked lists, and to surface where that process breaks down.

---

## Title and Summary

**VibeMatch 1.0 with AI Reliability Layer**

VibeMatch now integrates a Claude-powered evaluation layer that diagnoses the quality of its own recommendations before returning them to the user. After the scoring pipeline runs, the AI examines the results and the user's original preferences, then generates a plain-language explanation of why each song was recommended — and, critically, flags silent failures like unrecognized genres, contradictory preferences, or suspiciously thin result sets. This matters because the original system's biggest flaw was that it returned confident-looking output even when it had quietly ignored what the user asked for. The AI layer makes those failures visible.

---

## Architecture Overview

The system has five stages:

1. **User profile** and **song catalog** (`songs.csv`) are loaded as inputs.
2. `score_song()` computes a weighted score for every song against the user's preferences across four signals: genre match (22.5%), mood match (25%), energy similarity (30%), and acousticness similarity (22.5%).
3. A **threshold filter** drops any song scoring below 0.40.
4. `recommend_songs()` sorts the remaining songs and returns the top k=5.
5. The results are passed to the **Claude API evaluator**, which diagnoses silent failures, explains the recommendations in plain language, and surfaces guardrail warnings when the output may be misleading.

A human reviewer can inspect the guardrail warnings at the final stage, satisfying the human-in-the-loop requirement for responsible AI output.

```
User profile ──┐
               ├──▶ score_song() ──▶ Threshold filter ──▶ recommend_songs() ──▶ Claude evaluator ──▶ Output
Song catalog ──┘                                                                        │
                                                                                 Human review
```

---

## Guardrails: Detecting Silent Failures

**What are guardrails?**
Guardrails are safety mechanisms that detect when a system is likely failing or producing misleading output. Unlike error handling (which stops execution), guardrails are *detectors* — they flag problems and let the system explain what went wrong, rather than blocking the output entirely.

**Why guardrails matter in VibeMatch:**
The original system's biggest flaw was that it failed *silently*. A user could ask for jazz, get zero jazz songs back, and have no way of knowing the system had failed. The output looked confident and complete, but it was wrong. Guardrails surface these hidden failures before they reach the user.

**Four guardrails implemented:**

1. **Missing genre** — If a user requests a genre that doesn't exist in the catalog (e.g., "bossa nova" when only "pop," "rock," "jazz" are available), genre match will always be 0. The guardrail flags this so Claude can tell the user: "You asked for X, but X isn't in our catalog."

2. **Contradictory numeric preferences** — If a user sets both high target energy (0.8+) *and* high target acousticness (0.8+), these signals physically contradict each other (energetic songs are typically less acoustic). The guardrail detects this contradiction, and Claude can suggest lowering one value.

3. **Thin results** — If fewer than 3 songs clear the 0.40 score threshold, the output is too sparse to be reliable. The guardrail flags this, signaling that the user's preferences are too strict or the catalog is too limited.

4. **Silent genre override** — If the user asks for a genre that *does* exist in the catalog, but none of the top-5 results actually match that genre (because mood/energy/acousticness signals outweighed it), the guardrail detects the mismatch. Claude then explains that the user's other preferences were so strong they overrode their genre choice.

Each guardrail is computed *before* the API call, so Claude receives specific, pre-vetted problems to diagnose rather than having to guess what went wrong from raw numbers.

---

## Setup Instructions

### Prerequisites
- Python 3.9 or higher
- An Anthropic API key with credits ([console.anthropic.com](https://console.anthropic.com))

### Steps

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd ai110-module3show-musicrecommendersimulation-starter
   ```

2. **Create and activate a virtual environment** (recommended)
   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac / Linux
   .venv\Scripts\activate         # Windows
   ```

3. **Install dependencies**
   ```bash
   python -m pip install -r requirements.txt
   ```

4. **Create a `.env` file** in the project root:
   ```
   ANTHROPIC_API_KEY=sk-ant-yourkeyhere
   ```
   > ⚠️ Never commit this file. It is already listed in `.gitignore`.

5. **Run the app**
   ```bash
   python -m src.main
   ```

6. **Run tests**
   ```bash
   pytest
   ```

---

## Sample Interactions

### Example 1 — Conflicting Preferences (Pop/Sad + High Energy + Acousticness)

**Input profile:**
```python
{"genre": "pop", "mood": "sad", "target_energy": 0.9, "target_acousticness": 0.65}
```

**Top recommendations:**

| # | Title | Artist | Genre | Mood | Score | Reasoning |
|---|-------|--------|-------|------|-------|-----------|
| 1 | Sunrise City | Neon Echo | pop | happy | 0.62 | genre match, high energy match, but mood mismatch |
| 2 | Velvet Underground Blues | Mara Hollis | blues | sad | 0.62 | mood match, but genre mismatch & energy too low (0.44) |
| 3 | Faded Love | Mara Hollis | r&b | sad | 0.61 | mood match & acousticness match, but genre mismatch & low energy |
| 4 | Gym Hero | Max Pulse | pop | intense | 0.61 | genre match & energy match, but mood mismatch & no acousticness |
| 5 | Rooftop Lights | Indigo Parade | indie pop | happy | 0.42 | energy match, but multiple signal mismatches |

**AI Evaluator Diagnosis:**

> The scoring system is recommending songs by partially matching your preferences, but the results reveal a fundamental problem: you've requested a combination that may not exist in the music library—high-energy (0.9) pop songs that are also sad and highly acoustic (0.65). The top recommendations either match genre and energy while missing mood and acousticness (like "Sunrise City" and "Gym Hero"), or they match mood and acousticness while having much lower energy than you requested (like "Velvet Underground Blues" at 0.44 energy). The algorithm is essentially compromising across incompatible attributes because sad, acoustic songs tend to be low-energy, while 0.9 energy typically indicates upbeat, electronic production. To get more coherent results, consider either lowering your target energy to around 0.3-0.5 if you want sad acoustic pop, or changing the mood to "happy" or "bittersweet" if you truly want high-energy music.

---

### Example 2 — Missing Genre (Bossa Nova)

**Input profile:**
```python
{"genre": "bossa nova", "mood": "happy", "target_energy": 0.5, "target_acousticness": 0.65}
```

**Top recommendations:**

| # | Title | Artist | Genre | Mood | Score | Reasoning |
|---|-------|--------|-------|------|-------|-----------|
| 1 | Rooftop Lights | Indigo Parade | indie pop | happy | 0.63 | mood match, energy & acousticness close to target |
| 2 | Sunrise City | Neon Echo | pop | happy | 0.57 | mood match, but lower acousticness match |
| 3 | Kingston Morning | Irie Collective | reggae | relaxed | 0.50 | good energy & acousticness match, mood mismatch |
| 4 | Golden Hour | Talia Monroe | r&b | chill | 0.49 | energy & acousticness close, but no mood match |
| 5 | Midnight Coding | LoRoom | lofi | chill | 0.49 | energy & acousticness close, but no mood match |

**AI Evaluator Diagnosis:**

> The recommendation system prioritized songs that matched your "happy" mood and had energy/acousticness levels close to your targets, which is why upbeat indie pop and pop tracks dominated the top results. However, there's a critical issue: bossa nova doesn't exist in the music catalog, so the system completely ignored your genre preference and instead ranked songs purely on mood and numeric audio features. This explains why you're seeing indie pop, reggae, and R&B instead of the Brazilian jazz-influenced sound you wanted. To get better results, try selecting "jazz" as your genre since it's the closest available style to bossa nova, or browse the available genres (pop, reggae, jazz, lofi, r&b, indie pop, etc.) to find the best match for the laid-back, acoustic sound you're seeking.

---

### Example 3 — Self-Defeating Preferences (High Energy + Max Acousticness)

**Input profile:**
```python
{"genre": "rock", "mood": "angry", "target_energy": 0.8, "target_acousticness": 1.0}
```

**Top recommendations:**

| # | Title | Artist | Genre | Mood | Score | Reasoning |
|---|-------|--------|-------|------|-------|-----------|
| 1 | Storm Runner | Voltline | rock | intense | 0.72 | genre match, excellent energy match, low acousticness (opposite of target) |
| 2 | Sunrise City | Neon Echo | pop | happy | 0.50 | no genre/mood match, energy & acousticness match |
| 3 | Crown & Glory | Dex Fontaine | hip hop | energetic | 0.50 | no genre/mood match, energy & acousticness match |
| 4 | Night Drive Loop | Neon Echo | synthwave | moody | 0.48 | no genre/mood match, energy & acousticness match |
| 5 | Soulfire | Neon Echo | r&b | energetic | 0.48 | no genre/mood match, energy & acousticness match |

**AI Evaluator Diagnosis:**

> The top recommendation "Storm Runner" scored well because it directly matches your rock genre preference and closely aligns with both your energy target (0.91 vs 0.8) and acousticness target (0.1 vs 0.1). However, the remaining four recommendations are problematic—they span pop, hip hop, synthwave, and r&b genres with moods like "happy" and "energetic" rather than the "angry" mood you requested, suggesting the scoring system is heavily weighted toward energy and acousticness matching while largely ignoring genre and mood preferences. This explains why songs 2-5 have identical or similar scores around 0.48-0.50 despite being completely off-genre and off-mood. To get better results, I'd recommend being more flexible with your energy or acousticness targets (perhaps widening the acceptable range) so the system can prioritize finding more rock songs with angry moods, which appear to be the features that matter most to your listening experience.

---

### Example 4 — Silent Genre Failure (Jazz with Zero Energy)

**Input profile:**
```python
{"genre": "jazz", "mood": "chill", "target_energy": 0.0, "target_acousticness": 0.65}
```

**Top recommendations:**

| # | Title | Artist | Genre | Mood | Score | Reasoning |
|---|-------|--------|-------|------|-------|-----------|
| 1 | Midnight Coding | LoRoom | lofi | chill | 0.64 | mood match, low energy match, good acousticness |
| 2 | Spacewalk Thoughts | Orbit Bloom | ambient | chill | 0.63 | mood match, excellent energy match (0.28), high acousticness |
| 3 | Golden Hour | Talia Monroe | r&b | chill | 0.62 | mood match, low energy match, good acousticness |
| 4 | Library Rain | Paper Lanterns | lofi | chill | 0.62 | mood match, low energy match, high acousticness |
| 5 | Late Nights | Indigo Parade | r&b | chill | 0.60 | mood match, low energy match, moderate acousticness |

**AI Evaluator Diagnosis:**

> The recommended songs all match your desired "chill" mood and have relatively low energy levels, which explains why they scored well in the system. However, there's a significant problem: you explicitly requested jazz, but the algorithm returned only lofi, ambient, and R&B tracks instead. This happened because the scoring pipeline heavily weighted the mood and audio features (energy and acousticness) while apparently treating genre as a lower priority or failing to filter by it entirely. To get jazz recommendations that still match your vibe, I'd suggest either making your energy target slightly higher (around 0.2-0.3 to capture more jazz tracks) or explicitly searching for "chill jazz" as a combined genre-mood query if the system supports that option.

---

## Design Decisions

**Why a reliability layer instead of RAG or an agentic workflow?**
The original system's most serious flaw — identified during testing — was that it failed silently. A jazz-requesting user received zero jazz songs with no warning. Adding a retrieval or agentic layer would have required significant new infrastructure (vector databases, multi-step planning loops) without directly solving that core problem. An AI-powered evaluation layer was the most targeted fix: it addresses the exact weakness the project already identified, integrates naturally into the existing pipeline, and requires only a single API call.

**Why keep the deterministic scoring pipeline?**
The weighted scoring function is fast, explainable, and testable. Replacing it with an LLM-based ranker would have made the system harder to debug and evaluate. Keeping the pipeline deterministic means the AI layer has reliable, structured data to reason about — which makes its diagnoses more accurate.

**Why use a `.env` file for the API key?**
Hardcoding credentials in source code is a security risk — anyone who forks or views the repository would have access to the key. The `.env` file keeps secrets out of version control while still making the key available to the application at runtime via `python-dotenv`.

**Trade-offs made:**
- The AI evaluation adds latency (one API call per run) and a small cost per request.
- The 25-song catalog is too small for a real product, but adequate for demonstrating the failure modes the AI layer is designed to catch.
- Genre and mood matching remain binary (exact string match). Fuzzy matching would reduce false negatives but adds complexity outside this project's scope.

---

## Testing Summary

**What worked:**
- The scoring pipeline behaved correctly and predictably across all four stress-test profiles documented in the model card.
- The threshold filter successfully limited results to meaningful matches in most cases.
- The guardrail detection logic (missing genre, contradictory prefs, thin results, silent genre override) correctly identified failure conditions before the API call, giving Claude specific problems to diagnose rather than asking it to guess.
- Error handling worked as designed — when the API returned a 400 (insufficient credits), the program printed a clean error message and did not crash.
- Logging confirmed the API call was reaching Anthropic's servers successfully.

**What didn't:**
- Profile 3 (rock/angry/high energy/max acousticness) produced only one result — the self-defeating preferences cancelled each other out so severely that almost nothing cleared the threshold.
- The energy floor problem: users who set `target_energy: 0.0` can never score highly on the energy signal because the lowest songs in the catalog still have energy values around 0.35.
- Initial import errors (`ModuleNotFoundError: No module named 'recommender'`) required changing bare imports to `src.recommender` and `src.evaluator` to reflect the package structure.

**What I learned:**
- Dataset quality matters as much as algorithm quality. Eight of twenty-five songs are r&b; jazz, blues, classical, and reggae each have one. That imbalance shapes every result before the weights even run.
- Small weight changes have outsized effects. Halving the genre weight from 0.45 to 0.225 was enough to completely erase a user's stated genre from their top 5.
- Prompting an LLM to diagnose structured data requires being specific about what to look for — passing pre-computed guardrail findings into the prompt produces more accurate and useful output than asking Claude to figure it out from raw numbers alone.
- Environment variables and `.env` files are the standard way to handle API credentials safely in Python projects.

---

## Reflection

Building VibeMatch taught me that the hardest problems in AI systems are not the ones that produce errors — they are the ones that produce wrong answers confidently. The original recommender never crashed. It always returned a full list. It looked like it was working. But Profile 4 showed that a system can be functionally correct (it followed all its rules) and still completely fail the user (zero jazz songs for a jazz fan). Adding the AI reliability layer was a direct response to that insight: if the system cannot always catch its own blind spots, at least it can explain them.

**For detailed reflection on biases, limitations, AI collaboration, and testing insights, see [model_card.md](model_card.md#9-personal-reflection-ai-responsibility--collaboration).**

---

## Project Structure

```
ai110-module3show-musicrecommendersimulation-starter/
├── src/
│   ├── main.py          # Entry point — runs pipeline and prints output
│   ├── recommender.py   # Scoring logic: score_song(), recommend_songs()
│   └── evaluator.py     # AI reliability layer — calls Claude API
├── data/
│   └── songs.csv        # 25-song catalog
├── tests/
│   └── test_recommender.py
├── .env                 # API key (not committed)
├── .gitignore
├── requirements.txt
└── README.md
```

---

*Built with Python · Anthropic Claude API · CSV-based song catalog*
