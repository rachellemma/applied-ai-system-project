# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

**VibeMatch 1.0**

---

## 2. Intended Use  

**Intended use:** VibeMatch 1.0 is designed to suggest songs from a small catalog that closely match a user's stated mood, genre preference, and audio taste (energy level and acousticness). It is built for classroom exploration — a learning tool to understand how scoring-based recommendation systems work, not a production app. It assumes the user can describe their preferences in advance and that those preferences stay consistent across a listening session.

**Non-intended use:** This system should not be used as a real music discovery tool for actual listeners. It does not learn from listening history, does not update based on feedback, cannot handle preferences that change mid-session, and its 25-song catalog is far too small to serve real-world needs. It should not be used to make decisions about which artists or genres receive promotion, as its dataset imbalances (r&b over-represented at 32%) would unfairly advantage some artists over others.

---

## 3. How the Model Works  

    You (the user) tells the system your favorite genre, your current mood, how energetic you want the music to feel, and how acoustic (versus electronic) you want it. For every song in the catalog, the system checks how closely that song matches each of your four preferences, converts each match into a number between 0 and 1, multiplies each number by a weight that reflects how important that preference is, and adds them all up into a final score. Genre and mood either match or they don't — it's a yes/no check. Energy and acousticness are measured as how close the song's value is to your target value on a scale from 0 to 1. Songs that score above 0.40 are kept; everything else is dropped. The top 5 remaining songs are returned as your recommendations.

    The weights used in the current experimental version are: energy (30%), mood (25%), acousticness (22.5%), and genre (22.5%). In the original starter version, genre carried 45% of the total weight, which caused genre matches to dominate all other signals. The weight shift was made to test whether energy and acousticness could surface better-fitting songs even when the genre didn't match perfectly.

---

## 4. Data  

The dataset contains 25 songs stored in a CSV file. Each song has the following features: title, artist, genre, mood, energy (0–1 scale), tempo in BPM, valence (musical positivity), danceability, and acousticness (0–1 scale). Genres represented include r&b, lofi, pop, rock, metal, ambient, jazz, blues, hip hop, indie pop, country, classical, reggae, and synthwave. Moods include chill, happy, intense, romantic, sad, relaxed, energetic, focused, anxious, moody, nostalgic, and melancholic.

The dataset was not modified — no songs were added or removed. However, the genre distribution is heavily skewed: r&b makes up 32% of the catalog (8 songs), while 10 other genres each have only one song. Entire areas of musical taste are missing — there is no electronic, folk, latin, K-pop, gospel, or funk. Tempo and valence are loaded but not currently used by the scoring function, which means meaningful musical information is being collected but ignored.

---

## 5. Strengths  

The system works best for users who prefer r&b or lofi, since those genres have the most songs in the catalog and offer the most chances for a genuine match. It also handles chill-mood users well — five songs share that mood tag, giving the system enough options to surface a varied and reasonable top-5 list. The continuous scoring for energy and acousticness is a genuine strength: even when genre and mood don't match perfectly, songs that are close in feel can still rise to the top, which makes the output feel less mechanical than a pure genre filter would. The score explanation feature is also useful — every recommendation tells you exactly which signals contributed and by how much, making the system's reasoning transparent.

---

## 6. Limitations and Bias 

The most significant bias discovered during testing is that the dataset over-represents r&b (8 of 25 songs, or 32%), while genres like jazz, blues, classical, and reggae each have only a single song. This means a jazz fan who scores well on genre match immediately exhausts their options and receives non-jazz songs with no explanation, while an r&b fan has eight chances to match — an unfair structural advantage built into the data before the scoring even runs. A second weakness is that the energy similarity formula (`1.0 - |song_energy - target_energy|`) punishes users who prefer very low energy music: because most songs in the catalog have energy values between 0.35 and 0.97, a user who sets `target_energy: 0.0` can never achieve a high energy score, even for the mellowest songs available. Finally, genre and mood matching is purely binary — a jazz lover who might also enjoy blues receives the exact same score of 0 for a blues song as they would for a metal song, meaning the system treats all non-matching genres as equally irrelevant and creates a filter bubble where any song outside the user's exact stated genre is effectively invisible unless mood, energy, and acousticness compensate enough to clear the minimum score threshold.

---

## 7. Evaluation  

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

**1. Replace binary genre matching with genre similarity groups.** Instead of scoring jazz vs. blues as an equal miss to jazz vs. metal, genres could be organized into clusters (e.g., acoustic/mellow, high-energy/electronic, urban/rhythmic). A near-match in the same cluster would earn partial credit rather than zero, making the system far less rigid for users whose preferred genre is rare in the catalog.

