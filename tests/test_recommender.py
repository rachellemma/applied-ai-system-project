"""
tests/test_recommender.py

Covers:
  - OOP Recommender layer (original starter tests)
  - Core scoring and recommendation pipeline
  - AI evaluator guardrail detection (no API call required)

Run with:
    pytest -v
"""

import os
import pytest

from src.recommender import load_songs, score_song, recommend_songs, Song, UserProfile, Recommender
from src.evaluator import evaluate_recommendations


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

def make_small_recommender() -> Recommender:
    """Original starter fixture — two songs for OOP layer tests."""
    songs = [
        Song(
            id=1,
            title="Test Pop Track",
            artist="Test Artist",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.2,
        ),
        Song(
            id=2,
            title="Chill Lofi Loop",
            artist="Test Artist",
            genre="lofi",
            mood="chill",
            energy=0.4,
            tempo_bpm=80,
            valence=0.6,
            danceability=0.5,
            acousticness=0.9,
        ),
    ]
    return Recommender(songs)


MOCK_SONGS = [
    {
        "id": 1, "title": "Chill Vibes", "artist": "Test Artist A",
        "genre": "lofi", "mood": "chill",
        "energy": 0.40, "tempo_bpm": 75.0, "valence": 0.5,
        "danceability": 0.4, "acousticness": 0.70,
    },
    {
        "id": 2, "title": "Happy Days", "artist": "Test Artist B",
        "genre": "pop", "mood": "happy",
        "energy": 0.80, "tempo_bpm": 120.0, "valence": 0.8,
        "danceability": 0.7, "acousticness": 0.20,
    },
    {
        "id": 3, "title": "Storm Runner", "artist": "Test Artist C",
        "genre": "rock", "mood": "intense",
        "energy": 0.90, "tempo_bpm": 145.0, "valence": 0.4,
        "danceability": 0.5, "acousticness": 0.10,
    },
    {
        "id": 4, "title": "Midnight Study", "artist": "Test Artist D",
        "genre": "ambient", "mood": "focused",
        "energy": 0.30, "tempo_bpm": 65.0, "valence": 0.4,
        "danceability": 0.3, "acousticness": 0.85,
    },
    {
        "id": 5, "title": "Golden Afternoon", "artist": "Test Artist E",
        "genre": "r&b", "mood": "chill",
        "energy": 0.45, "tempo_bpm": 90.0, "valence": 0.6,
        "danceability": 0.6, "acousticness": 0.60,
    },
]


# ---------------------------------------------------------------------------
# 1. OOP layer — original starter tests (unchanged)
# ---------------------------------------------------------------------------

def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    # The pop, happy, high energy song should score higher
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    song = rec.songs[0]

    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


# ---------------------------------------------------------------------------
# 2. OOP layer — additional coverage
# ---------------------------------------------------------------------------

def test_recommender_explain_mentions_genre_when_matched():
    """explain_recommendation should mention genre when it matches."""
    song = Song(
        id=1, title="Chill Vibes", artist="Test Artist A",
        genre="lofi", mood="chill",
        energy=0.4, tempo_bpm=75.0, valence=0.5,
        danceability=0.4, acousticness=0.7,
    )
    user = UserProfile(
        favorite_genre="lofi", favorite_mood="chill",
        target_energy=0.4, likes_acoustic=True,
    )
    rec = Recommender([song])
    explanation = rec.explain_recommendation(user, song)
    assert "lofi" in explanation


def test_recommender_explain_mentions_mood_when_matched():
    """explain_recommendation should mention mood when it matches."""
    song = Song(
        id=2, title="Happy Days", artist="Test Artist B",
        genre="pop", mood="happy",
        energy=0.8, tempo_bpm=120.0, valence=0.8,
        danceability=0.7, acousticness=0.2,
    )
    user = UserProfile(
        favorite_genre="pop", favorite_mood="happy",
        target_energy=0.8, likes_acoustic=False,
    )
    rec = Recommender([song])
    explanation = rec.explain_recommendation(user, song)
    assert "happy" in explanation


# ---------------------------------------------------------------------------
# 3. score_song() — core scoring logic
# ---------------------------------------------------------------------------

def test_score_song_genre_and_mood_match_scores_higher():
    """A song matching genre and mood should score higher than one that doesn't."""
    user_prefs = {
        "genre": "lofi", "mood": "chill",
        "target_energy": 0.40, "target_acousticness": 0.70,
    }
    score_match, _ = score_song(user_prefs, MOCK_SONGS[0])  # lofi / chill
    score_miss, _  = score_song(user_prefs, MOCK_SONGS[1])  # pop / happy
    assert score_match > score_miss


