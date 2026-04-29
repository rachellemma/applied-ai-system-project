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

---

## Setup Instructions

### Prerequisites
- Python 3.9 or higher
- An Anthropic API key ([get one here](https://console.anthropic.com/))

### Steps

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd vibematch
   ```

2. **Create and activate a virtual environment** (recommended)
   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac / Linux
   .venv\Scripts\activate         # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set your API key**
   ```bash
   export ANTHROPIC_API_KEY="your-api-key-here"   # Mac / Linux
   set ANTHROPIC_API_KEY=your-api-key-here         # Windows
   ```

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

> ⚠️ *Replace these placeholders with real outputs once you run the system.*

### Example 1 — Genre not in catalog (bossa nova)

**Input profile:**
```python
{"genre": "bossa nova", "mood": "happy", "target_energy": 0.5, "target_acousticness": 0.65}
```

**Scoring output:**
```
#1  Rooftop Lights by [Artist]
    Genre: indie pop | Mood: happy | Score: 0.63
#2  Sunrise City by [Artist]
    Genre: pop | Mood: happy | Score: 0.57
```

**AI evaluator output:**
```
[PASTE AI RESPONSE HERE]
```

---

### Example 2 — Self-defeating preferences (high energy + max acousticness)

**Input profile:**
```python
{"genre": "rock", "mood": "angry", "target_energy": 0.8, "target_acousticness": 1.0}
```

**Scoring output:**
```
#1  Storm Runner by [Artist]
    Genre: rock | Mood: intense | Score: 0.51
    (only 1 song cleared the 0.40 threshold)
```

**AI evaluator output:**
```
[PASTE AI RESPONSE HERE]
```

---

### Example 3 — Silent genre failure (jazz with zero energy)

**Input profile:**
```python
{"genre": "jazz", "mood": "chill", "target_energy": 0.0, "target_acousticness": 0.65}
```

**Scoring output:**
```
#1  Midnight Coding by [Artist]
    Genre: lofi | Mood: chill | Score: 0.64
#2  Spacewalk Thoughts by [Artist]
    Genre: ambient | Mood: chill | Score: 0.63
    (no jazz songs appear despite jazz being the stated preference)
```

**AI evaluator output:**
```
[PASTE AI RESPONSE HERE]
```

---

## Design Decisions

**Why a reliability layer instead of RAG or an agentic workflow?**
The original system's most serious flaw — identified during testing — was that it failed silently. A jazz-requesting user received zero jazz songs with no warning. Adding a retrieval or agentic layer would have required significant new infrastructure (vector databases, multi-step planning loops) without directly solving that core problem. An AI-powered evaluation layer was the most targeted fix: it addresses the exact weakness the project already identified, integrates naturally into the existing pipeline, and requires only a single API call.

**Why keep the deterministic scoring pipeline?**
The weighted scoring function is fast, explainable, and testable. Replacing it with an LLM-based ranker would have made the system harder to debug and evaluate. Keeping the pipeline deterministic means the AI layer has reliable, structured data to reason about — which makes its diagnoses more accurate.

**Trade-offs made:**
- The AI evaluation adds latency (one API call per run) and a small cost per request.
- The 25-song catalog is too small for a real product, but adequate for demonstrating the failure modes the AI layer is designed to catch.
- Genre and mood matching remain binary (exact string match). A fuzzy matching approach would reduce false negatives but add complexity outside this project's scope.

---

## Testing Summary

**What worked:**
- The scoring pipeline behaved correctly and predictably across all four stress-test profiles.
- The threshold filter successfully limited results to meaningful matches in most cases.
- The AI evaluator correctly identified the bossa nova missing-genre case and the jazz silent-failure case in testing.

**What didn't:**
- Profile 3 (rock/angry/high energy/max acousticness) produced only one result — the self-defeating preferences cancelled each other out so severely that almost nothing cleared the threshold. The system technically works but the output is nearly useless.
- The energy floor problem: users who set `target_energy: 0.0` can never score highly on the energy signal because the lowest songs in the catalog still have energy values around 0.35.
- The AI evaluator's output quality depends on how clearly the prompt is written. Early prompt versions produced generic explanations rather than specific guardrail warnings.

**What I learned:**
- Dataset quality matters as much as algorithm quality. Eight of twenty-five songs are r&b; jazz, blues, classical, and reggae each have one. That imbalance shapes every result before the weights even run.
- Small weight changes have outsized effects. Halving the genre weight from 0.45 to 0.225 was enough to completely erase a user's stated genre from their top 5.
- Prompting an LLM to diagnose structured data requires being specific about what to look for — a vague "evaluate these recommendations" prompt produces vague output.

---

## Reflection

Building VibeMatch taught me that the hardest problems in AI systems are not the ones that produce errors — they are the ones that produce wrong answers confidently. The original recommender never crashed. It always returned a full list. It looked like it was working. But Profile 4 showed that a system can be functionally correct (it followed all its rules) and still completely fail the user (zero jazz songs for a jazz fan). Adding the AI reliability layer was a direct response to that insight: if the system cannot always catch its own blind spots, at least it can explain them.

This also changed how I think about real platforms like Spotify or Apple Music. When a recommendation feels slightly off, it is probably not a bug — it is the system doing exactly what it was designed to do, given whatever data and weights happen to be there. The math is working. The catalog or the weighting just doesn't reflect what the user actually wants.

---

*Built with Python · Anthropic Claude API · CSV-based song catalog*
