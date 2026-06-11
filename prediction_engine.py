import os
import random
import re
import yaml
from google import genai
from google.genai import types
import dotenv

# Load .env file if it exists
dotenv.load_dotenv()

def get_genai_client(api_key=None):
    """
    Initializes and returns the Gemini API client.
    """
    key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise ValueError(
            "Gemini API Key not found. Please provide it via: \n"
            "1. CLI flag: --api-key YOUR_KEY\n"
            "2. In a .env file: GEMINI_API_KEY=YOUR_KEY\n"
            "3. Environment variable: export GEMINI_API_KEY=YOUR_KEY\n"
            "You can get an API key at https://aistudio.google.com/app/api-keys"
        )
    return genai.Client(api_key=key)

def format_standings_table(standings):
    """
    Formats the standings of a group as a markdown table.
    """
    if not standings:
        return "No standings data available."
        
    table = "| Pos | Team | MP | W | D | L | GF | GA | GD | Pts |\n"
    table += "| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n"
    for idx, t in enumerate(standings):
        table += f"| {idx+1} | {t['team']} | {t['mp']} | {t['w']} | {t['d']} | {t['l']} | {t['gf']} | {t['ga']} | {t['gd']} | {t['pts']} |\n"
    return table

def get_team_history_context(team_name, predictions_dict):
    """
    Retrieves and formats the historical predictions involving a team.
    """
    history_matches = []
    # Find all played matches for this team
    for m_id, pred in predictions_dict.items():
        if not pred.get("is_played", False):
            continue
        t1, t2 = pred["team1"], pred["team2"]
        if t1 == team_name or t2 == team_name:
            history_matches.append(pred)
            
    if not history_matches:
        return f"No previous matches played by {team_name} in this tournament."
        
    # Limit to the last 2 played matches to control prompt size
    history_matches = history_matches[-2:]
        
    context = f"Matches played by {team_name} so far:\n\n"
    for m in history_matches:
        context += f"Match: {m['team1']} vs {m['team2']}\n"
        context += f"Result: {m['team1']} {m['score1']} - {m['score2']} {m['team2']}"
        if m.get("pen_winner"):
            context += f" ({m['pen_winner']} won on penalties)"
        context += "\n"
        context += f"Specialist Reasoning & Analysis:\n{m.get('prediction_text', '')}\n"
        context += "-" * 40 + "\n\n"
    return context

def build_prompt(team1, team2, stage, group_name, standings, predictions_dict):
    """
    Builds the prompt for Gemini following the exact user guidelines.
    """
    # 1. Format previous predictions context
    t1_history = get_team_history_context(team1, predictions_dict)
    t2_history = get_team_history_context(team2, predictions_dict)
    
    previous_context = f"### Previous Context for {team1}:\n{t1_history}\n\n"
    previous_context += f"### Previous Context for {team2}:\n{t2_history}"
    
    # 2. Format standings context
    if stage == "group" and standings:
        standings_context = f"Group standings for Group {group_name}:\n{format_standings_table(standings)}"
    else:
        standings_context = "Not applicable (Knockout Stage - Single Elimination. Win or go home.)"
        
    # 3. Construct prompt using the exact template
    prompt = f"""You are a Football Statistical Specialist, specializing in the FIFA World Cup 2026. Your mission is to predict the scoreline of a tournament match using a rigorous Chain-of-Thought (step-by-step reasoning) approach, tailored to the dynamics of a high-pressure, short-turnaround tournament.

[PREVIOUS PREDICTIONS CONTEXT]
The following text contains the history of previously generated match predictions and tournament outcomes simulated so far. Use this context to maintain logical consistency regarding team momentum, injuries mentioned earlier, and group dynamics:
{previous_context}

[CURRENT GROUP STANDINGS]
{standings_context}

Whenever you receive a World Cup matchup, you must strictly follow these 4 steps based on the manual data provided by the user:

STEP 1: USER-PROVIDED CAMPAIGN & CURRENT CONTEXT
- Review the match context, current standings, and team data provided manually by the user in the prompt.
- Explicitly state the parameters provided: Matches played so far in the tournament, Points accumulated, Goals For (GF), Goals Against (GA), Goal Difference (GD), and any crucial team news or suspensions listed by the user.

STEP 2: SCENARIO ANALYSIS & GROUP MATHEMATICS
- Cross-reference the provided standings data to understand the true necessity of the result: Does a draw qualify someone? Does a team need a blowout win to advance on goal difference? Is anyone already eliminated or qualified?
- Assess the psychological weight and accumulated physical fatigue based on the match history provided for this World Cup.

STEP 3: EXPECTED GOALS MODELING (Adapted Poisson)
- Estimate the expected goals average (λ) for each team in the match, using as your primary baseline the offensive efficiency (GF) and defensive efficiency (GA) demonstrated in the user-provided data, adjusted by the quality of the opponents faced.
- Present the probabilities for the regular time (90 minutes) in percentages: Home/Team A Win (%), Draw (%), and Away/Team B Win (%). If it is a Knockout Stage match, add the final qualification probability.

STEP 4: TACTICAL PROJECTION & MOST LIKELY SCORELINE
- Briefly describe how the match is expected to unfold tactically based on each team's mathematical needs in the standings.
- Conclude by providing the MOST LIKELY EXACT SCORELINE for regular time (90 minutes).

Tone Guidelines: Analytical, focused on the tension and mathematical nuances of a short tournament, maintaining a pragmatic data scientist posture. Scoreless draws (0-0) are extremely common in high-pressure tournaments; if the tactical projection or mathematical models indicate a low-risk, highly defensive, or heavily fatigued matchup, you should predict a 0-0 draw if that is the most likely outcome.

Use the instructions above to predict the following game: {team1} vs {team2}.

At the very end of your response, on a new line, provide the final score in this exact format:
FINAL_SCORE: {team1} <SCORE 1> - <SCORE 2> {team2}

If the match is a Knockout Stage match and must be decided by a penalty shootout in case of a draw, format it as:
FINAL_SCORE: {team1} <SCORE 1> - <SCORE 2> {team2} (<PEN_WINNER> wins on penalties, e.g. <PEN_SCORE_1>-<PEN_SCORE_2> pens)
"""
    return prompt

