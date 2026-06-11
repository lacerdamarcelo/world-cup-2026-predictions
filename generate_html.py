import json
import os
import yaml

def main():
    state_file = "tournament_state.json"
    predictions_file = "predictions.json"
    
    if not os.path.exists(state_file):
        print(f"State file {state_file} not found. Please run simulations first.")
        return
        
    with open(state_file, "r") as f:
        state = json.load(f)
        
    predictions = {}
    if os.path.exists(predictions_file):
        with open(predictions_file, "r") as f:
            predictions = json.load(f)
            
    # Enrich matches with text if they are not already in state
    for m in state.get("matches", []):
        m_id = str(m["id"])
        if m_id in predictions:
            m["prediction_text"] = predictions[m_id].get("prediction_text", "")
            m["prompt_text"] = predictions[m_id].get("prompt_text", "")
            
    standings = state.get("standings", {})
    ranked_thirds = state.get("ranked_thirds", [])
    matches = state.get("matches", [])
    
    # Calculate stats
    total_played = sum(1 for m in matches if m.get("is_played"))
    total_goals = sum(m.get("score1", 0) + m.get("score2", 0) for m in matches if m.get("is_played"))
    
    # Get Champion
    champ = "TBD"
    final_match = next((m for m in matches if m.get("stage") == "KO_FINAL"), None)
    if final_match and final_match.get("is_played"):
        s1, s2 = final_match["score1"], final_match["score2"]
        if s1 > s2:
            champ = final_match["team1"]
        elif s2 > s1:
            champ = final_match["team2"]
        else:
            champ = final_match.get("pen_winner", "TBD")
            
    # Generate HTML content
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FIFA World Cup 2026 Simulation Report</title>
    <!-- Google Fonts Outfit & Inter -->
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #060913;
            --card-bg: rgba(15, 23, 42, 0.65);
            --border-color: rgba(255, 255, 255, 0.08);
            --text-color: #e2e8f0;
            --text-muted: #94a3b8;
            --primary: #0ea5e9;
            --success: #00ff87;
            --warning: #f59e0b;
        }}
        
        body {{
            background-color: var(--bg-color);
            background-image: radial-gradient(circle at 10% 20%, rgba(4, 21, 45, 0.6) 0%, rgba(6, 9, 19, 1) 90%);
            color: var(--text-color);
            font-family: 'Outfit', 'Inter', sans-serif;
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        
        h1 {{
            font-size: 2.5rem;
            margin: 10px 0;
            font-weight: 800;
            letter-spacing: 1px;
            text-shadow: 0 0 15px rgba(14, 165, 233, 0.3);
        }}
        
        .title-fifa {{ color: #ffffff; }}
        .title-world {{ color: var(--primary); }}
        .title-2026 {{ color: var(--success); }}
        
        .subtitle {{
            font-size: 1.1rem;
            color: var(--text-muted);
            margin-bottom: 20px;
        }}
        
        /* Stats Row */
        .stats-row {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .stat-card {{
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-3px);
            border-color: rgba(255, 255, 255, 0.15);
        }}
        
        .stat-card small {{
            display: block;
            font-size: 0.85rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }}
        
        .stat-card h3 {{
            margin: 0;
            font-size: 1.8rem;
            font-weight: 700;
        }}
        
        .text-cyan {{ color: var(--primary); text-shadow: 0 0 10px rgba(14, 165, 233, 0.4); }}
        .text-green {{ color: var(--success); text-shadow: 0 0 10px rgba(0, 255, 135, 0.4); }}
        .text-gold {{ color: var(--warning); text-shadow: 0 0 10px rgba(245, 158, 11, 0.4); }}
        
        /* Interactive Controls */
        .controls-card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 40px;
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            align-items: center;
            gap: 20px;
        }}
        
        .control-group {{
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            align-items: center;
        }}
        
        .toggle-btn {{
            background: rgba(30, 41, 59, 0.6);
            border: 1px solid var(--border-color);
            color: var(--text-color);
            padding: 8px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            font-size: 0.85rem;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .toggle-btn:hover {{
            background: rgba(255, 255, 255, 0.05);
            border-color: rgba(255,255,255,0.2);
        }}
        
        .toggle-btn.active {{
            background: rgba(14, 165, 233, 0.2);
            border-color: var(--primary);
            color: var(--primary);
        }}
        
        .search-input {{
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid var(--border-color);
            color: var(--text-color);
            padding: 10px 16px;
            border-radius: 8px;
            width: 250px;
            outline: none;
            font-family: inherit;
        }}
        
        .search-input:focus {{
            border-color: var(--primary);
            box-shadow: 0 0 8px rgba(14, 165, 233, 0.3);
        }}
        
        .select-filter {{
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid var(--border-color);
            color: var(--text-color);
            padding: 10px 16px;
            border-radius: 8px;
            outline: none;
            cursor: pointer;
            font-family: inherit;
        }}
        
        /* Section Heading */
        .section-header {{
            margin-bottom: 20px;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .section-header h2 {{
            margin: 0;
            font-size: 1.8rem;
            font-weight: 700;
        }}
        
        /* Standings Grid */
        .standings-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .group-card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 15px;
        }}
        
        .group-title {{
            font-weight: 700;
            font-size: 1.1rem;
            color: var(--primary);
            margin-top: 0;
            margin-bottom: 12px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            padding-bottom: 6px;
        }}
        
        .standings-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.82rem;
            text-align: center;
        }}
        
        .standings-table th {{
            color: var(--text-muted);
            font-weight: 600;
            padding: 6px;
            border-bottom: 1px solid var(--border-color);
        }}
        
        .standings-table td {{
            padding: 6px;
            border-bottom: 1px solid rgba(255,255,255,0.03);
        }}
        
        .standings-table td.team-name {{
            text-align: left;
            font-weight: 600;
            max-width: 110px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        
        .standings-table tr.qualify-direct {{
            background: rgba(16, 185, 129, 0.05);
        }}
        
        .standings-table tr.qualify-3rd {{
            background: rgba(14, 165, 233, 0.04);
        }}
        
        /* 3rd place rankings */
        .thirds-card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 40px;
            overflow-x: auto;
        }}
        
        /* Bracket Layout */
        .bracket-container {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 40px;
            display: flex;
            flex-direction: row;
            justify-content: space-between;
            overflow-x: auto;
            overflow-y: auto;
            gap: 25px;
            min-width: 1100px;
            height: 600px;
        }}
        
        .bracket-column {{
            display: flex;
            flex-direction: column;
            justify-content: space-around;
            width: 220px;
            height: 100%;
        }}
        
        .bracket-column h4 {{
            text-align: center;
            font-size: 0.95rem;
            color: var(--text-muted);
            margin: 0 0 10px 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            padding-bottom: 6px;
        }}
        
        .bracket-match {{
            background: rgba(15, 23, 42, 0.7);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 8px;
            font-size: 0.75rem;
            margin: 4px 0;
            box-shadow: 0 4px 10px rgba(0,0,0,0.2);
            transition: all 0.2s ease;
        }}
        
        .bracket-match:hover {{
            transform: translateY(-2px);
            border-color: rgba(14, 165, 233, 0.4);
        }}
        
        .bracket-match-header {{
            display: flex;
            justify-content: space-between;
            color: var(--text-muted);
            font-size: 0.68rem;
            border-bottom: 1px solid rgba(255,255,255,0.03);
            padding-bottom: 3px;
            margin-bottom: 5px;
        }}
        
        .bracket-match-team {{
            display: flex;
            justify-content: space-between;
            padding: 2px 0;
        }}
        
        .bracket-match-team.winner {{
            color: var(--success);
            font-weight: 700;
        }}
        
        .bracket-match-score {{
            font-weight: 700;
            background: rgba(30, 41, 59, 0.5);
            padding: 1px 5px;
            border-radius: 3px;
            min-width: 14px;
            text-align: center;
        }}
        
        /* Matches Accordion List */
        .matches-list {{
            display: flex;
            flex-direction: column;
            gap: 15px;
            margin-bottom: 40px;
        }}
        
        .match-row {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            overflow: hidden;
            transition: all 0.2s ease;
        }}
        
        .match-row:hover {{
            border-color: rgba(255, 255, 255, 0.12);
        }}
        
        .match-summary {{
            padding: 16px 20px;
            cursor: pointer;
            display: grid;
            grid-template-columns: 80px 120px 1fr 120px;
            align-items: center;
            gap: 15px;
            user-select: none;
        }}
        
        .match-num {{
            font-weight: 700;
            color: var(--text-muted);
            font-size: 0.85rem;
        }}
        
        .match-stage-label {{
            font-size: 0.78rem;
            color: var(--primary);
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }}
        
        .match-teams-score {{
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 1.05rem;
            font-weight: 600;
            gap: 20px;
        }}
        
        .match-teams-score .team-col {{
            flex: 1;
            display: flex;
            align-items: center;
        }}
        
        .match-teams-score .team-col.team1 {{ justify-content: flex-end; text-align: right; }}
        .match-teams-score .team-col.team2 {{ justify-content: flex-start; text-align: left; }}
        
        .match-teams-score .score-box {{
            background: rgba(30, 41, 59, 0.8);
            border: 1px solid rgba(255,255,255,0.05);
            padding: 4px 14px;
            border-radius: 6px;
            font-weight: 800;
            color: var(--success);
            font-size: 1.1rem;
            min-width: 45px;
            text-align: center;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.3);
        }}
        
        .match-status-pill {{
            justify-self: flex-end;
            font-size: 0.75rem;
            background: rgba(16, 185, 129, 0.15);
            color: var(--success);
            border: 1px solid rgba(0, 255, 135, 0.2);
            padding: 4px 10px;
            border-radius: 20px;
            font-weight: 600;
        }}
        
        .match-status-pill.upcoming {{
            background: rgba(245, 158, 11, 0.1);
            color: var(--warning);
            border-color: rgba(245, 158, 11, 0.2);
        }}
        
        /* Expanded reasoning content */
        .match-details {{
            display: none;
            background: rgba(9, 13, 24, 0.6);
            border-top: 1px solid var(--border-color);
            padding: 20px;
        }}
        
        .tabs-header {{
            display: flex;
            gap: 10px;
            border-bottom: 1px solid rgba(255,255,255,0.06);
            margin-bottom: 15px;
        }}
        
        .tab-link {{
            background: transparent;
            border: none;
            color: var(--text-muted);
            padding: 8px 16px;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.2s ease;
        }}
        
        .tab-link:hover {{
            color: var(--text-color);
        }}
        
        .tab-link.active {{
            color: var(--primary);
            border-bottom-color: var(--primary);
        }}
        
        .tab-content {{
            display: none;
            font-size: 0.88rem;
            line-height: 1.6;
            color: #cbd5e1;
            white-space: pre-line;
            max-height: 400px;
            overflow-y: auto;
            background: rgba(15, 23, 42, 0.4);
            border-radius: 8px;
            padding: 15px;
            border: 1px solid rgba(255,255,255,0.03);
        }}
        
        .tab-content.active {{
            display: block;
        }}
        
        /* Chevron expand indicator */
        .chevron::after {{
            content: '▼';
            font-size: 0.65rem;
            color: var(--text-muted);
            margin-left: 8px;
            display: inline-block;
            transition: transform 0.2s ease;
        }}
        
        .match-row.open .chevron::after {{
            transform: rotate(-180deg);
        }}
        
        @media (max-width: 768px) {{
            .match-summary {{
                grid-template-columns: 50px 1fr 100px;
                grid-template-rows: auto auto;
                gap: 8px;
                padding: 12px;
            }}
            .match-stage-label {{
                grid-column: 2;
                grid-row: 1;
            }}
            .match-teams-score {{
                grid-column: 1 / span 3;
                grid-row: 2;
                font-size: 0.95rem;
            }}
            .match-status-pill {{
                grid-column: 3;
                grid-row: 1;
            }}
        }}
    </style>
