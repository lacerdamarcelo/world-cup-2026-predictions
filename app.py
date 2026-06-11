import json
import os
import yaml
import dash
from dash import dcc, html, Input, Output, State, ALL
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px

# Import local modules
from tournament_rules import resolve_knockout_bracket
from prediction_engine import build_prompt

# Initialize Dash App
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.DARKLY,
        "https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Inter:wght@300;400;600;700&display=swap"
    ],
    suppress_callback_exceptions=True,
    title="FIFA World Cup 2026 Prediction Dashboard"
)

# File paths
GROUPS_FILE = "groups.yaml"
MATCHES_FILE = "matches.yaml"
PREDICTIONS_FILE = "predictions.json"
STATE_FILE = "tournament_state.json"

# Helper to load state
def load_tournament_state():
    state = {"standings": {}, "ranked_thirds": [], "matches": []}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
        except Exception as e:
            print(f"Error reading state file: {e}")
            
    # Enrich matches with prediction_text and prompt_text from predictions.json
    if state.get("matches") and os.path.exists(PREDICTIONS_FILE):
        try:
            with open(PREDICTIONS_FILE, "r") as f:
                predictions = json.load(f)
            for m in state["matches"]:
                m_id = str(m["id"])
                if m_id in predictions:
                    m["prediction_text"] = predictions[m_id].get("prediction_text")
                    m["prompt_text"] = predictions[m_id].get("prompt_text")
        except Exception as e:
            print(f"Error enriching matches in load_tournament_state: {e}")
            
    if not state.get("matches") and os.path.exists(GROUPS_FILE) and os.path.exists(MATCHES_FILE):
        # Fallback to in-memory generation if state file not available/complete
        try:
            with open(GROUPS_FILE, "r") as f:
                groups = yaml.safe_load(f)
            with open(MATCHES_FILE, "r") as f:
                matches = yaml.safe_load(f)
            
            predictions = {}
            if os.path.exists(PREDICTIONS_FILE):
                with open(PREDICTIONS_FILE, "r") as f:
                    predictions = json.load(f)
                    
            standings, ranked_thirds, resolved_matches = resolve_knockout_bracket(matches, predictions, groups)
            state = {
                "standings": standings,
                "ranked_thirds": ranked_thirds,
                "matches": resolved_matches
            }
        except Exception as e:
            print(f"Error generating fallback state: {e}")
            
    return state