def test_score_song_returns_tuple():
    """score_song should return a (float, list) tuple."""
    user_prefs = {
        "genre": "pop", "mood": "happy",
        "target_energy": 0.5, "target_acousticness": 0.5,
    }
    result = score_song(user_prefs, MOCK_SONGS[1])
    assert isinstance(result, tuple)
    assert isinstance(result[0], float)
    assert isinstance(result[1], list)


def test_score_song_stays_in_range():
    """All scores should be between 0.0 and 1.0."""
    user_prefs = {
        "genre": "jazz", "mood": "sad",
        "target_energy": 0.9, "target_acousticness": 0.1,
    }
    for song in MOCK_SONGS:
        score, _ = score_song(user_prefs, song)
        assert 0.0 <= score <= 1.0, f"Score out of range for {song['title']}: {score}"


def test_score_song_reasons_not_empty():
    """score_song should always return at least one reason string."""
    user_prefs = {
        "genre": "lofi", "mood": "chill",
        "target_energy": 0.4, "target_acousticness": 0.7,
    }
    _, reasons = score_song(user_prefs, MOCK_SONGS[0])
    assert len(reasons) > 0


# ---------------------------------------------------------------------------
# 4. recommend_songs() — filtering and ranking
# ---------------------------------------------------------------------------

def test_recommend_songs_respects_k_limit():
    """recommend_songs should return at most k results."""
    user_prefs = {
        "genre": "lofi", "mood": "chill",
        "target_energy": 0.4, "target_acousticness": 0.7,
    }
    results = recommend_songs(user_prefs, MOCK_SONGS, k=2)
    assert len(results) <= 2


def test_recommend_songs_sorted_descending():
    """Results should be sorted highest score first."""
    user_prefs = {
        "genre": "r&b", "mood": "chill",
        "target_energy": 0.45, "target_acousticness": 0.60,
    }
    results = recommend_songs(user_prefs, MOCK_SONGS, k=5)
    scores = [score for _, score, _ in results]
    assert scores == sorted(scores, reverse=True)


def test_recommend_songs_threshold_filter():
    """No result should have a score below the 0.40 threshold."""
    user_prefs = {
        "genre": "classical", "mood": "melancholic",
        "target_energy": 0.1, "target_acousticness": 0.9,
    }
    results = recommend_songs(user_prefs, MOCK_SONGS, k=5)
    for _, score, _ in results:
        assert score >= 0.40, f"Score {score:.2f} is below the 0.40 threshold"


def test_recommend_songs_empty_catalog():
    """recommend_songs should return an empty list when given no songs."""
    user_prefs = {
        "genre": "lofi", "mood": "chill",
        "target_energy": 0.4, "target_acousticness": 0.7,
    }
    results = recommend_songs(user_prefs, [], k=5)
    assert results == []


# ---------------------------------------------------------------------------
# 5. AI evaluator — guardrail detection (no API credits required)
# ---------------------------------------------------------------------------

def test_guardrail_safe_fallback_when_no_api_key(monkeypatch):
    """
    Evaluator must never crash when ANTHROPIC_API_KEY is missing.
    Should return the expected fallback string.
    """
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    user_prefs = {
        "genre": "jazz", "mood": "chill",
        "target_energy": 0.0, "target_acousticness": 0.65,
    }
    result = evaluate_recommendations(user_prefs, [], MOCK_SONGS)
    assert "ANTHROPIC_API_KEY" in result or "unavailable" in result.lower()


def test_guardrail_missing_genre_no_crash(monkeypatch):
    """
    Missing genre path should be reached and handled without crashing,
    even when no API key is present.
    """
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    user_prefs = {
        "genre": "bossa nova", "mood": "happy",
        "target_energy": 0.5, "target_acousticness": 0.65,
    }
    result = evaluate_recommendations(user_prefs, [], MOCK_SONGS)
    assert isinstance(result, str)
    assert len(result) > 0


def test_guardrail_thin_results_no_crash(monkeypatch):
    """
    Thin results (0 songs returned) should not crash the evaluator.
    """
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    user_prefs = {
        "genre": "rock", "mood": "angry",
        "target_energy": 0.8, "target_acousticness": 1.0,
    }
    result = evaluate_recommendations(user_prefs, [], MOCK_SONGS)
    assert isinstance(result, str)
    assert len(result) > 0


def test_guardrail_always_returns_string(monkeypatch):
    """
    evaluate_recommendations should always return a string, never raise.
    """
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    user_prefs = {
        "genre": "pop", "mood": "happy",
        "target_energy": 0.5, "target_acousticness": 0.5,
    }
    result = evaluate_recommendations(user_prefs, [], MOCK_SONGS)
    assert isinstance(result, str)
