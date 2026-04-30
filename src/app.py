import streamlit as st
from pathlib import Path
from src.recommender import load_songs, recommend_songs
from src.evaluator import evaluate_recommendations

DATA_PATH = Path(__file__).parent.parent / "data" / "songs.csv"

st.set_page_config(page_title="VibeMatch 1.0", page_icon="🎵", layout="centered")

st.title("🎵 VibeMatch 1.0")
st.caption("Set your preferences and get AI-evaluated song recommendations")

# ── Sidebar: user preferences ──
with st.sidebar:
    st.header("Your Preferences")

    genre = st.selectbox("Favorite genre", [
        "jazz", "pop", "rock", "lofi", "r&b", "ambient",
        "hip hop", "synthwave", "metal", "classical",
        "country", "reggae", "blues", "indie pop", "bossa nova"
    ])

    mood = st.selectbox("Mood", [
        "chill", "happy", "sad", "intense", "romantic",
        "energetic", "focused", "nostalgic", "moody", "relaxed", "angry"
    ])

    target_energy = st.slider("Target energy", 0.0, 1.0, 0.5, 0.05)
    target_acousticness = st.slider("Target acousticness", 0.0, 1.0, 0.65, 0.05)

    run = st.button("Get recommendations", type="primary", use_container_width=True)

# ── Main panel ──
if run:
    user_prefs = {
        "genre": genre,
        "mood": mood,
        "target_energy": target_energy,
        "target_acousticness": target_acousticness,
    }

    songs = load_songs(DATA_PATH)

    with st.spinner("Scoring songs..."):
        recommendations = recommend_songs(user_prefs, songs, k=5)

    if not recommendations:
        st.warning("No songs cleared the 0.40 score threshold. Try loosening your preferences.")
    else:
        st.subheader("Top Recommendations")
        for i, (song, score, explanation) in enumerate(recommendations, 1):
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**#{i} {song['title']}** by {song['artist']}")
                    st.caption(f"{song['genre']} · {song['mood']}")
                    reasons = explanation.replace("Recommended because: ", "").split(", ")
                    for r in reasons:
                        st.caption(f"• {r}")
                with col2:
                    st.metric("Score", f"{score:.2f}")
                    st.progress(score)

    # ── AI Reliability Layer ──
    st.divider()
    st.subheader("AI Evaluator")

    with st.spinner("Asking Claude to evaluate these results..."):
        diagnosis = evaluate_recommendations(user_prefs, recommendations, songs)

    st.info(diagnosis)

else:
    st.info("Set your preferences in the sidebar and click **Get recommendations**.")