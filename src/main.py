"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from pathlib import Path
from recommender import load_songs, recommend_songs

DATA_PATH = Path(__file__).parent.parent / "data" / "songs.csv"


def main() -> None:
    songs = load_songs(DATA_PATH)

    # Starter example profile
    # conflicting energy and mood 
    # user_prefs = {"genre": "pop", "mood": "sad", "tempo_bpm": 92, "target_energy": 0.9, "target_acousticness": 0.65}
    # genre that doesnt exist in the dataset
    # user_prefs = {"genre": "bossa nova", "mood": "happy", "tempo_bpm":110, "target_energy": 0.5, "target_acousticness": 0.65}
    # self defeating profile (the preferences cancel themselves out)
    # user_prefs = {"genre": "rock", "mood": "angry", "tempo_bpm": 140, "target_energy": 0.8, "target_acousticness": 1.00}
    # # energy similairty bottoms out at zero 
    user_prefs = {"genre": "jazz", "mood": "chill", "tempo_bpm": 70, "target_energy": 0.0, "target_acousticness": 0.65}

    recommendations = recommend_songs(user_prefs, songs, k=5)

    print("\n" + "=" * 40)
    print("  Top Recommendations For You")
    print("=" * 40)
    for i, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"\n#{i}  {song['title']} by {song['artist']}")
        print(f"    Genre: {song['genre']} | Mood: {song['mood']} | Score: {score:.2f}")
        print(f"    Why:")
        reasons = explanation.replace("Recommended because: ", "").split(", ")
        for reason in reasons:
            print(f"      - {reason}")
    print("\n" + "=" * 40)


if __name__ == "__main__":
    main()
