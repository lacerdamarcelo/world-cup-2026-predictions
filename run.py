import argparse
import json
import os
import yaml
from tournament_rules import resolve_knockout_bracket
from prediction_engine import get_genai_client, predict_match, format_standings_table

# File paths
GROUPS_FILE = "groups.yaml"
MATCHES_FILE = "matches.yaml"
PREDICTIONS_FILE = "predictions.json"
PROMPTS_FILE = "prompts.json"
STATE_FILE = "tournament_state.json"

def load_data():
    # Load groups
    with open(GROUPS_FILE, "r") as f:
        groups = yaml.safe_load(f)
        
    # Load matches
    with open(MATCHES_FILE, "r") as f:
        matches = yaml.safe_load(f)
        
    # Load predictions
    if os.path.exists(PREDICTIONS_FILE):
        with open(PREDICTIONS_FILE, "r") as f:
            predictions = json.load(f)
    else:
        predictions = {}
        
    return groups, matches, predictions

def save_predictions(predictions):
    with open(PREDICTIONS_FILE, "w") as f:
        json.dump(predictions, f, indent=2)
        
    # Extract and save prompts in a separate prompts.json file
    prompts = {}
    for m_id, pred in predictions.items():
        if "prompt_text" in pred:
            prompts[m_id] = pred["prompt_text"]
            
    with open(PROMPTS_FILE, "w") as f:
        json.dump(prompts, f, indent=2)

def save_state(standings, ranked_thirds, matches):
    state = {
        "standings": standings,
        "ranked_thirds": ranked_thirds,
        "matches": matches
    }
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)
    print(f"Tournament state updated in {STATE_FILE}.")

