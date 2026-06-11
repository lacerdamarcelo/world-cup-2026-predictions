# FIFA World Cup 2026 Prediction System Methodology

This document outlines the core methodology, mathematical modeling, and engineering architecture used to predict and simulate the **FIFA World Cup 2026** (comprising 48 teams, 12 groups, and 104 matches).

---

## 1. AI Architecture & Chain-of-Thought (CoT) Engine

The simulation engine leverages Google's **Gemini 3.1 Pro** model (`gemini-3.1-pro-preview`) via the official Google GenAI SDK. Rather than relying on simple direct probability outputs, the system forces the model to act as a **Football Statistical Specialist** utilizing a 4-step Chain-of-Thought (CoT) reasoning model.

### Prompt Construction & Context Retention
To maintain logical tournament consistency (e.g., team momentum, injuries, suspensions, cards, and tactical changes), the system compiles a dynamic prompt before every simulation run:
1.  ** Standings Context:** For group stage fixtures, the current real-time standings table (Pos, MP, W, D, L, GF, GA, GD, Pts) is formatted into markdown and injected into the prompt.
2.  **Team History Context (Prompt Size Optimized):** The engine queries the history of previous matches involving the competing teams. It extracts the **last 2 played matches** for each team, including their scorelines, shootout details, and the full specialist reasoning generated during their previous simulations.
3.  **Campaign Parameters:** Under **STEP 1**, the model explicitly recites the campaign metrics (points, goals, goal differences) to align its statistical priors.

---

## 2. Expected Goals Modeling (Adapted Poisson)

Under **STEP 3**, the prompt instructs Gemini to construct an expected goals model ($\lambda$) for both teams.

### The Poisson Distribution
In football analytics, goalscoring is widely represented using a **Poisson distribution**. The probability of a team scoring exactly $k$ goals in a match is:
$$P(X = k) = \frac{\lambda^k e^{-\lambda}}{k!}$$
Where $\lambda$ represents the Expected Goals (xG) of that team for the match. 

### $\lambda$ Estimation Inputs
Gemini estimates $\lambda$ for both sides based on:
1.  **Baseline Tournament Form:** The team's offensive efficiency (GF per game) and defensive efficiency (GA per game) in the tournament so far.
2.  **External Baseline Prior:** On Matchday 1 (when GF/GA is 0), the model estimates baseline strengths using squad values, historical standings, regional strength (UEFA, CONMEBOL, CAF, etc.), and host-nation modifiers (e.g. Mexico/USA/Canada home advantage).
3.  **Tactical Urgency & Scenario Mathematics:** The standings dictate the mathematical necessity of the result (e.g., a team needing a high-margin win to qualify vs. a team that only needs a draw to top the group).

### Match Probabilities & Scoreline Mode
The model calculates the regular-time win/draw/loss percentages based on the Poisson distribution of the estimated $\lambda$ values:
*   **Draw Probability:** $P(\text{Draw}) = \sum_{k=0}^{\infty} P(X_1 = k) \cdot P(X_2 = k)$
*   **Most Likely Scoreline:** The model identifies the **mode** (most likely outcome) of the joint distribution $(X_1, X_2)$.
    *   *Note on Underdogs:* Since the mode of a Poisson distribution for any $\lambda < 1.0$ is $0$, underdogs often score 0 in the projected scoreline.
    *   *Tone Guidelines:* The prompt specifies that scoreless draws ($0-0$) are extremely common in high-pressure tournaments. It nudges the model to consider the tactical advantages of fatigued or highly defensive low-block scenarios (e.g. Morocco's defensive style), resulting in realistic draw proportions.

---

## 3. Knockout Bracket & Mappings Matrix

The tournament progression follows the official FIFA World Cup 2026 knockout bracket structure.

### Round of 32 Mappings
The first knockout stage (Matches 73 to 88) pairs the 12 group winners, 12 runners-up, and the 8 best third-placed teams. The matchups are fixed in [matches.yaml](file:///Users/marcelo/Documents/world-cup-2026-predictions/matches.yaml):
*   **Runner-up vs. Runner-up:** 8 runners-up play in pairs (A vs B, E vs I, K vs L, D vs G).
*   **Winner vs. Runner-up:** 4 group winners face runners-up (C vs F, H vs J).
*   **Winner vs. Third-Place:** 8 group winners (A, B, D, E, G, I, K, L) play the qualified third-placed teams.

### Third-Place Allocation (Annex C Matrix)
Because only 8 of the 12 third-placed teams qualify, there are $\binom{12}{8} = 495$ possible qualification combinations. FIFA uses a pre-set mapping matrix to determine which group winners play which third-placed teams.
*   The system loads this parsed matrix from [third_place_combinations.json](file:///Users/marcelo/Documents/world-cup-2026-predictions/third_place_combinations.json).
*   Once the group stage finishes, the engine ranks the 12 third-placed teams (using Points $\rightarrow$ GD $\rightarrow$ GF $\rightarrow$ Alphabetical tiebreaker).
*   The top 8 qualified groups are sorted alphabetically (e.g. `ABCDEFGH` or `EFGHIJKL`).
*   The system searches the json matrix for this combination key, retrieves the mapping dictionary, and programmatically binds the third-placed teams to their corresponding group winners (`1A`, `1B`, `1D`, `1E`, `1G`, `1I`, `1K`, `1L`) in [tournament_rules.py](file:///Users/marcelo/Documents/world-cup-2026-predictions/tournament_rules.py).

### Bracket Progression Flow
Knockout paths are chronological and mathematically isolated (e.g., Winner Group C enters Match 76 and Winner Group E enters Match 74, placing them on opposite halves of the bracket so they cannot meet before the Final or 3rd-Place match).

---

## 4. Knockout Draw Resolution & Parsing

Knockout matches cannot end in a draw.

### Scoreline Parsing Regex
Gemini is instructed to output the final score in a strict format:
`FINAL_SCORE: <Team1> <Score1> - <Score2> <Team2> (<PenWinner> wins on penalties, <P1>-<P2> pens)`

The parser in `prediction_engine.py` uses a case-insensitive regular expression:
`r"FINAL_SCORE:\s*(.+?)\s+(\d+)\s*-\s*(\d+)\s+([^\n\r(]+)(?:\s*\((.+?)\))?"`

*   **Draw Resolution:** If `Score1 == Score2`, the parser extracts the penalty details to identify the advancing team and shootout score.
*   **Fallback Resolution:** If a knockout match is predicted as a tie but the LLM omits the penalty shootout details, the code programmatically assigns a default `5-4` shootout win for Team 1 to prevent bracket progression locks.

---

## 5. Fallback Simulation Mechanism

For scenarios where the Gemini API calls fail (e.g. invalid API key, network issues, or rate limits), the engine implements a local fallback generator:
*   Goal counts for each team are chosen independently using a randomized choice weighted to match real-world football distributions:
    *   **0 Goals:** 20%
    *   **1 Goal:** 40%
    *   **2 Goals:** 25%
    *   **3 Goals:** 11%
    *   **4 Goals:** 4%
*   If a knockout stage match fallback results in a tie, a penalty shootout is simulated randomly with standard scores (e.g. `4-3`, `5-4`, `5-3`).
