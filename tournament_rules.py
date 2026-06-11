import json
import yaml

def get_group_standings(group_teams, group_matches):
    """
    Calculates standings for a single group.
    group_teams: list of team names in the group
    group_matches: list of matches in this group that have predictions
    Returns a sorted list of dicts with team stats:
    {
      "team": "Name", "mp": 3, "w": 2, "d": 0, "l": 1, "gf": 5, "ga": 3, "gd": 2, "pts": 6
    }
    """
    stats = {}
    for team in group_teams:
        stats[team] = {
            "team": team, "mp": 0, "w": 0, "d": 0, "l": 0, "gf": 0, "ga": 0, "gd": 0, "pts": 0
        }
        
    for m in group_matches:
        if not m.get("is_played", False):
            continue
        t1, t2 = m["team1"], m["team2"]
        s1, s2 = m["score1"], m["score2"]
        
        # Update stats
        stats[t1]["mp"] += 1
        stats[t2]["mp"] += 1
        stats[t1]["gf"] += s1
        stats[t2]["gf"] += s2
        stats[t1]["ga"] += s2
        stats[t2]["ga"] += s1
        
        if s1 > s2:
            stats[t1]["w"] += 1
            stats[t1]["pts"] += 3
            stats[t2]["l"] += 1
        elif s1 < s2:
            stats[t2]["w"] += 1
            stats[t2]["pts"] += 3
            stats[t1]["l"] += 1
        else:
            stats[t1]["d"] += 1
            stats[t1]["pts"] += 1
            stats[t2]["d"] += 1
            stats[t2]["pts"] += 1

    for team in stats:
        stats[team]["gd"] = stats[team]["gf"] - stats[team]["ga"]

    # Tie-breaking logic:
    # 1. Points
    # 2. Goal Difference
    # 3. Goals Scored
    # 4. Head-to-Head between tied teams (points, GD, GF)
    # 5. Alphabetical fallback
    
    # We will first sort teams using the primary criteria (PTS, GD, GF)
    # Then we check for ties, and apply H2H tiebreakers if necessary.
    teams_list = list(stats.values())
    
    # Group teams by their primary criteria (pts, gd, gf)
    primary_groups = {}
    for t in teams_list:
        key = (t["pts"], t["gd"], t["gf"])
        if key not in primary_groups:
            primary_groups[key] = []
        primary_groups[key].append(t)
        
    # Sort the group keys descending
    sorted_keys = sorted(primary_groups.keys(), key=lambda x: (x[0], x[1], x[2]), reverse=True)
    
    final_sorted_teams = []
    for key in sorted_keys:
        tied_teams = primary_groups[key]
        if len(tied_teams) == 1:
            final_sorted_teams.append(tied_teams[0])
        else:
            # We have a tie! Apply Head-to-Head criteria
            # Calculate H2H points, H2H GD, H2H GF in matches played between these tied teams
            tied_names = [t["team"] for t in tied_teams]
            h2h_stats = {name: {"pts": 0, "gd": 0, "gf": 0} for name in tied_names}
            
            for m in group_matches:
                if not m.get("is_played", False):
                    continue
                t1, t2 = m["team1"], m["team2"]
                if t1 in tied_names and t2 in tied_names:
                    s1, s2 = m["score1"], m["score2"]
                    h2h_stats[t1]["gf"] += s1
                    h2h_stats[t2]["gf"] += s2
                    h2h_stats[t1]["gd"] += (s1 - s2)
                    h2h_stats[t2]["gd"] += (s2 - s1)
                    if s1 > s2:
                        h2h_stats[t1]["pts"] += 3
                    elif s1 < s2:
                        h2h_stats[t2]["pts"] += 3
                    else:
                        h2h_stats[t1]["pts"] += 1
                        h2h_stats[t2]["pts"] += 1
                        
            # Sort tied teams by H2H stats, and then alphabetically as final fallback
            def h2h_key(t_stat):
                name = t_stat["team"]
                h2h = h2h_stats[name]
                # We want descending for stats, ascending for team name
                # Since we sort with reverse=True, we use negative name for alphabetical
                # But string sorting doesn't mix easily with negative, so we do custom sort or key:
                # We return a tuple where stats are positive and name is reversed/sorted.
                return (h2h["pts"], h2h["gd"], h2h["gf"])
                
            # Sort by h2h metrics first
            # Since python sort is stable, we can first sort alphabetically, then by H2H metrics descending
            tied_teams_sorted = sorted(tied_teams, key=lambda x: x["team"]) # A-Z
            tied_teams_sorted = sorted(tied_teams_sorted, key=h2h_key, reverse=True)
            
            final_sorted_teams.extend(tied_teams_sorted)
            
    return final_sorted_teams