def print_status(standings, ranked_thirds, matches):
    print("\n" + "="*50)
    print("         FIFA WORLD CUP 2026 STATUS")
    print("="*50)
    
    # Count played matches
    played_count = sum(1 for m in matches if m.get("is_played", False))
    print(f"Matches Played: {played_count} / 104\n")
    
    print("--- GROUP STANDINGS ---")
    for g_code in sorted(standings.keys()):
        print(f"\nGroup {g_code}:")
        print(format_standings_table(standings[g_code]))
        
    print("\n--- BEST 3RD-PLACED TEAMS RANKING ---")
    print("| Pos | Team | Group | MP | W | D | L | GF | GA | GD | Pts |")
    print("| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
    for idx, t in enumerate(ranked_thirds):
        qual_marker = "✅" if idx < 8 else "❌"
        print(f"| {idx+1} {qual_marker} | {t['team']} | {t['group']} | {t['mp']} | {t['w']} | {t['d']} | {t['l']} | {t['gf']} | {t['ga']} | {t['gd']} | {t['pts']} |")

def run_predictions(limit=None, api_key=None, model_name="gemini-3.1-pro-preview"):
    groups, matches, predictions = load_data()
    
    # Initial state resolution
    standings, ranked_thirds, resolved_matches = resolve_knockout_bracket(matches, predictions, groups)
    save_state(standings, ranked_thirds, resolved_matches)
    
    # Find matches to predict starting strictly after the highest predicted match ID
    played_ids = [int(m_id) for m_id, pred in predictions.items() if pred.get("is_played", False)]
    max_played_id = max(played_ids) if played_ids else 0
    
    matches_to_predict = []
    for m in resolved_matches:
        if int(m["id"]) > max_played_id:
            matches_to_predict.append(m)
            
    if not matches_to_predict:
        print("All matches have already been predicted!")
        return
        
    if limit is not None:
        matches_to_predict = matches_to_predict[:limit]
        
    print(f"Starting prediction run for {len(matches_to_predict)} matches...")
    
    # Initialize API Client
    try:
        client = get_genai_client(api_key)
    except Exception as e:
        print(f"\nConfiguration Error: {e}")
        return

    for idx, m in enumerate(matches_to_predict):
        m_id = str(m["id"])
        stage = m["stage"]
        
        # Resolve KO matches placeholders again in-loop (in case previous matches in this run unlocked them)
        standings, ranked_thirds, resolved_matches = resolve_knockout_bracket(matches, predictions, groups)
        # Find current match in resolved list to get updated team names
        m_resolved = next(item for item in resolved_matches if item["id"] == m["id"])
        
        t1, t2 = m_resolved["team1"], m_resolved["team2"]
        
        # Check if placeholders are fully resolved
        # Placeholders contain keywords like Group, Winner, Loser, Match, 3rd, etc.
        placeholders_keywords = ["Group", "Winner", "Loser", "Match", "3rd"]
        t1_is_placeholder = any(kw in str(t1) for kw in placeholders_keywords) if t1 else True
        t2_is_placeholder = any(kw in str(t2) for kw in placeholders_keywords) if t2 else True
        
        if t1_is_placeholder or t2_is_placeholder:
            print(f"Skipping Match {m_id} ({stage}): Teams are not fully resolved yet ({t1} vs {t2}).")
            break
            
        print(f"\n[{idx+1}/{len(matches_to_predict)}] Predicting Match {m_id} ({stage}): {t1} vs {t2}")
        
        # Get standings of the group if it is a group stage match
        group_standings = None
        if stage == "group":
            group_standings = standings.get(m_resolved["group"])
            
        # Call Gemini to predict match
        result = predict_match(client, t1, t2, stage, m_resolved.get("group"), group_standings, predictions, model_name)
        
        # Update predictions dict and save immediately
        predictions[m_id] = result
        save_predictions(predictions)
        
        print(f"Result: {t1} {result['score1']} - {result['score2']} {t2}")
        if result.get("pen_winner"):
            print(f"Penalty Shootout: {result['pen_winner']} won ({result['pen_score']})")
            
        # Re-resolve and save state after each prediction
        standings, ranked_thirds, resolved_matches = resolve_knockout_bracket(matches, predictions, groups)
        save_state(standings, ranked_thirds, resolved_matches)

def reset_predictions():
    if os.path.exists(PREDICTIONS_FILE):
        os.remove(PREDICTIONS_FILE)
        print(f"Deleted {PREDICTIONS_FILE}.")
    if os.path.exists(PROMPTS_FILE):
        os.remove(PROMPTS_FILE)
        print(f"Deleted {PROMPTS_FILE}.")
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
        print(f"Deleted {STATE_FILE}.")
    print("Tournament simulation has been reset.")

def main():
    parser = argparse.ArgumentParser(description="FIFA World Cup 2026 Gemini Predictor CLI")
    
    parser.add_argument("--predict-next", type=int, help="Predict the next N matches in chronological order")
    parser.add_argument("--predict-all", action="store_true", help="Predict all remaining matches")
    parser.add_argument("--reset", action="store_true", help="Reset and clear all predictions")
    parser.add_argument("--status", action="store_true", help="Print current standings and bracket status in terminal")
    parser.add_argument("--show-next-prompt", action="store_true", help="Print the Gemini prompt for the next upcoming resolved match and exit")
    parser.add_argument("--api-key", type=str, help="Gemini API Key (optional if GEMINI_API_KEY is in environment or .env)")
    parser.add_argument("--model", type=str, default="gemini-3.1-pro-preview", help="Gemini Model name to query (default: gemini-3.1-pro-preview)")
    
    args = parser.parse_args()
    
    if args.reset:
        reset_predictions()
    elif args.status:
        groups, matches, predictions = load_data()
        standings, ranked_thirds, resolved_matches = resolve_knockout_bracket(matches, predictions, groups)
        print_status(standings, ranked_thirds, resolved_matches)
    elif args.show_next_prompt:
        # Wait, since show-next-prompt has a hyphen, argparse changes it to show_next_prompt
        groups, matches, predictions = load_data()
        standings, ranked_thirds, resolved_matches = resolve_knockout_bracket(matches, predictions, groups)
        
        # Find next match to predict starting strictly after the highest predicted match ID
        played_ids = [int(m_id) for m_id, pred in predictions.items() if pred.get("is_played", False)]
        max_played_id = max(played_ids) if played_ids else 0
        
        next_match = None
        for m in resolved_matches:
            if int(m["id"]) > max_played_id:
                next_match = m
                break
                
        if not next_match:
            print("All matches have already been predicted!")
            return
            
        t1, t2 = next_match["team1"], next_match["team2"]
        stage = next_match["stage"]
        
        placeholders_keywords = ["Group", "Winner", "Loser", "Match", "3rd"]
        t1_is_placeholder = any(kw in str(t1) for kw in placeholders_keywords) if t1 else True
        t2_is_placeholder = any(kw in str(t2) for kw in placeholders_keywords) if t2 else True
        
        if t1_is_placeholder or t2_is_placeholder:
            print(f"Next Match {next_match['id']} ({stage}): Teams are not fully resolved yet ({t1} vs {t2}).")
            return
            
        from prediction_engine import build_prompt
        group_standings = standings.get(next_match["group"]) if stage == "group" else None
        prompt = build_prompt(t1, t2, stage, next_match.get("group"), group_standings, predictions)
        
        print("\n" + "="*80)
        print(f"PROMPT FOR MATCH {next_match['id']} ({stage}): {t1} vs {t2}")
        print("="*80)
        print(prompt)
        print("="*80 + "\n")
    elif args.predict_next:
        run_predictions(limit=args.predict_next, api_key=args.api_key, model_name=args.model)
    elif args.predict_all:
        run_predictions(limit=None, api_key=args.api_key, model_name=args.model)
    else:
        # If no arguments provided, print help or current status
        groups, matches, predictions = load_data()
        try:
            standings, ranked_thirds, resolved_matches = resolve_knockout_bracket(matches, predictions, groups)
            print_status(standings, ranked_thirds, resolved_matches)
        except Exception as e:
            print("Welcome to World Cup 2026 Predictions CLI!")
            print("Run with -h to view options.")

if __name__ == "__main__":
    main()
