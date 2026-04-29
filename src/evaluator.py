import os
import json
import logging
from typing import List, Tuple, Dict

import anthropic
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def evaluate_recommendations(
    user_prefs: Dict,
    recommendations: List[Tuple[Dict, float, str]],
    all_songs: List[Dict],
) -> str:
    """
    Sends the scoring results to Claude for diagnosis.
    Returns a plain-language evaluation string.

    Flags:
      - Genre not found in catalog
      - Contradictory numeric preferences (high energy + high acousticness)
      - Fewer than 3 results returned (thin output)
      - Top results don't match the user's stated genre
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set — skipping AI evaluation.")
        return "(AI evaluation unavailable: ANTHROPIC_API_KEY not set.)"

    # --- Build guardrail context for the prompt ---
    catalog_genres = list({s["genre"] for s in all_songs})
    stated_genre = user_prefs.get("genre", "")
    genre_in_catalog = stated_genre.lower() in [g.lower() for g in catalog_genres]
    result_count = len(recommendations)

    energy = user_prefs.get("target_energy", 0.5)
    acousticness = user_prefs.get("target_acousticness", 0.5)
    contradictory = energy > 0.7 and acousticness > 0.7

    top_genres = [r[0]["genre"] for r in recommendations]
    genre_represented = any(g.lower() == stated_genre.lower() for g in top_genres)

    guardrail_notes = []
    if not genre_in_catalog:
        guardrail_notes.append(
            f"WARNING: The user's stated genre '{stated_genre}' does not exist in the catalog. "
            f"Genre match was always 0. Available genres: {', '.join(catalog_genres)}."
        )
    if contradictory:
        guardrail_notes.append(
            f"WARNING: The user set target_energy={energy} and target_acousticness={acousticness}. "
            "High energy and high acousticness are physically contradictory — "
            "these two signals likely cancelled each other out."
        )
    if result_count < 3:
        guardrail_notes.append(
            f"WARNING: Only {result_count} song(s) cleared the 0.40 score threshold. "
            "The output is too thin to be a reliable recommendation."
        )
    if genre_in_catalog and not genre_represented and result_count >= 3:
        guardrail_notes.append(
            f"WARNING: The user asked for '{stated_genre}' but none of the top results match that genre. "
            "The genre preference was silently overridden by mood/energy/acousticness signals."
        )

    guardrail_block = "\n".join(guardrail_notes) if guardrail_notes else "No guardrail warnings detected."

    # --- Format recommendations for the prompt ---
    recs_formatted = ""
    for i, (song, score, explanation) in enumerate(recommendations, 1):
        recs_formatted += (
            f"{i}. \"{song['title']}\" by {song['artist']} "
            f"(genre: {song['genre']}, mood: {song['mood']}, score: {score:.2f})\n"
            f"   Scoring reason: {explanation}\n"
        )
    if not recs_formatted:
        recs_formatted = "No songs cleared the minimum score threshold."

    prompt = f"""You are a music recommender diagnostic assistant. A scoring pipeline has just run and produced the following results. Your job is to evaluate the output quality and explain it clearly to the user.

USER PREFERENCES:
- Genre: {user_prefs.get('genre')}
- Mood: {user_prefs.get('mood')}
- Target energy (0–1): {user_prefs.get('target_energy')}
- Target acousticness (0–1): {user_prefs.get('target_acousticness')}

RECOMMENDATIONS RETURNED ({result_count} songs):
{recs_formatted}

GUARDRAIL ANALYSIS:
{guardrail_block}

Please write a short evaluation (3–5 sentences) that:
1. Summarizes why the top songs were recommended in plain language
2. Clearly flags any guardrail warnings above — explain what went wrong and why
3. If results are poor or misleading, suggests one concrete adjustment the user could make to their profile

Be direct and specific. Do not repeat the song list. Do not use bullet points."""

    try:
        logger.info("Calling Claude API for recommendation evaluation...")
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        response = message.content[0].text
        logger.info("AI evaluation complete.")
        return response

    except anthropic.AuthenticationError:
        logger.error("Invalid API key.")
        return "(AI evaluation failed: invalid API key.)"
    except anthropic.RateLimitError:
        logger.error("Rate limit hit.")
        return "(AI evaluation failed: rate limit exceeded. Try again in a moment.)"
    except Exception as e:
        logger.error(f"Unexpected error during AI evaluation: {e}")
        return f"(AI evaluation failed: {e})" 