**2. Use tempo and valence in the scoring function.** Both fields are already loaded from the CSV but completely ignored. A user who wants slow, melancholic music could be served much better if tempo (lower = slower) and valence (lower = sadder) were factored into the score alongside energy and acousticness.

**3. Add a diversity guardrail to the top-5 output.** Right now all five results can come from the same genre or artist if they score highest. Adding a rule that limits results to at most two songs per genre would force the list to cover more ground and expose users to music they might not have thought to ask for — which is the whole point of a discovery tool.

---

## 9. Personal Reflection: AI Responsibility & Collaboration

### Limitations & Biases

Beyond the dataset imbalance and binary matching described in section 6, several deeper biases exist:

- **Dataset imbalance**: Eight of twenty-five songs are R&B; jazz, blues, classical, and reggae each have one song. This skew means R&B users will always get better recommendations than jazz fans, regardless of algorithm quality. Dataset quality shapes output before weights even run.
- **Energy floor problem**: The lowest-energy songs in the catalog still have energy ~0.35. A user setting `target_energy: 0.0` (very chill) can never score perfectly on the energy signal because no songs are actually that low-energy.
- **Binary genre/mood matching**: My system uses exact string matching. A user who likes "indie rock" probably also likes "alternative rock," but both non-matches score identically as 0. This creates filter bubbles where only exact matches matter.
- **Catalog size**: Twenty-five songs is too small. Real datasets have millions of tracks, smoothing imbalances and offering genuine user choice.

### Potential for Misuse & Prevention

- **Filter bubble risk**: If weights favor one signal heavily (e.g., 80% genre), users get trapped in narrow niches, always seeing the same few artists.
  - *Prevention*: Keep weights balanced and document them. Encourage users to experiment with different profiles.
- **Exploitative targeting**: Systems could learn demographic segments and deliberately recommend lower-quality content to certain groups.
  - *Prevention*: Audit fairness across user segments. Never condition weights on demographics.
- **Silent manipulation**: The original system failed silently — users requesting jazz got zero jazz with no warning. 
  - *Prevention*: Always explain failures, never silently fall back. Use guardrails and evaluation layers.

### What Surprised Me During Testing

- **Weight fragility**: Halving the genre weight from 0.45 to 0.225 completely erased the user's stated genre from the top 5. Small number changes have outsized effects.
- **Dataset impact > algorithm quality**: The genre imbalance mattered more than the scoring math. No weighting could make a jazz recommender work well with only one jazz song in the catalog.
- **Confident wrong answers**: The original system's biggest flaw wasn't crashes — it was returning beautiful, ranked output even when silently ignoring the user's core request.

### Collaboration with AI (Claude)

**Helpful suggestion:**
When building the guardrail detection logic, Claude suggested pre-computing guardrail findings (missing genre, contradictory prefs, thin results) *before* the API call, then passing those specific problems to Claude for diagnosis. Instead of asking Claude to figure out what went wrong from raw numbers, I'd tell it explicitly: "Here are four detected problems." This made diagnoses accurate and focused. I implemented this in `evaluator.py`, and it significantly improved output quality over naive approaches.

**Flawed suggestion:**
Claude initially recommended replacing the deterministic scoring pipeline entirely with an LLM-based ranker, reasoning: "LLMs can understand nuance better than weighted formulas." This was wrong for my project because:
1. LLM-based ranking would make the system non-deterministic and hard to debug
2. It would be slow (25 API calls per recommendation = 5-10 seconds)
3. It would hide reasoning behind opaque LLM decisions, breaking guardrail detection
4. The real problem wasn't the scoring algorithm — it was lack of transparency about failures (which guardrails solve)

I kept the deterministic pipeline and added the AI reliability layer instead, which was a better fit for the actual problem.

### Broader Reflection

Building VibeMatch taught me that the hardest problems in AI systems are not the ones that produce errors — they are the ones that produce wrong answers confidently. The original recommender never crashed. It always returned a full list. It looked like it was working. But Profile 4 showed that a system can be functionally correct and still completely fail the user (zero jazz songs for a jazz fan). Adding the AI reliability layer was a direct response to that insight: if the system cannot always catch its own blind spots, at least it can explain them.

This changes how I think about real platforms like Spotify or Apple Music. When a recommendation feels slightly off, it is probably not a bug — it is the system doing exactly what it was designed to do, given whatever data and weights happen to be there. The math is working. The catalog or the weighting just doesn't reflect what the user actually wants.
