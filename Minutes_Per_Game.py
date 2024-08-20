import os
import pandas as pd

def calculate_average_minutes_per_game(gw_folders, output_csv_path):
    # Initialize a dictionary to hold total minutes and game count for each player
    player_minutes_data = {}

    # Iterate over all provided folders containing gameweek files
    for gw_folder_path in gw_folders:
        # Load all gameweek files from the folder
        for file_name in os.listdir(gw_folder_path):
            if file_name.startswith('gw') and file_name.endswith('.csv'):
                file_path = os.path.join(gw_folder_path, file_name)
                gw_data = pd.read_csv(file_path)

                # Process each player's data
                for _, row in gw_data.iterrows():
                    # Extract player name
                    player_name = row['name']
                    minutes_played = row['minutes']
                    starts = row['starts']

                    if starts==1:
                        if player_name not in player_minutes_data:
                            player_minutes_data[player_name] = {'total_minutes': 0, 'games_played': 0}

                        player_minutes_data[player_name]['total_minutes'] += minutes_played
                        player_minutes_data[player_name]['games_played'] += starts

    # Calculate the average minutes per game for each player
    player_avg_minutes = []
    for player_name, data in player_minutes_data.items():
        avg_minutes = data['total_minutes'] / data['games_played'] if data['games_played'] > 0 else 0
        player_avg_minutes.append({'player_name': player_name, 'avg_minutes_per_game': avg_minutes})

    # Convert to DataFrame
    avg_minutes_df = pd.DataFrame(player_avg_minutes)

    # Save to CSV
    avg_minutes_df.to_csv(output_csv_path, index=False)

    return avg_minutes_df

# Define the folder paths containing the gameweek files for both seasons and the output CSV file path
gws_23_24 = '/Users/evanmcdermid/PycharmProjects/FantasyPremierLeague/Fantasy-Premier-League-master/data/2023-24/gws'
gws_24_25 = '/Users/evanmcdermid/PycharmProjects/FantasyPremierLeague/Fantasy-Premier-League-master/data/2024-25/gws'
gw_folders = [gws_23_24,gws_24_25]
output_csv_path = 'combined_player_avg_minutes_per_game.csv'

# Process both seasons and combine into one CSV
calculate_average_minutes_per_game(gw_folders, output_csv_path)