</head>
<body>

<div class="container">
    <header>
        <h1>
            <span class="title-fifa">FIFA </span>
            <span class="title-world">WORLD CUP </span>
            <span class="title-2026">2026</span>
        </h1>
        <div class="subtitle">Statistical Simulation & Prediction Analysis Report</div>
    </header>
    
    <!-- Stats Cards -->
    <div class="stats-row">
        <div class="stat-card">
            <small>Simulation Progress</small>
            <h3 class="text-cyan">{total_played} / 104 Matches</h3>
        </div>
        <div class="stat-card">
            <small>Total Goals Scored</small>
            <h3 class="text-green">{total_goals} Goals</h3>
        </div>
        <div class="stat-card">
            <small>Predicted Champion</small>
            <h3 class="text-gold">🏆 {champ}</h3>
        </div>
    </div>
    
    <!-- Interactive Toolbar -->
    <div class="controls-card">
        <div class="control-group">
            <button id="toggle-standings" class="toggle-btn active" onclick="toggleSection('standings-outer', this)">
                📁 Hide Standings
            </button>
            <button id="toggle-group-results" class="toggle-btn active" onclick="toggleGroupResults(this)">
                ⚽ Show Group Stage Matches
            </button>
        </div>
        <div class="control-group">
            <input type="text" id="team-search" class="search-input" placeholder="Search by team..." onkeyup="filterMatches()">
            <select id="stage-filter" class="select-filter" onchange="filterMatches()">
                <option value="all">All Stages</option>
                <option value="group">Group Stage</option>
                <option value="KO_R32">Round of 32</option>
                <option value="KO_R16">Round of 16</option>
                <option value="KO_QF">Quarterfinals</option>
                <option value="KO_SF">Semifinals</option>
                <option value="KO_FINAL">Finals</option>
            </select>
        </div>
    </div>
    
    <!-- Group Standings Section -->
    <div id="standings-outer">
        <div class="section-header">
            <h2>Group Stage Standings</h2>
        </div>
        <div class="standings-grid">