def parse_scoreline(llm_response, team1, team2, stage):
    """
    Parses the LLM response text to find the scoreline.
    Returns:
      score1 (int), score2 (int), pen_winner (str/None), pen_score (str/None)
    """
    # Look for the FINAL_SCORE line
    # Format: FINAL_SCORE: Team1 Score1 - Score2 Team2
    # Or: FINAL_SCORE: Team1 Score1 - Score2 Team2 (Pen details)
    # We use a case-insensitive search
    match_line = re.search(
        r"FINAL_SCORE:\s*(.+?)\s+(\d+)\s*-\s*(\d+)\s+([^\n\r(]+)(?:\s*\((.+?)\))?",
        llm_response,
        re.IGNORECASE
    )
    
    if not match_line:
        print(f"Warning: Failed to match primary FINAL_SCORE regex pattern for {team1} vs {team2}.")
        # Fallback regex search anywhere in the text
        # (e.g. if the LLM did not write FINAL_SCORE but wrote Team A X - Y Team B)
        # We will try to find a score pattern at the end of the text
        pattern = rf"{re.escape(team1)}\s+(\d+)\s*-\s*(\d+)\s+{re.escape(team2)}"
        match_fallback = re.search(pattern, llm_response, re.IGNORECASE)
        if match_fallback:
            s1 = int(match_fallback.group(1))
            s2 = int(match_fallback.group(2))
            return s1, s2, None, None
            
        # Try finding any score like "Score: Team1 X - Y Team2" or "X - Y"
        match_any = re.search(r"(\d+)\s*-\s*(\d+)", llm_response)
        if match_any:
            return int(match_any.group(1)), int(match_any.group(2)), None, None
            
        # Hard fallback
        return 1, 0, None, None # default win
        
    t1 = match_line.group(1).strip()
    s1 = int(match_line.group(2))
    s2 = int(match_line.group(3))
    t2 = match_line.group(4).strip()
    pen_details = match_line.group(5)
    
    pen_winner = None
    pen_score = None
    
    # If it is a KO match and it is a tie, we need a winner!
    if stage != "group" and s1 == s2:
        if pen_details:
            # 1. Identify winner by name mention in details
            t1_mentioned = bool(re.search(re.escape(team1), pen_details, re.IGNORECASE)) if team1 else False
            t2_mentioned = bool(re.search(re.escape(team2), pen_details, re.IGNORECASE)) if team2 else False
            
            if t1_mentioned and not t2_mentioned:
                pen_winner = team1
            elif t2_mentioned and not t1_mentioned:
                pen_winner = team2
                
            # 2. Extract pen score digits
            pen_score_match = re.search(r"(\d+)-(\d+)\s*pens?", pen_details)
            if pen_score_match:
                p1, p2 = int(pen_score_match.group(1)), int(pen_score_match.group(2))
                pen_score = f"{p1}-{p2}"
                # If name wasn't conclusive, use digits
                if not pen_winner:
                    pen_winner = team1 if p1 > p2 else team2
            else:
                if not pen_winner:
                    pen_winner = team1
        else:
            # If no pen details but it is a tie in KO, assign a default penalty winner
            pen_winner = team1
            pen_score = "5-4"
            
    return s1, s2, pen_winner, pen_score

def predict_match(client, team1, team2, stage, group_name, standings, predictions_dict, model_name="gemini-3.1-pro-preview"):
    """
    Executes a match prediction using Gemini.
    """
    prompt = build_prompt(team1, team2, stage, group_name, standings, predictions_dict)
    
    # Generate content using Client
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        response_text = response.text
    except Exception as e:
        print(f"Error calling model {model_name}: {e}")
        # Return fallback text with a realistic random score
        # Weighted probability: 0 goals (20%), 1 goal (40%), 2 goals (25%), 3 goals (11%), 4 goals (4%)
        s1_fallback = random.choices([0, 1, 2, 3, 4], weights=[0.20, 0.40, 0.25, 0.11, 0.04])[0]
        s2_fallback = random.choices([0, 1, 2, 3, 4], weights=[0.20, 0.40, 0.25, 0.11, 0.04])[0]
        
        pen_winner_fallback = None
        pen_score_fallback = None
        if stage != "group" and s1_fallback == s2_fallback:
            p1 = random.randint(3, 5)
            p2 = random.randint(3, 5)
            while p1 == p2:
                p2 = random.randint(3, 5)
            pen_winner_fallback = team1 if p1 > p2 else team2
            pen_score_fallback = f"{p1}-{p2}"
            
        pen_part = f" ({pen_winner_fallback} wins on penalties, {pen_score_fallback} pens)" if pen_winner_fallback else ""
        response_text = (
            f"Fallback simulation match: {team1} vs {team2}. Technical error occurred: {e}.\n"
            f"FINAL_SCORE: {team1} {s1_fallback} - {s2_fallback} {team2}{pen_part}"
        )
        
    s1, s2, pen_winner, pen_score = parse_scoreline(response_text, team1, team2, stage)
    
    return {
        "team1": team1,
        "team2": team2,
        "score1": s1,
        "score2": s2,
        "pen_winner": pen_winner,
        "pen_score": pen_score,
        "is_played": True,
        "prompt_text": prompt,
        "prediction_text": response_text
    }
