# FIFA World Cup 2026 Prediction with Gemini

A complete simulator and predictor for the FIFA World Cup 2026, powered by the Gemini API (using `gemini-3.1-pro-preview` with long-horizon reasoning) and rendered in a visually stunning, interactive dark-themed Plotly Dash dashboard.

## Important

**Every bit of this code was entirely vibe-coded. This isn't intended to be a high-end simulator that gives me the probabilities of each team reaching a certain goal. I just wanted to know what Gemini thinks about what is going to happen at the 2026 FIFA World Cup. Therefore, DON'T TAKE ANY OF THIS SERIOUSLY.**

## 🚀 Key Features

*   **Official World Cup 2026 Rules Engine:** Simulates 12 groups of 4 teams. Ranks third-placed teams and resolves the Round of 32 knockout brackets dynamically using the official 495 third-place combinations matrix (Annex C).
*   **Chronological CLI Prediction Engine:** Simulates matches in strict chronological order. The `--predict-next N` option dynamically identifies the highest predicted match ID and runs the next `N` games, preventing out-of-order execution or gaps.
*   **Realistic Goal & Draw Modeling:** Configured mock simulations and technical fallbacks to use realistic international tournament goal distributions (where a scoreless draw `0-0` has a ~9% likelihood at regular time, resolving knockout ties via shootout details).
*   **Prompt Visualization & Preview:** Inspect the exact prompt sent to the Gemini API for past simulations, or preview upcoming prompts dynamically built on-the-fly from standings and momentum context. Available via both the Dashboard (modal tabs and header button) and the CLI (`--show-next-prompt`).
*   **Auditable Prompts Database (`prompts.json`):** Automatically exports the exact prompts sent to the Gemini API for each played match into a dedicated `prompts.json` file for easy inspection, auditing, and research.
*   **Robust Scoreline Parser:** Employs a highly robust parser that handles various LLM formatting deviations (such as carriage returns, trailing punctuation, and name-based penalty shootout winner resolution).
*   **Interactive Dark-Theme Dashboard:** Displays dynamic group standing tables (direct qualifiers and best 3rd-placed highlighted), a visual left-to-right tree bracket, and a tabbed modal detail window showing the model's full CoT logic, tactical analysis, and prompt text.
*   **Live Syncing:** Auto-refreshes the dashboard dynamically every 10 seconds to display prediction results as they run in the terminal.

---

## 🛠️ Installation & Setup

1.  **Clone or Open the Project Folder:**
    Make sure you are in the project root directory:
    ```bash
    cd /Users/marcelo/Documents/world-cup-2026-predictions
    ```

2.  **API Key Configuration:**
    Get a Gemini API Key from [Google AI Studio](https://aistudio.google.com/app/api-keys).
    You can export it in your shell:
    ```bash
    export GEMINI_API_KEY="your-api-key-here"
    ```
    Or create a `.env` file in the root folder:
    ```bash
    echo "GEMINI_API_KEY=your-api-key-here" > .env
    ```

---

## 💻 Quick Start & Commands (using Makefile)

You can run predictions, view standings, launch the dashboard, and manage the environment using the provided `Makefile` tasks:

*   **Install Dependencies:**
    ```bash
    make install
    ```

*   **View Tournament Status (Standings & Bracket):**
    ```bash
    make status
    ```

*   **Predict the Next Match (use `N=X` to predict `X` matches, e.g. 5):**
    ```bash
    make predict-next N=5
    ```

*   **Predict All Remaining Matches (Full Simulation):**
    ```bash
    make predict-all
    ```

*   **Start the Interactive Dashboard:**
    ```bash
    make app
    ```
    *(Then go to `http://localhost:8050` in your web browser to view the live standings, bracket, and prediction narratives.)*

*   **Reset Tournament Simulation:**
    ```bash
    make reset
    ```

*   **Run Bracket Simulation Test:**
    ```bash
    make verify
    ```

*   **Clean Cache & Temporary Files:**
    ```bash
    make clean
    ```

---

## 🐍 Manual Python Commands (Fallback)

If you prefer to run the scripts directly using Python:

*   **Run Dashboard App:** `python app.py`
*   **View Standings CLI:** `python run.py --status`
*   **Predict next 5 matches:** `python run.py --predict-next 5`
*   **Predict all matches:** `python run.py --predict-all`
*   **Show next match prompt:** `python run.py --show-next-prompt`
*   **Reset all predictions:** `python run.py --reset`
*   **Override Model or API Key:** `python run.py --predict-next 1 --api-key "KEY" --model "gemini-3.1-pro-preview"`

### Dashboard Layout
1.  **🏆 Knockout Bracket Tab:** Shows the Round of 32 tree progression. Click on any card (played or upcoming resolved fixtures) to open a modal with the detailed Gemini prediction text, scores, and penalty details, or the exact prompt.
2.  **📊 Group Standings Tab:** Lists standings for groups A to L and ranks the 12 third-placed teams, highlighting those currently advancing.
3.  **⚽ All Matches & Predictions Tab:** Searchable list of all 104 matches, with a green "Read Prediction" button to examine prediction narratives, or a yellow "Preview Prompt" button for upcoming resolved fixtures.
4.  **🧠 Prompt Visualization & Preview Options:**
    *   **Global Preview Button:** A `📋 Preview Next Match Prompt` button in the header instantly displays the generated prompt for the very next fixture to be simulated.
    *   **Tabbed Modal Layout:** The detail modal contains two tabs: **Specialist Prediction** (shows Gemini's reasoning output) and **Gemini Prompt** (shows the exact formatted markdown prompt sent/to-be-sent to the API).
    *   **State-Aware Previewing:** Supports previewing the prompt of future/unplayed games. If the match is not yet resolved (e.g. contains placeholders like `Winner Match 73`), the prompt tab will display a helpful message explaining what teams need to advance to resolve it.