# Main Layout
app.layout = dbc.Container(
    [
        # Store for active selections
        dcc.Store(id="predictions-store"),
        
        # Header Row
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.H1(
                                    [
                                        html.Span("FIFA ", style={"color": "#fff", "fontWeight": "800"}),
                                        html.Span("WORLD CUP ", style={"color": "#0ea5e9", "fontWeight": "800"}),
                                        html.Span("2026", style={"color": "#00ff87", "fontWeight": "800"})
                                    ],
                                    className="text-center my-3 neon-glow-cyan",
                                    style={"letterSpacing": "2px"}
                                ),
                                html.P(
                                    "Gemini 3.1 Pro Statistical Predictor Dashboard",
                                    className="text-center text-muted",
                                    style={"fontSize": "1.1rem"}
                                )
                            ]
                        )
                    ],
                    width=12
                )
            ],
            className="mb-4"
        ),
        
        # Dashboard Overview Panel
        dbc.Row(
            [
                dbc.Col(
                    dbc.Button(
                        "🔄 Refresh Live Data",
                        id="refresh-btn",
                        color="info",
                        size="md",
                        className="w-100 shadow-sm font-weight-bold"
                    ),
                    xs=12, sm=6, md=3, className="mb-2"
                ),
                dbc.Col(
                    dbc.Button(
                        "📋 Preview Next Match Prompt",
                        id="preview-prompt-btn",
                        color="warning",
                        size="md",
                        className="w-100 shadow-sm font-weight-bold"
                    ),
                    xs=12, sm=6, md=3, className="mb-2"
                ),
                dbc.Col(
                    html.Div(id="summary-stats-container"),
                    xs=12, md=6, className="mb-2"
                )
            ],
            className="align-items-center mb-4"
        ),
        
        # Navigation Tabs
        dbc.Tabs(
            [
                dbc.Tab(label="🏆 Knockout Bracket", tab_id="tab-bracket"),
                dbc.Tab(label="📊 Group Standings", tab_id="tab-groups"),
                dbc.Tab(label="⚽ All Matches & Predictions", tab_id="tab-matches")
            ],
            id="tabs-main",
            active_tab="tab-bracket",
            className="mb-4"
        ),
        
        # Dynamic Content Container
        html.Div(id="tab-content-container"),
        
        # Interval components for live updates
        dcc.Interval(
            id="interval-component",
            interval=10 * 1000, # 10 seconds
            n_intervals=0
        ),
        
        # Prediction Detail Modal
        dbc.Modal(
            [
                dbc.ModalHeader(
                    dbc.ModalTitle(id="modal-match-title", className="font-weight-bold"),
                    close_button=True
                ),
                dbc.ModalBody(
                    [
                        html.Div(
                            [
                                html.Span("STAGE: ", style={"color": "#94a3b8", "fontWeight": "600"}),
                                html.Span(id="modal-match-stage", style={"color": "#0ea5e9", "fontWeight": "600"})
                            ],
                            className="mb-2"
                        ),
                        html.Div(
                            id="modal-match-score",
                            className="text-center my-4 py-3",
                            style={
                                "fontSize": "2.2rem",
                                "fontWeight": "800",
                                "background": "rgba(30, 41, 59, 0.4)",
                                "borderRadius": "12px",
                                "border": "1px solid rgba(255, 255, 255, 0.05)"
                            }
                        ),
                        dbc.Tabs(
                            [
                                dbc.Tab(
                                    label="🧠 Specialist Prediction",
                                    tab_id="modal-tab-cot",
                                    children=html.Div(
                                        id="modal-match-cot",
                                        style={
                                            "maxHeight": "400px",
                                            "overflowY": "auto",
                                            "padding": "15px",
                                            "background": "#090d16",
                                            "borderRadius": "0 0 10px 10px",
                                            "border": "1px solid rgba(255, 255, 255, 0.05)",
                                            "borderTop": "none",
                                            "fontSize": "0.95rem",
                                            "lineHeight": "1.6"
                                        }
                                    )
                                ),
                                dbc.Tab(
                                    label="📋 Gemini Prompt",
                                    tab_id="modal-tab-prompt",
                                    children=html.Div(
                                        id="modal-match-prompt",
                                        style={
                                            "maxHeight": "400px",
                                            "overflowY": "auto",
                                            "padding": "15px",
                                            "background": "#090d16",
                                            "borderRadius": "0 0 10px 10px",
                                            "border": "1px solid rgba(255, 255, 255, 0.05)",
                                            "borderTop": "none",
                                            "fontSize": "0.90rem",
                                            "lineHeight": "1.5",
                                            "fontFamily": "monospace",
                                            "whiteSpace": "pre-wrap"
                                        }
                                    )
                                )
                            ],
                            id="modal-tabs",
                            active_tab="modal-tab-cot",
                            className="mb-2"
                        )
                    ]
                ),
                dbc.ModalFooter(
                    dbc.Button("Close", id="close-modal-btn", className="ml-auto", color="secondary")
                )
            ],
            id="match-modal",
            size="lg",
            centered=True,
            className="custom-modal"
        )
    ],
    fluid=True,
    className="py-4 px-md-5"
)

