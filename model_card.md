# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

**VibeMatch 1.0**

---

## 2. Intended Use  

Describe what your recommender is designed to do and who it is for. 

Prompts:  

- What kind of recommendations does it generate  
- What assumptions does it make about the user  
- Is this for real users or classroom exploration  

**Intended use:** VibeMatch 1.0 is designed to suggest songs from a small catalog that closely match a user's stated mood, genre preference, and audio taste (energy level and acousticness). It is built for classroom exploration — a learning tool to understand how scoring-based recommendation systems work, not a production app. It assumes the user can describe their preferences in advance and that those preferences stay consistent across a listening session.

**Non-intended use:** This system should not be used as a real music discovery tool for actual listeners. It does not learn from listening history, does not update based on feedback, cannot handle preferences that change mid-session, and its 25-song catalog is far too small to serve real-world needs. It should not be used to make decisions about which artists or genres receive promotion, as its dataset imbalances (r&b over-represented at 32%) would unfairly advantage some artists over others.

---

## 3. How the Model Works  

Explain your scoring approach in simple language.  

Prompts:  

- What features of each song are used (genre, energy, mood, etc.)  
- What user preferences are considered  
- How does the model turn those into a score  
- What changes did you make from the starter logic  

Avoid code here. Pretend you are explaining the idea to a friend who does not program.

You tell the system your favorite genre, your current mood, how energetic you want the music to feel, and how acoustic (versus electronic) you want it. For every song in the catalog, the system checks how closely that song matches each of your four preferences, converts each match into a number between 0 and 1, multiplies each number by a weight that reflects how important that preference is, and adds them all up into a final score. Genre and mood either match or they don't — it's a yes/no check. Energy and acousticness are measured as how close the song's value is to your target value on a scale from 0 to 1. Songs that score above 0.40 are kept; everything else is dropped. The top 5 remaining songs are returned as your recommendations.

The weights used in the current experimental version are: energy (30%), mood (25%), acousticness (22.5%), and genre (22.5%). In the original starter version, genre carried 45% of the total weight, which caused genre matches to dominate all other signals. The weight shift was made to test whether energy and acousticness could surface better-fitting songs even when the genre didn't match perfectly.

---

## 4. Data  

Describe the dataset the model uses.  

Prompts:  

- How many songs are in the catalog  
- What genres or moods are represented  
- Did you add or remove data  
- Are there parts of musical taste missing in the dataset  

The dataset contains 25 songs stored in a CSV file. Each song has the following features: title, artist, genre, mood, energy (0–1 scale), tempo in BPM, valence (musical positivity), danceability, and acousticness (0–1 scale). Genres represented include r&b, lofi, pop, rock, metal, ambient, jazz, blues, hip hop, indie pop, country, classical, reggae, and synthwave. Moods include chill, happy, intense, romantic, sad, relaxed, energetic, focused, anxious, moody, nostalgic, and melancholic.

The dataset was not modified — no songs were added or removed. However, the genre distribution is heavily skewed: r&b makes up 32% of the catalog (8 songs), while 10 other genres each have only one song. Entire areas of musical taste are missing — there is no electronic, folk, latin, K-pop, gospel, or funk. Tempo and valence are loaded but not currently used by the scoring function, which means meaningful musical information is being collected but ignored.

---

## 5. Strengths  

Where does your system seem to work well  

Prompts:  

- User types for which it gives reasonable results  
- Any patterns you think your scoring captures correctly  
- Cases where the recommendations matched your intuition  

The system works best for users who prefer r&b or lofi, since those genres have the most songs in the catalog and offer the most chances for a genuine match. It also handles chill-mood users well — five songs share that mood tag, giving the system enough options to surface a varied and reasonable top-5 list. The continuous scoring for energy and acousticness is a genuine strength: even when genre and mood don't match perfectly, songs that are close in feel can still rise to the top, which makes the output feel less mechanical than a pure genre filter would. The score explanation feature is also useful — every recommendation tells you exactly which signals contributed and by how much, making the system's reasoning transparent.

---

## 6. Limitations and Bias 

Where the system struggles or behaves unfairly. 

Prompts:  

- Features it does not consider  
- Genres or moods that are underrepresented  
- Cases where the system overfits to one preference  
- Ways the scoring might unintentionally favor some users  

The most significant bias discovered during testing is that the dataset over-represents r&b (8 of 25 songs, or 32%), while genres like jazz, blues, classical, and reggae each have only a single song. This means a jazz fan who scores well on genre match immediately exhausts their options and receives non-jazz songs with no explanation, while an r&b fan has eight chances to match — an unfair structural advantage built into the data before the scoring even runs. A second weakness is that the energy similarity formula (`1.0 - |song_energy - target_energy|`) punishes users who prefer very low energy music: because most songs in the catalog have energy values between 0.35 and 0.97, a user who sets `target_energy: 0.0` can never achieve a high energy score, even for the mellowest songs available. Finally, genre and mood matching is purely binary — a jazz lover who might also enjoy blues receives the exact same score of 0 for a blues song as they would for a metal song, meaning the system treats all non-matching genres as equally irrelevant and creates a filter bubble where any song outside the user's exact stated genre is effectively invisible unless mood, energy, and acousticness compensate enough to clear the minimum score threshold.

---

## 7. Evaluation  

How you checked whether the recommender behaved as expected. 

Prompts:  

- Which user profiles you tested  
- What you looked for in the recommendations  
- What surprised you  
- Any simple tests or comparisons you ran  

No need for numeric metrics unless you created some.

