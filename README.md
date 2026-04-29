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

### Example 1 — Missing genre (bossa nova)

**Input profile:**
```python
{"genre": "bossa nova", "mood": "happy", "target_energy": 0.5, "target_acousticness": 0.65}
```

**Scoring output:**
```
#1  Rooftop Lights by Neon Dusk
    Genre: indie pop | Mood: happy | Score: 0.63
#2  Sunrise City by The Coastlines
    Genre: pop | Mood: happy | Score: 0.57
```

**AI evaluator output:**
```
[PASTE AI OUTPUT HERE — run with bossa nova profile and copy the diagnosis block]
```

---

### Example 2 — Self-defeating preferences (high energy + max acousticness)

**Input profile:**
```python
{"genre": "rock", "mood": "angry", "target_energy": 0.8, "target_acousticness": 1.0}
```

**Scoring output:**
```
#1  Storm Runner by Voltage Kings
    Genre: rock | Mood: intense | Score: 0.51
    (only 1 song cleared the 0.40 threshold)
```

**AI evaluator output:**
```
[PASTE AI OUTPUT HERE — run with rock/angry profile and copy the diagnosis block]
```

---

### Example 3 — Silent genre failure (jazz with zero energy)

**Input profile:**
```python
{"genre": "jazz", "mood": "chill", "target_energy": 0.0, "target_acousticness": 0.65}
```

**Scoring output:**
```
#1  Midnight Coding by LoRoom
    Genre: lofi | Mood: chill | Score: 0.64
#2  Spacewalk Thoughts by Orbit Bloom
    Genre: ambient | Mood: chill | Score: 0.63
#3  Golden Hour by Talia Monroe
    Genre: r&b | Mood: chill | Score: 0.62
#4  Library Rain by Paper Lanterns
    Genre: lofi | Mood: chill | Score: 0.62
#5  Late Nights by Indigo Parade
    Genre: r&b | Mood: chill | Score: 0.60
    (no jazz songs appear despite jazz being the stated preference)
```

**AI evaluator output:**
```
[PASTE AI OUTPUT HERE — run with jazz profile and copy the diagnosis block]
```

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

## Reflection: AI Responsibility & Collaboration

Building VibeMatch taught me that the hardest problems in AI systems are not the ones that produce errors — they are the ones that produce wrong answers confidently. The original recommender never crashed. It always returned a full list. It looked like it was working. But Profile 4 showed that a system can be functionally correct (it followed all its rules) and still completely fail the user (zero jazz songs for a jazz fan). Adding the AI reliability layer was a direct response to that insight: if the system cannot always catch its own blind spots, at least it can explain them.

### Limitations & Biases

- **Dataset imbalance**: Eight of twenty-five songs are R&B; jazz, blues, classical, and reggae each have one song. This skew means R&B users will always get better recommendations than jazz fans, regardless of how good the algorithm is. Dataset quality shapes the output before the weights ever run.
- **Binary genre/mood matching**: My system uses exact string matching (genre == "jazz"). In reality, genres are fuzzy categories. A user who likes "indie rock" probably also likes "alternative rock," but my system scores both as 0. Fuzzy matching would help, but adds complexity.
- **Energy floor problem**: The lowest-energy songs in the catalog still have energy ~0.35. A user setting `target_energy: 0.0` (very chill) can never score perfectly on the energy signal because the songs aren't actually that low-energy. Real datasets would need broader ranges.
- **Catalog size**: Twenty-five songs is too small. Real recommenders have millions of tracks, which smooths out imbalances and gives users more actual choice.

### Potential for Misuse & Prevention

- **Filter bubble risk**: If weighted heavily toward one signal (e.g., 80% genre), the system could trap users in narrow musical niches by always recommending the same few artists.
  - *Prevention*: Keep weights balanced and document them clearly (I did this). Encourage users to experiment with different preference profiles.
- **Exploitative targeting**: An AI recommender could learn that certain demographic groups will pay for "premium" music subscriptions and deliberately recommend lower-quality songs to non-premium users.
  - *Prevention*: Audit recommendation fairness across user segments. Don't condition weights on user demographics.
- **Silent manipulation**: The original system did this unintentionally—users requesting jazz got zero jazz with no warning. Guardrails catch and surface this.
  - *Prevention*: Always explain failures, never silently fall back. Use a reliability layer (what this project does).

### What Surprised Me During Testing

- **How fragile the scoring is**: Halving the genre weight from 0.45 to 0.225 completely erased the user's stated genre preference from the top 5. Small weight changes have outsized effects.
- **How much the catalog matters**: The imbalance in the dataset was more impactful than the algorithm. No weighting could make a jazz recommender work well with only one jazz song in the entire catalog.
- **How confident wrong answers look**: The original system's biggest flaw wasn't a crash or error message — it was that it returned beautiful, ranked output even when it had silently ignored the user's core request. Robustness isn't just about not crashing; it's about explaining when you're unsure.

### Collaboration with AI (Claude)

**Helpful suggestion:**
When I was building the guardrail detection logic, Claude suggested pre-computing the guardrail findings (missing genre, contradictory prefs, etc.) *before* sending the data to the LLM for evaluation. Instead of asking Claude to figure out what went wrong from raw numbers alone, I would tell it explicitly: "Here are four specific problems I detected." This made Claude's diagnoses more accurate and focused. I used this approach in my `evaluate_recommendations()` function, and it significantly improved output quality.

**Flawed suggestion:**
Claude initially recommended replacing the deterministic scoring pipeline entirely with an LLM-based ranker. Its reasoning: "LLMs can understand nuance better than weighted formulas." But this was wrong for my project because:
1. LLM-based ranking would make the system non-deterministic and harder to debug
2. The weighted pipeline is fast and testable
3. The real problem wasn't the scoring algorithm—it was lack of transparency about failures (which the guardrails solve)

I chose to keep the deterministic pipeline and add the AI reliability layer instead. This was a better fit for the actual problem I was solving.

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