# Callback to switch Tabs and render content
@app.callback(
    Output("tab-content-container", "children"),
    Input("tabs-main", "active_tab"),
    Input("predictions-store", "data")
)
def render_tab_content(active_tab, state_data):
    # Load state data
    state = load_tournament_state()
    matches = state.get("matches", [])
    standings = state.get("standings", {})
    ranked_thirds = state.get("ranked_thirds", [])
    
    if active_tab == "tab-groups":
        # Group Standings Tab Layout
        group_cards = []
        for g_letter in sorted(standings.keys()):
            g_standings = standings[g_letter]
            
            rows = []
            for idx, t in enumerate(g_standings):
                # Highlights for qualified/3rd/eliminated
                row_class = ""
                if idx < 2:
                    row_class = "qualify-direct"
                elif idx == 2:
                    # Check if qualified as 3rd place
                    is_qual = any(rt["team"] == t["team"] for rt in ranked_thirds[:8])
                    row_class = "qualify-3rd" if is_qual else ""
                    
                rows.append(
                    html.Tr(
                        [
                            html.Td(f"{idx+1}", style={"fontWeight": "600"}),
                            html.Td(t["team"], style={"textAlign": "left", "fontWeight": "600" if idx < 2 else "400"}),
                            html.Td(t["mp"]),
                            html.Td(t["w"]),
                            html.Td(t["d"]),
                            html.Td(t["l"]),
                            html.Td(t["gf"]),
                            html.Td(t["ga"]),
                            html.Td(t["gd"]),
                            html.Td(t["pts"], style={"fontWeight": "700", "color": "#0ea5e9" if idx < 2 else "#e2e8f0"})
                        ],
                        className=row_class
                    )
                )
                
            group_cards.append(
                dbc.Col(
                    html.Div(
                        [
                            html.H5(f"Group {g_letter}", className="text-center p-2 text-info", style={"borderBottom": "1px solid rgba(255, 255, 255, 0.08)", "fontWeight": "700"}),
                            html.Table(
                                [
                                    html.Thead(
                                        html.Tr(
                                            [
                                                html.Th("Pos"), html.Th("Team", style={"textAlign": "left"}), 
                                                html.Th("MP"), html.Th("W"), html.Th("D"), html.Th("L"), 
                                                html.Th("GF"), html.Th("GA"), html.Th("GD"), html.Th("Pts")
                                            ]
                                        )
                                    ),
                                    html.Tbody(rows)
                                ],
                                className="standings-table"
                            )
                        ],
                        className="glass-card p-3 h-100"
                    ),
                    xs=12, md=6, xl=4, className="mb-4"
                )
            )
            
        # Third Place Standings Table
        third_place_rows = []
        for idx, t in enumerate(ranked_thirds):
            is_qual = idx < 8
            row_class = "qualify-3rd" if is_qual else ""
            indicator = "✅" if is_qual else "❌"
            third_place_rows.append(
                html.Tr(
                    [
                        html.Td(f"{idx+1} {indicator}", style={"fontWeight": "600"}),
                        html.Td(t["team"], style={"textAlign": "left", "fontWeight": "600" if is_qual else "400"}),
                        html.Td(t["group"]),
                        html.Td(t["mp"]),
                        html.Td(t["w"]),
                        html.Td(t["d"]),
                        html.Td(t["l"]),
                        html.Td(t["gf"]),
                        html.Td(t["ga"]),
                        html.Td(t["gd"]),
                        html.Td(t["pts"], style={"fontWeight": "700", "color": "#00ff87" if is_qual else "#e2e8f0"})
                    ],
                    className=row_class
                )
            )
            
        third_place_table_card = dbc.Row(
            dbc.Col(
                html.Div(
                    [
                        html.H4("Best Third-Placed Teams Standings", className="text-center mb-3 text-info", style={"fontWeight": "700"}),
                        html.P("Top 8 third-placed teams qualify for the Round of 32.", className="text-center text-muted mb-3"),
                        html.Table(
                            [
                                html.Thead(
                                    html.Tr(
                                        [
                                            html.Th("Rank"), html.Th("Team", style={"textAlign": "left"}), html.Th("Group"),
                                            html.Th("MP"), html.Th("W"), html.Th("D"), html.Th("L"), 
                                            html.Th("GF"), html.Th("GA"), html.Th("GD"), html.Th("Pts")
                                        ]
                                    )
                                ),
                                html.Tbody(third_place_rows)
                            ],
                            className="standings-table"
                        )
                    ],
                    className="glass-card p-4 mb-4"
                ),
                width=12
            )
        )
        
        return html.Div(
            [
                third_place_table_card,
                html.H3("Group Stage Standings", className="mb-4 text-center text-light", style={"fontWeight": "700"}),
                dbc.Row(group_cards)
            ]
        )
        
    elif active_tab == "tab-matches":
        # All Matches list layout
        match_rows = []
        for m in matches:
            m_id = m["id"]
            stage_clean = m["stage"].replace("KO_", "Round of ").replace("R32", "32").replace("R16", "16").replace("QF", "Quarterfinals").replace("SF", "Semifinals").replace("3RD", "3rd Place Match").replace("FINAL", "Final").capitalize()
            
            t1 = m.get("team1") or m.get("team1_placeholder")
            t2 = m.get("team2") or m.get("team2_placeholder")
            
            score_text = "Upcoming"
            if m.get("is_played", False):
                score_text = f"{m['score1']} - {m['score2']}"
                if m.get("pen_winner"):
                    score_text += f" ({m['pen_score']} pens)"
            
            # Format row
            # If match has reasoning details, show a details button
            if m.get("is_played", False):
                details_btn = dbc.Button(
                    "Read Prediction",
                    id={"type": "list-match-btn", "index": m_id},
                    size="sm",
                    color="success"
                )
            else:
                # Check if resolved
                placeholders_keywords = ["Group", "Winner", "Loser", "Match", "3rd"]
                t1_is_placeholder = any(kw in str(t1) for kw in placeholders_keywords) if t1 else True
                t2_is_placeholder = any(kw in str(t2) for kw in placeholders_keywords) if t2 else True
                
                if t1_is_placeholder or t2_is_placeholder:
                    details_btn = dbc.Button(
                        "Upcoming",
                        id={"type": "list-match-btn", "index": m_id},
                        size="sm",
                        color="secondary",
                        outline=True
                    )
                else:
                    details_btn = dbc.Button(
                        "Preview Prompt",
                        id={"type": "list-match-btn", "index": m_id},
                        size="sm",
                        color="warning",
                        outline=True
                    )
            
            match_rows.append(
                html.Tr(
                    [
                        html.Td(f"{m_id}", style={"fontWeight": "600"}),
                        html.Td(stage_clean),
                        html.Td(m.get("group", "-")),
                        html.Td(t1, style={"textAlign": "right", "fontWeight": "600" if m.get("is_played") and m.get("score1", 0) > m.get("score2", 0) else "400"}),
                        html.Td(score_text, style={"fontWeight": "700", "color": "#0ea5e9" if m.get("is_played") else "#94a3b8"}),
                        html.Td(t2, style={"textAlign": "left", "fontWeight": "600" if m.get("is_played") and m.get("score2", 0) > m.get("score1", 0) else "400"}),
                        html.Td(details_btn)
                    ]
                )
            )
            
        return html.Div(
            [
                html.H3("Full Tournament Schedule", className="mb-4 text-center text-light", style={"fontWeight": "700"}),
                html.Div(
                    [
                        html.Table(
                            [
                                html.Thead(
                                    html.Tr(
                                        [
                                            html.Th("Match ID"), html.Th("Stage"), html.Th("Group"), 
                                            html.Th("Team 1", style={"textAlign": "right"}), html.Th("Score"), 
                                            html.Th("Team 2", style={"textAlign": "left"}), html.Th("Details")
                                        ]
                                    )
                                ),
                                html.Tbody(match_rows)
                            ],
                            className="standings-table"
                        )
                    ],
                    className="glass-card p-4"
                )
            ]
        )
        
    else:
        # Default: Knockout Bracket View
        # Separate matches by stage
        ko_matches = [m for m in matches if m["stage"] != "group"]
        
        # Maps matching IDs
        m_map = {m["match_num"]: m for m in ko_matches}
        
        def render_match_node(match_num):
            m = m_map.get(match_num)
            if not m:
                return html.Div("Loading...", className="match-card")
                
            m_id = m["id"]
            stage_name = m["stage"].replace("KO_", "").replace("R32", "R32").replace("R16", "R16")
            
            t1 = m.get("team1") or m.get("team1_placeholder")
            t2 = m.get("team2") or m.get("team2_placeholder")
            
            s1 = m.get("score1", "") if m.get("is_played") else ""
            s2 = m.get("score2", "") if m.get("is_played") else ""
            
            t1_win = m.get("is_played") and (s1 > s2 or m.get("pen_winner") == t1)
            t2_win = m.get("is_played") and (s2 > s1 or m.get("pen_winner") == t2)
            
            pen_text = ""
            if m.get("is_played") and m.get("pen_winner"):
                pen_text = f" ({m['pen_score']} pens)"
                
            return html.Div(
                [
                    html.Div(
                        [
                            html.Span(f"Match {match_num}"),
                            html.Span(stage_name, style={"color": "#38bdf8"})
                        ],
                        className="match-card-header"
                    ),
                    html.Div(
                        [
                            html.Span(t1, style={"textOverflow": "ellipsis", "overflow": "hidden", "whiteSpace": "nowrap", "maxWidth": "150px"}),
                            html.Span(s1, className="match-card-score")
                        ],
                        className=f"match-card-team {'winner neon-glow-green' if t1_win else ''}"
                    ),
                    html.Div(
                        [
                            html.Span(t2, style={"textOverflow": "ellipsis", "overflow": "hidden", "whiteSpace": "nowrap", "maxWidth": "150px"}),
                            html.Span(s2, className="match-card-score")
                        ],
                        className=f"match-card-team {'winner neon-glow-green' if t2_win else ''}"
                    ),
                    html.Div(
                        f"Predicted Result{pen_text}" if m.get("is_played") else "Upcoming Match",
                        className="match-card-footer"
                    )
                ],
                id={"type": "match-card", "index": m_id},
                className="match-card"
            )
            
        # Bracket column structures
        # Left-to-right flow
        # Round of 32: 16 matches (73 to 88)
        col_r32 = html.Div(
            [html.H5("Round of 32", className="text-center text-muted mb-3", style={"fontWeight": "600"})] + 
            [render_match_node(num) for num in range(73, 89)],
            className="bracket-column"
        )
        
        # Round of 16: 8 matches (89 to 96)
        col_r16 = html.Div(
            [html.H5("Round of 16", className="text-center text-muted mb-3", style={"fontWeight": "600"})] + 
            [render_match_node(num) for num in range(89, 97)],
            className="bracket-column"
        )
        
        # Quarterfinals: 4 matches (97 to 100)
        col_qf = html.Div(
            [html.H5("Quarterfinals", className="text-center text-muted mb-3", style={"fontWeight": "600"})] + 
            [render_match_node(num) for num in range(97, 101)],
            className="bracket-column"
        )
        
        # Semifinals: 2 matches (101 to 102)
        col_sf = html.Div(
            [html.H5("Semifinals", className="text-center text-muted mb-3", style={"fontWeight": "600"})] + 
            [render_match_node(num) for num in range(101, 103)],
            className="bracket-column"
        )
        
        # Final & 3rd Place Match: Matches 103 and 104
        col_finals = html.Div(
            [
                html.H5("Finals", className="text-center text-muted mb-3", style={"fontWeight": "600"}),
                html.Div([
                    html.Div("Third Place Playoff", className="text-center text-muted mb-2", style={"fontSize": "0.75rem", "fontWeight": "700"}),
                    render_match_node(103)
                ], style={"margin-top": "100px", "border": "1px dashed rgba(255, 255, 255, 0.08)", "borderRadius": "12px", "padding": "5px"}),
                html.Div([
                    html.Div("🏆 Championship Final 🏆", className="text-center text-warning mb-2 neon-glow-gold", style={"fontSize": "0.85rem", "fontWeight": "800"}),
                    render_match_node(104)
                ], style={"margin-top": "150px", "border": "2px solid rgba(255, 215, 0, 0.2)", "borderRadius": "16px", "padding": "8px", "background": "rgba(251, 191, 36, 0.02)"})
            ],
            className="bracket-column"
        )
        
        return html.Div(
            [
                html.P("Click on any match card to view Gemini's step-by-step reasoning and prediction analysis.", className="text-center text-muted"),
                html.Div(
                    [col_r32, col_r16, col_qf, col_sf, col_finals],
                    className="bracket-container glass-card"
                )
            ]
        )