"""
    
    # Add groups tables
    for g_code in sorted(standings.keys()):
        html_content += f"""            <div class="group-card">
                <div class="group-title">Group {g_code}</div>
                <table class="standings-table">
                    <thead>
                        <tr>
                            <th>Pos</th>
                            <th style="text-align: left;">Team</th>
                            <th>MP</th>
                            <th>W</th>
                            <th>D</th>
                            <th>L</th>
                            <th>GF</th>
                            <th>GA</th>
                            <th>Pts</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        for idx, t in enumerate(standings[g_code]):
            qual_class = ""
            if idx < 2:
                qual_class = 'class="qualify-direct"'
            elif t["team"] in [x["team"] for x in ranked_thirds[:8]]:
                qual_class = 'class="qualify-3rd"'
                
            html_content += f"""                        <tr {qual_class}>
                            <td>{idx+1}</td>
                            <td class="team-name">{t['team']}</td>
                            <td>{t['mp']}</td>
                            <td>{t['w']}</td>
                            <td>{t['d']}</td>
                            <td>{t['l']}</td>
                            <td>{t['gf']}</td>
                            <td>{t['ga']}</td>
                            <td style="font-weight: 700;">{t['pts']}</td>
                        </tr>
"""
        html_content += """                    </tbody>
                </table>
            </div>
"""
        
    html_content += """        </div>
        
        <!-- Best 3rd place -->
        <div class="thirds-card">
            <div class="group-title">Best Third-Placed Teams Rankings</div>
            <table class="standings-table" style="font-size: 0.85rem;">
                <thead>
                    <tr>
                        <th>Pos</th>
                        <th style="text-align: left;">Team</th>
                        <th>Group</th>
                        <th>MP</th>
                        <th>W</th>
                        <th>D</th>
                        <th>L</th>
                        <th>GF</th>
                        <th>GA</th>
                        <th>GD</th>
                        <th>Pts</th>
                    </tr>
                </thead>
                <tbody>
"""
    for idx, t in enumerate(ranked_thirds):
        qual_class = ""
        qual_marker = "❌"
        if idx < 8:
            qual_class = 'class="qualify-3rd"'
            qual_marker = "✅"
            
        html_content += f"""                    <tr {qual_class}>
                        <td style="font-weight: 700;">{idx+1} {qual_marker}</td>
                        <td class="team-name">{t['team']}</td>
                        <td>{t['group']}</td>
                        <td>{t['mp']}</td>
                        <td>{t['w']}</td>
                        <td>{t['d']}</td>
                        <td>{t['l']}</td>
                        <td>{t['gf']}</td>
                        <td>{t['ga']}</td>
                        <td>{t['gd']}</td>
                        <td style="font-weight: 700;">{t['pts']}</td>
                    </tr>
"""
        
    html_content += """                </tbody>
            </table>
        </div>
    </div>
    
    <!-- Visual Bracket Section -->
    <div class="section-header">
        <h2>Knockout Bracket</h2>
    </div>
    
    <div class="bracket-container">
"""
    
    # Bracket Columns configuration
    stages_order = [
        ("Round of 32", 73, 89),
        ("Round of 16", 89, 97),
        ("Quarterfinals", 97, 101),
        ("Semifinals", 101, 103),
        ("Finals", 103, 105)
    ]
    
    ko_matches_map = {m["match_num"]: m for m in matches if m["stage"] != "group"}
    
    for stage_title, start_id, end_id in stages_order:
        html_content += f"""        <div class="bracket-column">
            <h4>{stage_title}</h4>
"""
        # If it is finals, we render third place and final separately or list them
        if stage_title == "Finals":
            # Render Third Place
            m3rd = ko_matches_map.get(103)
            if m3rd:
                t1 = m3rd.get("team1") or m3rd.get("team1_placeholder")
                t2 = m3rd.get("team2") or m3rd.get("team2_placeholder")
                s1 = m3rd.get("score1", "") if m3rd.get("is_played") else ""
                s2 = m3rd.get("score2", "") if m3rd.get("is_played") else ""
                t1_class = "winner" if m3rd.get("is_played") and (s1 > s2 or m3rd.get("pen_winner") == t1) else ""
                t2_class = "winner" if m3rd.get("is_played") and (s2 > s1 or m3rd.get("pen_winner") == t2) else ""
                pen_text = f" ({m3rd['pen_score']} pens)" if m3rd.get("is_played") and m3rd.get("pen_winner") else ""
                html_content += f"""            <div style="font-size: 0.65rem; color: var(--text-muted); text-align: center; margin-top: 20px;">Third Place Playoff</div>
            <div class="bracket-match">
                <div class="bracket-match-header">
                    <span>Match 103</span>
                    <span>3rd Place</span>
                </div>
                <div class="bracket-match-team {t1_class}">
                    <span>{t1}</span>
                    <span class="bracket-match-score">{s1}</span>
                </div>
                <div class="bracket-match-team {t2_class}">
                    <span>{t2}</span>
                    <span class="bracket-match-score">{s2}</span>
                </div>
                <div style="font-size: 0.6rem; text-align: right; color: var(--text-muted); margin-top: 3px;">
                    {pen_text if pen_text else ('Played' if m3rd.get('is_played') else 'Upcoming')}
                </div>
            </div>
"""
            # Render Final
            m_fin = ko_matches_map.get(104)
            if m_fin:
                t1 = m_fin.get("team1") or m_fin.get("team1_placeholder")
                t2 = m_fin.get("team2") or m_fin.get("team2_placeholder")
                s1 = m_fin.get("score1", "") if m_fin.get("is_played") else ""
                s2 = m_fin.get("score2", "") if m_fin.get("is_played") else ""
                t1_class = "winner" if m_fin.get("is_played") and (s1 > s2 or m_fin.get("pen_winner") == t1) else ""
                t2_class = "winner" if m_fin.get("is_played") and (s2 > s1 or m_fin.get("pen_winner") == t2) else ""
                pen_text = f" ({m_fin['pen_score']} pens)" if m_fin.get("is_played") and m_fin.get("pen_winner") else ""
                html_content += f"""            <div style="font-size: 0.65rem; color: var(--warning); text-align: center; margin-top: 30px; font-weight: 700;">Championship Final</div>
            <div class="bracket-match" style="border-color: rgba(245, 158, 11, 0.3);">
                <div class="bracket-match-header">
                    <span style="color: var(--warning);">Match 104</span>
                    <span>Final</span>
                </div>
                <div class="bracket-match-team {t1_class}">
                    <span>{t1}</span>
                    <span class="bracket-match-score">{s1}</span>
                </div>
                <div class="bracket-match-team {t2_class}">
                    <span>{t2}</span>
                    <span class="bracket-match-score">{s2}</span>
                </div>
                <div style="font-size: 0.6rem; text-align: right; color: var(--warning); margin-top: 3px;">
                    {pen_text if pen_text else ('Completed' if m_fin.get('is_played') else 'Upcoming')}
                </div>
            </div>
"""
        else:
            for num in range(start_id, end_id):
                m = ko_matches_map.get(num)
                if not m:
                    continue
                t1 = m.get("team1") or m.get("team1_placeholder")
                t2 = m.get("team2") or m.get("team2_placeholder")
                s1 = m.get("score1", "") if m.get("is_played") else ""
                s2 = m.get("score2", "") if m.get("is_played") else ""
                t1_class = "winner" if m.get("is_played") and (s1 > s2 or m.get("pen_winner") == t1) else ""
                t2_class = "winner" if m.get("is_played") and (s2 > s1 or m.get("pen_winner") == t2) else ""
                pen_text = f" ({m['pen_score']} pens)" if m.get("is_played") and m.get("pen_winner") else ""
                stage_label = m["stage"].replace("KO_", "").replace("R32", "R32").replace("R16", "R16")
                html_content += f"""            <div class="bracket-match">
                <div class="bracket-match-header">
                    <span>Match {num}</span>
                    <span>{stage_label}</span>
                </div>
                <div class="bracket-match-team {t1_class}">
                    <span>{t1}</span>
                    <span class="bracket-match-score">{s1}</span>
                </div>
                <div class="bracket-match-team {t2_class}">
                    <span>{t2}</span>
                    <span class="bracket-match-score">{s2}</span>
                </div>
            </div>
"""
        html_content += """        </div>
"""
        
    html_content += """    </div>
    
    <!-- Matches Section -->
    <div class="section-header">
        <h2>Match Schedule & Analysis</h2>
    </div>
    
    <div id="matches-container" class="matches-list">
"""
    
    # Add matches list
    for idx, m in enumerate(matches):
        m_id = m["id"]
        stage = m["stage"]
        is_played = m.get("is_played", False)
        
        t1 = m.get("team1") or m.get("team1_placeholder")
        t2 = m.get("team2") or m.get("team2_placeholder")
        
        stage_label = stage.replace("KO_", "Round of ").replace("R32", "32").replace("R16", "16").replace("QF", "Quarterfinals").replace("SF", "Semifinals").replace("3RD", "3rd Place Match").replace("FINAL", "Final").capitalize()
        if stage == "group":
            stage_label = f"Group {m.get('group')} Match"
            
        score_display = ""
        status_text = "Upcoming"
        status_class = "upcoming"
        if is_played:
            status_text = "Simulation Resolved"
            status_class = ""
            s1, s2 = m["score1"], m["score2"]
            score_display = f"{s1} - {s2}"
            if m.get("pen_winner"):
                score_display += f" ({m['pen_score']} pens)"
        else:
            score_display = "vs"
            
        cot_text = m.get("prediction_text", "No detailed analysis available.")
        prompt_text = m.get("prompt_text", "No prompt data available.")
        
        html_content += f"""        <div class="match-row" data-stage="{stage}" data-team1="{t1.lower()}" data-team2="{t2.lower()}">
            <div class="match-summary chevron" onclick="toggleMatchDetails({m_id})">
                <span class="match-num">Match {m_id}</span>
                <span class="match-stage-label">{stage_label}</span>
                <div class="match-teams-score">
                    <div class="team-col team1">
                        <span>{t1}</span>
                    </div>
                    <span class="score-box">{score_display}</span>
                    <div class="team-col team2">
                        <span>{t2}</span>
                    </div>
                </div>
                <span class="match-status-pill {status_class}">{status_text}</span>
            </div>
            
            <div id="match-details-{m_id}" class="match-details">
                <div class="tabs-header">
                    <button class="tab-link active" onclick="switchTab({m_id}, 'cot', this)">Specialist Analysis</button>
                    <button class="tab-link" onclick="switchTab({m_id}, 'prompt', this)">Gemini Prompt</button>
                </div>
                
                <div id="tab-cot-{m_id}" class="tab-content active">
{cot_text}
                </div>
                
                <div id="tab-prompt-{m_id}" class="tab-content" style="font-family: monospace; font-size: 0.75rem; white-space: pre-wrap;">
{prompt_text}
                </div>
            </div>
        </div>
"""
        
    html_content += """    </div>
</div>

<script>
    // Toggle overall sections
    function toggleSection(sectionId, btn) {
        var section = document.getElementById(sectionId);
        if (section.style.display === "none") {
            section.style.display = "block";
            btn.classList.add("active");
            btn.textContent = btn.textContent.replace("Show", "Hide");
        } else {
            section.style.display = "none";
            btn.classList.remove("active");
            btn.textContent = btn.textContent.replace("Hide", "Show");
        }
    }
    
    // Toggle group stage matches visibility
    var showGroupStage = true;
    function toggleGroupResults(btn) {
        showGroupStage = !showGroupStage;
        if (showGroupStage) {
            btn.classList.add("active");
            btn.textContent = "⚽ Show Group Stage Matches";
        } else {
            btn.classList.remove("active");
            btn.textContent = "⚽ Hide Group Stage Matches";
        }
        filterMatches();
    }
    
    // Toggle accordion details
    function toggleMatchDetails(matchId) {
        var details = document.getElementById("match-details-" + matchId);
        var row = details.parentElement;
        if (details.style.display === "block") {
            details.style.display = "none";
            row.classList.remove("open");
        } else {
            details.style.display = "block";
            row.classList.add("open");
        }
    }
    
    // Switch between Specialist Analysis and Prompt tabs
    function switchTab(matchId, tabType, btn) {
        // Deactivate all tab links in this match card
        var row = document.getElementById("match-details-" + matchId);
        var links = row.getElementsByClassName("tab-link");
        for (var i = 0; i < links.length; i++) {
            links[i].classList.remove("active");
        }
        btn.classList.add("active");
        
        // Hide all tab contents in this match card
        var contents = row.getElementsByClassName("tab-content");
        for (var i = 0; i < contents.length; i++) {
            contents[i].classList.remove("active");
        }
        
        document.getElementById("tab-" + tabType + "-" + matchId).classList.add("active");
    }
    
    // Filter matches list based on toolbar search & stage selection
    function filterMatches() {
        var query = document.getElementById("team-search").value.toLowerCase();
        var selectedStage = document.getElementById("stage-filter").value;
        var matchRows = document.getElementsByClassName("match-row");
        
        for (var i = 0; i < matchRows.length; i++) {
            var row = matchRows[i];
            var mStage = row.getAttribute("data-stage");
            var t1 = row.getAttribute("data-team1");
            var t2 = row.getAttribute("data-team2");
            
            var matchesSearch = t1.includes(query) || t2.includes(query);
            var matchesStage = (selectedStage === "all") || (mStage === selectedStage);
            
            // Handle group stage visibility toggle
            var isGroupStageMatch = (mStage === "group");
            var passesGroupToggle = !isGroupStageMatch || showGroupStage;
            
            if (matchesSearch && matchesStage && passesGroupToggle) {
                row.style.display = "block";
            } else {
                row.style.display = "none";
            }
        }
    }
    
    // Set initial text on toggle-standings button
    document.getElementById("toggle-standings").textContent = "📁 Hide Standings";
</script>

</body>
</html>
"""
    
    output_file = "results.html"
    with open(output_file, "w") as f:
        f.write(html_content)
        
    print(f"Interactive HTML Report generated successfully at {output_file}!")

if __name__ == "__main__":
    main()
