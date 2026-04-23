import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Returns a human-readable explanation of why a song was recommended."""
        reasons = []
        if song.genre == user.favorite_genre:
            reasons.append(f"genre match ({song.genre})")
        if song.mood == user.favorite_mood:
            reasons.append(f"mood match ({song.mood})")
        energy_diff = abs(song.energy - user.target_energy)
        reasons.append(f"energy similarity {1.0 - energy_diff:.2f} (song: {song.energy}, target: {user.target_energy})")
        return "Recommended because: " + ", ".join(reasons)


def load_songs(csv_path: str) -> List[Dict]:
    """Reads songs.csv and returns a list of song dicts with numeric fields converted."""
    print(f"Loading songs from {csv_path}...")
    songs = []
    with open(csv_path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row['id'] = int(row['id'])
            row['energy'] = float(row['energy'])
            row['tempo_bpm'] = float(row['tempo_bpm'])
            row['valence'] = float(row['valence'])
            row['danceability'] = float(row['danceability'])
            row['acousticness'] = float(row['acousticness'])
            songs.append(row)
    return songs


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Scores a single song against user preferences and returns a (score, reasons) tuple."""
    target_energy = user_prefs.get("target_energy", 0.45)
    target_acousticness = user_prefs.get("target_acousticness", 0.65)

    genre_match = 1.0 if song['genre'] == user_prefs.get('genre') else 0.0
    mood_match = 1.0 if song['mood'] == user_prefs.get('mood') else 0.0
    energy_similarity = 1.0 - abs(song['energy'] - target_energy)
    acousticness_similarity = 1.0 - abs(song['acousticness'] - target_acousticness)

    # Experimental weight shift: genre halved (0.45→0.225), energy doubled (0.15→0.30),
    # acousticness raised (0.15→0.225) to keep weights summing to 1.0
    score = (0.225 * genre_match) + (0.25 * mood_match) + (0.30 * energy_similarity) + (0.225 * acousticness_similarity)

    reasons = []
    if genre_match:
        reasons.append(f"genre match +0.225 ({song['genre']})")
    if mood_match:
        reasons.append(f"mood match +0.25 ({song['mood']})")
    reasons.append(f"energy similarity +{0.30 * energy_similarity:.2f} (song: {song['energy']}, target: {target_energy})")
    reasons.append(f"acousticness similarity +{0.225 * acousticness_similarity:.2f} (song: {song['acousticness']}, target: {target_acousticness})")

    return score, reasons


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """Scores every song using score_song, filters by threshold, and returns the top k ranked results."""
    MIN_SCORE_THRESHOLD = 0.40

    scored = [
        (song, score, "Recommended because: " + ", ".join(reasons))
        for song in songs
        for score, reasons in [score_song(user_prefs, song)]
        if score >= MIN_SCORE_THRESHOLD
    ]

    # Sort by score highest first, return top k
    return sorted(scored, key=lambda x: x[1], reverse=True)[:k]