# Callback to load and update state (triggered by interval or manual refresh)
@app.callback(
    Output("predictions-store", "data"),
    Output("summary-stats-container", "children"),
    Input("refresh-btn", "n_clicks"),
    Input("interval-component", "n_intervals")
)
def update_store(n_clicks, n_intervals):
    state = load_tournament_state()
    matches = state.get("matches", [])
    
    # Calculate stats
    total_played = sum(1 for m in matches if m.get("is_played", False))
    total_goals = sum(m.get("score1", 0) + m.get("score2", 0) for m in matches if m.get("is_played", False))
    
    # Find current champion
    champ_text = "Undetermined"
    final_match = next((m for m in matches if m.get("match_num") == 104), None)
    if final_match and final_match.get("is_played", False):
        s1, s2 = final_match["score1"], final_match["score2"]
        if s1 > s2:
            champ_text = final_match["team1"]
        elif s2 > s1:
            champ_text = final_match["team2"]
        else:
            champ_text = final_match.get("pen_winner")
            
    stats_row = dbc.Row(
        [
            dbc.Col(
                html.Div(
                    [
                        html.Small("Tournament Progress", className="text-muted"),
                        html.H3(f"{total_played} / 104 Matches", className="text-info font-weight-bold")
                    ],
                    className="glass-card p-2 text-center"
                ),
                width=4
            ),
            dbc.Col(
                html.Div(
                    [
                        html.Small("Total Goals Scored", className="text-muted"),
                        html.H3(f"{total_goals} Goals", className="text-success font-weight-bold")
                    ],
                    className="glass-card p-2 text-center"
                ),
                width=4
            ),
            dbc.Col(
                html.Div(
                    [
                        html.Small("Predicted Champion", className="text-muted"),
                        html.H3(champ_text, className="text-warning font-weight-bold neon-glow-gold")
                    ],
                    className="glass-card p-2 text-center"
                ),
                width=4
            )
        ]
    )
    
    return state, stats_row