def rank_third_placed_teams(standings_dict):
    """
    Ranks the 12 third-placed teams.
    standings_dict: dict mapping GroupLetter -> sorted standings list of 4 teams
    Returns:
      ranked_thirds: list of ranked 12 teams with stats, each having a 'group' key.
      qualified_groups: set of group letters (e.g. {'A', 'C', ...}) that finished in top 8.
    """
    thirds = []
    for g_letter, group_standings in standings_dict.items():
        if len(group_standings) >= 3:
            third_team_stats = dict(group_standings[2]) # copy stats
            third_team_stats["group"] = g_letter
            thirds.append(third_team_stats)
            
    # Sort thirds: Points (desc), GD (desc), GF (desc), then alphabetically (asc)
    # First sort alphabetically A-Z
    thirds_sorted = sorted(thirds, key=lambda x: x["team"])
    # Then sort by GF, GD, PTS desc
    thirds_sorted = sorted(thirds_sorted, key=lambda x: (x["pts"], x["gd"], x["gf"]), reverse=True)
    
    qualified_groups = {t["group"] for t in thirds_sorted[:8]}
    return thirds_sorted, qualified_groups

def resolve_knockout_bracket(matches_list, predictions_dict, groups_dict):
    """
    Re-calculates the standings, ranks 3rd place teams, and resolves placeholders in KO matches.
    matches_list: list of matches from matches.yaml (modified in-place)
    predictions_dict: dict of match predictions by match_id
    groups_dict: dict of groups A-L from groups.yaml
    Returns:
      standings: dict of GroupLetter -> sorted standings list
      ranked_thirds: list of ranked 3rd placed teams
      resolved_matches: the updated list of matches with actual team names resolved
    """
    # 1. Update group match results in-memory
    group_matches_by_group = {g: [] for g in "ABCDEFGHIJKL"}
    
    # We will map match schedule
    for m in matches_list:
        m_id = str(m["id"])
        pred = predictions_dict.get(m_id, {})
        
        # Set played status and score
        m["is_played"] = pred.get("is_played", False)
        if m["is_played"]:
            m["score1"] = pred["score1"]
            m["score2"] = pred["score2"]
            m["pen_winner"] = pred.get("pen_winner")
            m["pen_score"] = pred.get("pen_score")
            m["prediction_text"] = pred.get("prediction_text")
            m["prompt_text"] = pred.get("prompt_text")
            
        if m["stage"] == "group":
            group_matches_by_group[m["group"]].append(m)

    # 2. Calculate group standings
    standings = {}
    for g_letter, g_teams in groups_dict.items():
        g_code = g_letter.split()[-1] # "Group A" -> "A"
        standings[g_code] = get_group_standings(g_teams, group_matches_by_group[g_code])

    # 3. Rank third-placed teams
    ranked_thirds, qualified_groups = rank_third_placed_teams(standings)

    # 4. Load third place combinations
    try:
        with open("third_place_combinations.json", "r") as f:
            combinations_list = json.load(f)
    except FileNotFoundError:
        combinations_list = []

    # Map combination key (e.g. "ABCDEFGH") to mapping dict
    combinations_map = {}
    for row in combinations_list:
        combinations_map[row["groups"]] = row["mapping"]

    # Find the combination key
    qualified_key = "".join(sorted(list(qualified_groups)))
    
    # Active mapping for 3rd place teams, e.g. {"1A": "3C", "1B": "3D", ...}
    active_3rd_mapping = combinations_map.get(qualified_key, {})

    # Helper function to find a team by placeholder
    # Placeholders are:
    # - "Winner Group X"
    # - "Runner-up Group X"
    # - "3rd Group X/Y/Z..."
    # - "Winner Match X"
    # - "Loser Match X"
    def resolve_team(placeholder, match_num=None):
        if not placeholder:
            return None
            
        placeholder = placeholder.strip()
        
        if placeholder.startswith("Winner Group"):
            g = placeholder.split()[-1]
            if g in standings and len(standings[g]) >= 1:
                return standings[g][0]["team"]
            return None
            
        elif placeholder.startswith("Runner-up Group"):
            g = placeholder.split()[-1]
            if g in standings and len(standings[g]) >= 2:
                return standings[g][1]["team"]
            return None
            
        elif placeholder.startswith("3rd Group"):
            # This is a variable 3rd place slot.
            # We must determine which winner is playing this slot, which corresponds to the match.
            # Match assignments:
            # Match 74 (Winner E vs 3rd A/B/C/D/F): corresponds to "1E" column in combinations mapping
            # Match 77 (Winner I vs 3rd C/D/F/G/H): "1I"
            # Match 79 (Winner A vs 3rd C/E/F/H/I): "1A"
            # Match 80 (Winner L vs 3rd E/H/I/J/K): "1L"
            # Match 81 (Winner D vs 3rd B/E/F/I/J): "1D"
            # Match 82 (Winner G vs 3rd A/E/H/I/J): "1G"
            # Match 85 (Winner B vs 3rd E/F/G/I/J): "1B"
            # Match 87 (Winner K vs 3rd D/E/I/J/L): "1K"
            # Wait, let's map match_num to the winner key:
            match_to_winner_key = {
                74: "1E",
                77: "1I",
                79: "1A",
                80: "1L",
                81: "1D",
                82: "1G",
                85: "1B",
                87: "1K"
            }
            if match_num in match_to_winner_key:
                w_key = match_to_winner_key[match_num]
                mapped_3rd_group_code = active_3rd_mapping.get(w_key) # e.g. "3E" -> group E
                if mapped_3rd_group_code:
                    g_letter = mapped_3rd_group_code[-1] # extract "E"
                    if g_letter in standings and len(standings[g_letter]) >= 3:
                        return standings[g_letter][2]["team"]
            return None
            
        elif placeholder.startswith("Winner Match"):
            m_num = int(placeholder.split()[-1])
            # Find the match with match_num == m_num or id == m_num
            # In matches.yaml, group stage matches don't have match_num, but KO matches have match_num.
            # Actually, let's search matches_list for match_num == m_num or id == m_num.
            target_match = None
            for m in matches_list:
                if m.get("match_num") == m_num or m.get("id") == m_num:
                    target_match = m
                    break
            if target_match and target_match.get("is_played", False):
                # Calculate winner
                t1, t2 = target_match["team1"], target_match["team2"]
                s1, s2 = target_match["score1"], target_match["score2"]
                if s1 > s2:
                    return t1
                elif s1 < s2:
                    return t2
                else:
                    return target_match.get("pen_winner")
            return None
            
        elif placeholder.startswith("Loser Match"):
            m_num = int(placeholder.split()[-1])
            target_match = None
            for m in matches_list:
                if m.get("match_num") == m_num or m.get("id") == m_num:
                    target_match = m
                    break
            if target_match and target_match.get("is_played", False):
                # Calculate loser
                t1, t2 = target_match["team1"], target_match["team2"]
                s1, s2 = target_match["score1"], target_match["score2"]
                if s1 > s2:
                    return t2
                elif s1 < s2:
                    return t1
                else:
                    pw = target_match.get("pen_winner")
                    return t2 if pw == t1 else t1
            return None
            
        return placeholder

    # 5. Resolve KO placeholders chronologically
    # We must resolve matches in order because later matches (e.g. R16) depend on the resolved winners of earlier matches (R32).
    # Since matches_list is sorted, we can just iterate.
    for m in matches_list:
        if m["stage"] != "group":
            m_num = m.get("match_num")
            
            # Resolve team1
            if "team1" not in m or m.get("team1_placeholder"):
                t1_placeholder = m.get("team1_placeholder")
                t1_resolved = resolve_team(t1_placeholder, m_num)
                if t1_resolved:
                    m["team1"] = t1_resolved
                else:
                    # Maintain the placeholder if not resolved yet
                    m["team1"] = t1_placeholder
                    
            # Resolve team2
            if "team2" not in m or m.get("team2_placeholder"):
                t2_placeholder = m.get("team2_placeholder")
                t2_resolved = resolve_team(t2_placeholder, m_num)
                if t2_resolved:
                    m["team2"] = t2_resolved
                else:
                    m["team2"] = t2_placeholder
                    
            # Propagate values to matches_list in predictions as well, in case we need them
            m_id = str(m["id"])
            if m_id in predictions_dict:
                predictions_dict[m_id]["team1"] = m["team1"]
                predictions_dict[m_id]["team2"] = m["team2"]

    return standings, ranked_thirds, matches_list
