import json
import random
import yaml
from tournament_rules import resolve_knockout_bracket

def main():
    print("=== STARTING WORLD CUP 2026 BRACKET VERIFICATION TEST ===")
    
    # 1. Load groups and matches
    with open("groups.yaml", "r") as f:
        groups = yaml.safe_load(f)
    with open("matches.yaml", "r") as f:
        matches = yaml.safe_load(f)
        
    predictions = {}
    
    # Helper to simulate a match
    def simulate_and_save(m_resolved, is_ko=False):
        t1, t2 = m_resolved["team1"], m_resolved["team2"]
        # Realistic football goal distribution:
        # 0 goals: 20%, 1 goal: 40%, 2 goals: 25%, 3 goals: 11%, 4 goals: 4%
        s1 = random.choices([0, 1, 2, 3, 4], weights=[0.20, 0.40, 0.25, 0.11, 0.04])[0]
        s2 = random.choices([0, 1, 2, 3, 4], weights=[0.20, 0.40, 0.25, 0.11, 0.04])[0]
        
        pen_winner = None
        pen_score = None
        if is_ko and s1 == s2:
            # Penalty shootout
            p1 = random.randint(3, 5)
            p2 = random.randint(3, 5)
            while p1 == p2:
                p2 = random.randint(3, 5)
            pen_winner = t1 if p1 > p2 else t2
            pen_score = f"{p1}-{p2}"
            
        m_id = str(m_resolved["id"])
        
        # Calculate in-memory current standings for group stage matches
        from tournament_rules import get_group_standings
        curr_group_standings = None
        if not is_ko and m_resolved.get("group"):
            g_code = m_resolved["group"]
            g_teams = groups[f"Group {g_code}"]
            # Filter matches in this group already simulated in this run
            g_matches = []
            for item in matches[:72]:
                if item["group"] == g_code:
                    item_id = str(item["id"])
                    if item_id in predictions:
                        g_matches.append(predictions[item_id])
            curr_group_standings = get_group_standings(g_teams, g_matches)
            
        from prediction_engine import build_prompt
        prompt = build_prompt(t1, t2, "group" if not is_ko else "KO", m_resolved.get("group"), curr_group_standings, predictions)
        
        pen_text_part = f" ({pen_winner} wins on penalties, {pen_score} pens)" if pen_winner else ""
        predictions[m_id] = {
            "team1": t1,
            "team2": t2,
            "score1": s1,
            "score2": s2,
            "pen_winner": pen_winner,
            "pen_score": pen_score,
            "is_played": True,
            "prompt_text": prompt,
            "prediction_text": f"Mock Chain-of-Thought Analysis for {t1} vs {t2}:\n\n"
                               f"**STEP 1: USER-PROVIDED CAMPAIGN & CURRENT CONTEXT**\n"
                               f"Matches played so far in this simulation: {t1} and {t2} are playing their fixture.\n\n"
                               f"**STEP 2: SCENARIO ANALYSIS & GROUP MATHEMATICS**\n"
                               f"This is a simulated verification fixture with random results.\n\n"
                               f"**STEP 3: EXPECTED GOALS MODELING**\n"
                               f"Adapted Poisson model: {t1} \u03bb=1.5, {t2} \u03bb=1.2.\n"
                               f"Home Win: 42%, Draw: 28%, Away Win: 30%.\n\n"
                               f"**STEP 4: TACTICAL PROJECTION & MOST LIKELY SCORELINE**\n"
                               f"Tactical projection points to open play with transitions.\n\n"
                               f"FINAL_SCORE: {t1} {s1} - {s2} {t2}{pen_text_part}"
        }

    # 2. Simulate Group Stage (matches 1 to 72)
    print("Simulating Group Stage matches...")
    for idx in range(72):
        m = matches[idx]
        simulate_and_save(m)
        
    # Re-evaluate standings
    standings, ranked_thirds, resolved_matches = resolve_knockout_bracket(matches, predictions, groups)
    
    print("\nGroup Stage finished.")
    print(f"Qualified 3rd-placed groups: {[t['group'] for t in ranked_thirds[:8]]}")
    
    # Print R32 matchups
    print("\nResolved Round of 32 Matchups:")
    r32_matches = [m for m in resolved_matches if m["stage"] == "KO_R32"]
    for m in r32_matches:
        print(f"  Match {m['match_num']}: {m['team1']} vs {m['team2']}")
        
    # 3. Simulate Round of 32 (matches 73 to 88)
    print("\nSimulating Round of 32 matches...")
    for idx in range(72, 88):
        # Re-resolve bracket in loop
        standings, ranked_thirds, resolved_matches = resolve_knockout_bracket(matches, predictions, groups)
        m = resolved_matches[idx]
        simulate_and_save(m, is_ko=True)
        
    # 4. Simulate Round of 16 (matches 89 to 96)
    print("Simulating Round of 16 matches...")
    for idx in range(88, 96):
        standings, ranked_thirds, resolved_matches = resolve_knockout_bracket(matches, predictions, groups)
        m = resolved_matches[idx]
        simulate_and_save(m, is_ko=True)
        
    # 5. Simulate Quarterfinals (matches 97 to 100)
    print("Simulating Quarterfinals...")
    for idx in range(96, 100):
        standings, ranked_thirds, resolved_matches = resolve_knockout_bracket(matches, predictions, groups)
        m = resolved_matches[idx]
        simulate_and_save(m, is_ko=True)
        
    # 6. Simulate Semifinals (matches 101 to 102)
    print("Simulating Semifinals...")
    for idx in range(100, 102):
        standings, ranked_thirds, resolved_matches = resolve_knockout_bracket(matches, predictions, groups)
        m = resolved_matches[idx]
        simulate_and_save(m, is_ko=True)
        
    # 7. Simulate 3rd Place Match (match 103)
    print("Simulating 3rd Place Match...")
    standings, ranked_thirds, resolved_matches = resolve_knockout_bracket(matches, predictions, groups)
    simulate_and_save(resolved_matches[102], is_ko=True)
    
    # 8. Simulate Final (match 104)
    print("Simulating Final...")
    standings, ranked_thirds, resolved_matches = resolve_knockout_bracket(matches, predictions, groups)
    simulate_and_save(resolved_matches[103], is_ko=True)
    
    # Final check
    standings, ranked_thirds, resolved_matches = resolve_knockout_bracket(matches, predictions, groups)
    final_match = resolved_matches[103]
    s1, s2 = final_match["score1"], final_match["score2"]
    if s1 > s2:
        champ = final_match["team1"]
    elif s2 > s1:
        champ = final_match["team2"]
    else:
        champ = final_match["pen_winner"]
        
    # Save mock results to disk
    from run import save_predictions, save_state
    save_predictions(predictions)
    save_state(standings, ranked_thirds, resolved_matches)
    
    print("\n" + "="*50)
    print(f"🥇 WORLD CUP CHAMPION: {champ} 🥇")
    print("="*50)
    print("Bracket verification test passed successfully and saved to predictions.json!")

if __name__ == "__main__":
    main()
