import pandas as pd
from itertools import combinations
from math import comb

# Load the CSV data
data = pd.read_csv('/Users/evanmcdermid/PycharmProjects/FantasyPremierLeague/24_25_combined_gw5_data.csv')

# Separate players by position
players = {
    'GK': [], 'DEF': [], 'MID': [], 'FWD': []
}

for _, row in data.iterrows():
    pos = row['Position']
    players[pos].append(row)


# Function to get top players by defined value brackets
def top_players_by_brackets(players_list):
    # Define the brackets and the number of players to select from each
    brackets = {
        "<5": {'range': (0, 4.9), 'count': 2},
        "5.0-5.9": {'range': (5.0, 5.9), 'count': 2},
        "6.0-7.5": {'range': (6.0, 7.4), 'count': 3},
        "7.5-9.4": {'range': (7.6, 9.4), 'count': 3},
        ">9.5": {'range': (9.5, float('inf')), 'count': 3},
    }

    top_players = []

    for bracket_name, bracket_info in brackets.items():
        range_min, range_max = bracket_info['range']
        count = bracket_info['count']

        # Filter players within the value range
        players_in_bracket = [
            player for player in players_list
            if range_min <= player['Value'] <= range_max
        ]

        # Sort players by 'Points Next 5' and select the top ones based on count
        sorted_players = sorted(players_in_bracket, key=lambda p: p['Points Next 5'], reverse=True)
        top_players.extend(sorted_players[:count])

    return top_players


# Get top players for each position based on the value brackets
top_gk = top_players_by_brackets(players['GK'])
top_def = top_players_by_brackets(players['DEF'])
top_mid = top_players_by_brackets(players['MID'])
top_fwd = top_players_by_brackets(players['FWD'])


# Now, you can use these top players in your team selection logic


def valid_team(team):
    team_counts = {}
    for player in team:
        team_name = player['Team']
        if team_name not in team_counts:
            team_counts[team_name] = 0
        team_counts[team_name] += 1
        if team_counts[team_name] > 3:
            return False
    return True

i=0
# Function to generate valid team combinations
def generate_valid_teams(gk, def_players, mid_players, att_players, max_value):
    global i
    best_team = None
    best_points = 0
    team_value=0

    for gk_comb in combinations(gk, 1):
        for def_comb in combinations(def_players, 3):
            for mid_comb in combinations(mid_players, 4):
                for att_comb in combinations(att_players, 3):
                    i+=1
                    team = list(gk_comb) + list(def_comb) + list(mid_comb) + list(att_comb)
                    total_value = sum(player['Value'] for player in team)
                    if total_value <= max_value and total_value>=max_value-1:
                        if valid_team(team):
                            captain_points = max(player['Points Next 5'] for player in team)
                            total_points = sum(player['Points Next 5'] for player in team) + captain_points
                            if total_points > best_points:
                                best_points = total_points
                                best_team = team
                                team_value = total_value
                                print(best_team, best_points, team_value)
                                print(i)
            for mid_comb in combinations(mid_players, 5):
                for att_comb in combinations(att_players, 2):
                    i+=1
                    team = list(gk_comb) + list(def_comb) + list(mid_comb) + list(att_comb)
                    total_value = sum(player['Value'] for player in team)
                    if total_value <= max_value and total_value>=max_value-1:
                        if valid_team(team):
                            captain_points = max(player['Points Next 5'] for player in team)
                            total_points = sum(player['Points Next 5'] for player in team) + captain_points
                            if total_points > best_points:
                                best_points = total_points
                                best_team = team
                                team_value = total_value
                                print(best_team, best_points, team_value)
                                print(i)
    print(i)
    return best_team, best_points, team_value


# Run the team generation function
best_team, best_points, team_value = generate_valid_teams(top_gk, top_def, top_mid, top_fwd, 83.5)

# Output the results
if best_team:
    print("Best team:")
    for player in best_team:
        print(f"{player['Name']} - {player['Position']} - {player['Points Next 5']} points")
    print(f"Total Points: {best_points}")
    print("Value:" + str(team_value) )
else:
    print("No valid team found within the budget.")