Four user profiles were tested to stress-test the scoring logic under different conditions.

---

**Profile 1 — Conflicting preferences: pop / sad mood / high energy (0.9) / high acousticness (0.65)**

Top results: Sunrise City (pop/happy, 0.62), Velvet Underground Blues (blues/sad, 0.62)

The system split its attention between the genre signal and the mood signal because no song in the dataset is both pop and sad. Sunrise City matched on genre (pop) but had the wrong mood (happy); Velvet Underground Blues matched on mood (sad) but had the wrong genre (blues). Neither result fully satisfied the user. Surprisingly, high energy and high acousticness are contradictory physical properties — acoustic songs tend to be quieter and low-energy — so those two signals worked against each other and dragged all scores down toward the middle.

---

**Profile 2 — Missing genre: bossa nova / happy mood / moderate energy (0.5) / acoustic (0.65)**

Top results: Rooftop Lights (indie pop/happy, 0.63), Sunrise City (pop/happy, 0.57)

Because bossa nova does not exist in the dataset, genre match was always zero for every song. The system fell back entirely on mood, energy, and acousticness — and happy mood became the dominant signal, pulling Rooftop Lights and Sunrise City to the top. This showed that the system degrades gracefully when a genre is missing, but it also revealed that the user receives no feedback that their stated genre was ignored entirely.

> **Comparison — Profile 1 vs. Profile 2:** Both profiles failed to get a clean genre match, but for different reasons. Profile 1 had a genre that exists yet conflicted with the mood; Profile 2 had a genre that simply wasn't in the catalog. Profile 1's results were scattered across genre-match and mood-match winners with similar scores, while Profile 2's results were tightly clustered around mood (happy) because that was the only strong signal left. When genre is absent, mood becomes the whole story.

---

**Profile 3 — Self-defeating preferences: rock / angry mood / high energy (0.8) / maximum acousticness (1.0)**

Top results: Storm Runner (rock/intense, 0.51) — only 1 song cleared the threshold

High energy and maximum acousticness directly contradict each other: electrically amplified, hard rock songs score near zero on acousticness, and genuinely acoustic songs are almost never high energy. Storm Runner matched on genre and was close to angry (intense), but its acousticness of 0.10 versus a target of 1.0 created an acousticness penalty so severe that nearly every song in the dataset was filtered out. Only one song survived the 0.40 minimum threshold, leaving the user with a single recommendation.

---

**Profile 4 — Low-energy user: jazz / chill mood / zero energy (0.0) / acoustic (0.65)**

Top results: Midnight Coding (lofi/chill, 0.64), Spacewalk Thoughts (ambient/chill, 0.63), Golden Hour (r&b/chill, 0.62)

Jazz was listed as the preferred genre but the only jazz song in the dataset (Coffee Shop Stories) has a relaxed mood rather than chill — that mood mismatch, combined with the experimental weight shift that reduced genre importance, meant it did not crack the top 5. Instead the list filled entirely with chill-mood songs from lofi, ambient, and r&b genres. The jazz preference was functionally ignored, which is the dataset scarcity problem described in the Limitations section playing out directly.

> **Comparison — Profile 3 vs. Profile 4:** Both profiles asked for something the dataset could not deliver, but in opposite ways. Profile 3 had contradictory numeric preferences (high energy + max acoustic) that cancelled each other out mathematically, leaving almost no valid results. Profile 4 had a valid but underrepresented genre preference (jazz, 1 song) that the system simply sidestepped by promoting mood matches instead. Profile 3 failed loudly with almost no output; Profile 4 failed silently with a full list that quietly ignored the stated genre.

---

## 8. Future Work  

Ideas for how you would improve the model next.  

Prompts:  

- Additional features or preferences  
- Better ways to explain recommendations  
- Improving diversity among the top results  
- Handling more complex user tastes  

**1. Replace binary genre matching with genre similarity groups.** Instead of scoring jazz vs. blues as an equal miss to jazz vs. metal, genres could be organized into clusters (e.g., acoustic/mellow, high-energy/electronic, urban/rhythmic). A near-match in the same cluster would earn partial credit rather than zero, making the system far less rigid for users whose preferred genre is rare in the catalog.

**2. Use tempo and valence in the scoring function.** Both fields are already loaded from the CSV but completely ignored. A user who wants slow, melancholic music could be served much better if tempo (lower = slower) and valence (lower = sadder) were factored into the score alongside energy and acousticness.

**3. Add a diversity guardrail to the top-5 output.** Right now all five results can come from the same genre or artist if they score highest. Adding a rule that limits results to at most two songs per genre would force the list to cover more ground and expose users to music they might not have thought to ask for — which is the whole point of a discovery tool.

---

## 9. Personal Reflection  

A few sentences about your experience.  

Prompts:  

- What you learned about recommender systems  
- Something unexpected or interesting you discovered  
- How this changed the way you think about music recommendation apps  

Building this recommender made it clear that the dataset is just as important as the algorithm — the scoring math can be perfectly designed, but if the catalog doesn't have the songs a user needs, the system will silently return wrong answers with high confidence. The most surprising moment was seeing that halving the genre weight caused a jazz-requesting user to receive zero jazz songs in their top five: a small number change produced a complete genre erasure. That showed how sensitive these systems are to weight choices, and why real platforms likely spend enormous effort tuning and testing those numbers. I'll think differently about Spotify or Apple Music recommendations now — when I get a recommendation that feels slightly off, I'll wonder whether it's a data gap, a weight problem, or a silent fallback that I was never told about.