# Callback to open/close modal and fill content
@app.callback(
    Output("match-modal", "is_open"),
    Output("modal-match-title", "children"),
    Output("modal-match-stage", "children"),
    Output("modal-match-score", "children"),
    Output("modal-match-cot", "children"),
    Output("modal-match-prompt", "children"),
    Input({"type": "match-card", "index": ALL}, "n_clicks"),
    Input({"type": "list-match-btn", "index": ALL}, "n_clicks"),
    Input("preview-prompt-btn", "n_clicks"),
    Input("close-modal-btn", "n_clicks"),
    State("match-modal", "is_open"),
    State("predictions-store", "data"),
    prevent_initial_call=True
)
def handle_modal(card_clicks, btn_clicks, preview_clicks, close_click, is_open, state_data):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
        
    trig = ctx.triggered[0]
    trig_id = trig["prop_id"].split(".")[0]
    trig_val = trig.get("value")
    
    # Ignore initial mounts, background updates, and interval triggers
    if trig_val is None or trig_val == 0:
        raise dash.exceptions.PreventUpdate
        
    # If close button clicked
    if "close-modal-btn" in trig_id:
        return False, "", "", "", "", ""
        
    # Find match ID based on what was clicked
    match_id = None
    
    if "preview-prompt-btn" in trig_id:
        # Find next unplayed, resolved match
        if not state_data:
            return is_open, "", "", "", "", ""
        matches = state_data.get("matches", [])
        
        # Find the first match after the highest predicted match ID that is resolved
        played_ids = [int(m["id"]) for m in matches if m.get("is_played", False)]
        max_played_id = max(played_ids) if played_ids else 0
        
        for m in matches:
            if int(m["id"]) > max_played_id:
                t1 = m.get("team1") or m.get("team1_placeholder")
                t2 = m.get("team2") or m.get("team2_placeholder")
                placeholders_keywords = ["Group", "Winner", "Loser", "Match", "3rd"]
                t1_is_placeholder = any(kw in str(t1) for kw in placeholders_keywords) if t1 else True
                t2_is_placeholder = any(kw in str(t2) for kw in placeholders_keywords) if t2 else True
                if not t1_is_placeholder and not t2_is_placeholder:
                    match_id = m["id"]
                    break
        
        if not match_id:
            return True, "No Match to Preview", "All Matches Complete or Awaiting Standings", "", dcc.Markdown("All matches have already been predicted or there is no next match ready to be predicted yet."), ""
            
    else:
        try:
            # Check if the trigger contains JSON structure (match-card or list-match-btn)
            trig_json = json.loads(trig_id)
            match_id = trig_json.get("index")
        except Exception:
            return is_open, "", "", "", "", ""
            
    if not match_id or not state_data:
        return is_open, "", "", "", "", ""
        
    # Retrieve match information
    matches = state_data.get("matches", [])
    m = next((item for item in matches if item["id"] == match_id), None)
    
    if not m:
        return is_open, "", "", "", "", ""
        
    # Format details
    stage_clean = m["stage"].replace("KO_", "Round of ").replace("R32", "32").replace("R16", "16").replace("QF", "Quarterfinals").replace("SF", "Semifinals").replace("3RD", "3rd Place Match").replace("FINAL", "Final").capitalize()
    
    t1 = m.get("team1") or m.get("team1_placeholder")
    t2 = m.get("team2") or m.get("team2_placeholder")
    
    title = f"{t1} vs {t2}"
    
    if m.get("is_played", False):
        s1, s2 = m["score1"], m["score2"]
        score_display = f"{s1} - {s2}"
        if m.get("pen_winner"):
            score_display += f" ({m['pen_score']} pens)"
            
        cot_raw = m.get("prediction_text", "No detailed analysis available.")
        cot_formatted = dcc.Markdown(cot_raw)
        
        prompt_raw = m.get("prompt_text", "No prompt data available.")
    else:
        score_display = "Upcoming Match"
        
        cot_formatted = dcc.Markdown(
            f"ℹ️ **Upcoming Match**\n\n"
            f"This match has not been predicted yet. The prediction will be simulated chronologically "
            f"by the Gemini engine. \n\n"
            f"Run `make predict-next` or `make predict-all` in the terminal to simulate this and subsequent fixtures."
        )
        
        # Build prompt dynamically
        placeholders_keywords = ["Group", "Winner", "Loser", "Match", "3rd"]
        t1_is_placeholder = any(kw in str(t1) for kw in placeholders_keywords) if t1 else True
        t2_is_placeholder = any(kw in str(t2) for kw in placeholders_keywords) if t2 else True
        
        if t1_is_placeholder or t2_is_placeholder:
            prompt_raw = (
                f"The prompt for this match cannot be generated yet because one or both teams "
                f"depend on the results of earlier matches.\n\n"
                f"Current Placeholders:\n"
                f"- Team 1: {t1}\n"
                f"- Team 2: {t2}\n\n"
                f"Once the previous rounds are played and the teams are resolved, the prompt preview "
                f"will be dynamically generated here."
            )
        else:
            predictions = {}
            if os.path.exists(PREDICTIONS_FILE):
                try:
                    with open(PREDICTIONS_FILE, "r") as f:
                        predictions = json.load(f)
                except Exception:
                    pass
            
            group_standings = None
            if m.get("stage") == "group":
                group_standings = state_data.get("standings", {}).get(m.get("group"))
                
            try:
                prompt_raw = build_prompt(t1, t2, m.get("stage"), m.get("group"), group_standings, predictions)
            except Exception as e:
                prompt_raw = f"Error building prompt dynamically: {e}"
                
    return True, title, stage_clean, score_display, cot_formatted, prompt_raw

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=True)
