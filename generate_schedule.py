import yaml

# Load groups
with open("groups.yaml", "r") as f:
    groups = yaml.safe_load(f)

matches = []
match_id = 1

# Generate Group Stage Matches (72 matches)
# We will do 3 Matchdays for all 12 groups A to L.
# For a group with teams [T1, T2, T3, T4]:
# MD 1: T1 vs T2, T3 vs T4
# MD 2: T1 vs T3, T4 vs T2
# MD 3: T4 vs T1, T2 vs T3

# MD 1
for g_name, teams in groups.items():
    matches.append({
        "id": match_id,
        "stage": "group",
        "group": g_name.split()[-1], # e.g. "A" from "Group A"
        "team1": teams[0],
        "team2": teams[1]
    })
    match_id += 1
    matches.append({
        "id": match_id,
        "stage": "group",
        "group": g_name.split()[-1],
        "team1": teams[2],
        "team2": teams[3]
    })
    match_id += 1

# MD 2
for g_name, teams in groups.items():
    matches.append({
        "id": match_id,
        "stage": "group",
        "group": g_name.split()[-1],
        "team1": teams[0],
        "team2": teams[2]
    })
    match_id += 1
    matches.append({
        "id": match_id,
        "stage": "group",
        "group": g_name.split()[-1],
        "team1": teams[3],
        "team2": teams[1]
    })
    match_id += 1

# MD 3
for g_name, teams in groups.items():
    matches.append({
        "id": match_id,
        "stage": "group",
        "group": g_name.split()[-1],
        "team1": teams[3],
        "team2": teams[0]
    })
    match_id += 1
    matches.append({
        "id": match_id,
        "stage": "group",
        "group": g_name.split()[-1],
        "team1": teams[1],
        "team2": teams[2]
    })
    match_id += 1

# Generate Round of 32 Matches (16 matches: 73 to 88)
r32_pairings = [
    # Match ID: 73
    {"team1_placeholder": "Runner-up Group A", "team2_placeholder": "Runner-up Group B"},
    # Match ID: 74
    {"team1_placeholder": "Winner Group C", "team2_placeholder": "Runner-up Group F"},
    # Match ID: 75
    {"team1_placeholder": "Winner Group E", "team2_placeholder": "3rd Group A/B/C/D/F"},
    # Match ID: 76
    {"team1_placeholder": "Winner Group F", "team2_placeholder": "Runner-up Group C"},
    # Match ID: 77
    {"team1_placeholder": "Runner-up Group E", "team2_placeholder": "Runner-up Group I"},
    # Match ID: 78
    {"team1_placeholder": "Winner Group I", "team2_placeholder": "3rd Group C/D/F/G/H"},
    # Match ID: 79
    {"team1_placeholder": "Winner Group A", "team2_placeholder": "3rd Group C/E/F/H/I"},
    # Match ID: 80
    {"team1_placeholder": "Winner Group L", "team2_placeholder": "3rd Group E/H/I/J/K"},
    # Match ID: 81
    {"team1_placeholder": "Winner Group G", "team2_placeholder": "3rd Group A/E/H/I/J"},
    # Match ID: 82
    {"team1_placeholder": "Winner Group D", "team2_placeholder": "3rd Group B/E/F/I/J"},
    # Match ID: 83
    {"team1_placeholder": "Winner Group H", "team2_placeholder": "Runner-up Group J"},
    # Match ID: 84
    {"team1_placeholder": "Runner-up Group K", "team2_placeholder": "Runner-up Group L"},
    # Match ID: 85
    {"team1_placeholder": "Winner Group B", "team2_placeholder": "3rd Group E/F/G/I/J"},
    # Match ID: 86
    {"team1_placeholder": "Runner-up Group D", "team2_placeholder": "Runner-up Group G"},
    # Match ID: 87
    {"team1_placeholder": "Winner Group J", "team2_placeholder": "Runner-up Group H"},
    # Match ID: 88
    {"team1_placeholder": "Winner Group K", "team2_placeholder": "3rd Group D/E/I/J/L"}
]

for idx, p in enumerate(r32_pairings):
    p.update({
        "id": match_id,
        "stage": "KO_R32",
        "match_num": 73 + idx
    })
    matches.append(p)
    match_id += 1

# Generate Round of 16 Matches (8 matches: 89 to 96)
r16_pairings = [
    # M89
    {"team1_placeholder": "Winner Match 73", "team2_placeholder": "Winner Match 75"},
    # M90
    {"team1_placeholder": "Winner Match 74", "team2_placeholder": "Winner Match 77"},
    # M91
    {"team1_placeholder": "Winner Match 76", "team2_placeholder": "Winner Match 78"},
    # M92
    {"team1_placeholder": "Winner Match 79", "team2_placeholder": "Winner Match 80"},
    # M93
    {"team1_placeholder": "Winner Match 83", "team2_placeholder": "Winner Match 84"},
    # M94
    {"team1_placeholder": "Winner Match 81", "team2_placeholder": "Winner Match 82"},
    # M95
    {"team1_placeholder": "Winner Match 86", "team2_placeholder": "Winner Match 88"},
    # M96
    {"team1_placeholder": "Winner Match 85", "team2_placeholder": "Winner Match 87"}
]

for idx, p in enumerate(r16_pairings):
    p.update({
        "id": match_id,
        "stage": "KO_R16",
        "match_num": 89 + idx
    })
    matches.append(p)
    match_id += 1

# Generate Quarterfinals (4 matches: 97 to 100)
qf_pairings = [
    # M97
    {"team1_placeholder": "Winner Match 89", "team2_placeholder": "Winner Match 90"},
    # M98
    {"team1_placeholder": "Winner Match 93", "team2_placeholder": "Winner Match 94"},
    # M99
    {"team1_placeholder": "Winner Match 91", "team2_placeholder": "Winner Match 92"},
    # M100
    {"team1_placeholder": "Winner Match 95", "team2_placeholder": "Winner Match 96"}
]

for idx, p in enumerate(qf_pairings):
    p.update({
        "id": match_id,
        "stage": "KO_QF",
        "match_num": 97 + idx
    })
    matches.append(p)
    match_id += 1

# Generate Semifinals (2 matches: 101 to 102)
sf_pairings = [
    # M101
    {"team1_placeholder": "Winner Match 97", "team2_placeholder": "Winner Match 98"},
    # M102
    {"team1_placeholder": "Winner Match 99", "team2_placeholder": "Winner Match 100"}
]

for idx, p in enumerate(sf_pairings):
    p.update({
        "id": match_id,
        "stage": "KO_SF",
        "match_num": 101 + idx
    })
    matches.append(p)
    match_id += 1

# Third Place Match (Match 103)
matches.append({
    "id": match_id,
    "stage": "KO_3RD",
    "match_num": 103,
    "team1_placeholder": "Loser Match 101",
    "team2_placeholder": "Loser Match 102"
})
match_id += 1

# Final (Match 104)
matches.append({
    "id": match_id,
    "stage": "KO_FINAL",
    "match_num": 104,
    "team1_placeholder": "Winner Match 101",
    "team2_placeholder": "Winner Match 102"
})

# Save to matches.yaml
with open("matches.yaml", "w") as f:
    yaml.dump(matches, f, sort_keys=False)

print(f"Successfully generated matches.yaml with {len(matches)} matches.")
