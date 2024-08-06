import os
import pandas as pd


class MultiplierCalculator:
    def __init__(self, folder_path, gameweek):
        self.folder_path = folder_path
        self.gameweek = gameweek
        self.gw_csv_files = self.get_gw_files()
        self.home_multiplier = {}
        self.away_multiplier = {}

    def get_gw_files(self):
        gw_files = []
        for file_name in os.listdir(self.folder_path):
            if file_name.startswith('gw') and file_name.endswith('.csv'):
                file_path = os.path.join(self.folder_path, file_name)
                gw_files.append(file_path)
        return sorted(gw_files, key=lambda x: int(os.path.splitext(os.path.basename(x))[0][2:]))

    def calculate_multipliers(self):
        home_expected_assists = {}
        away_expected_assists = {}

        for file_path in self.gw_csv_files:
            gw_number = int(os.path.splitext(os.path.basename(file_path))[0][2:])
            if gw_number <= self.gameweek:
                data = pd.read_csv(file_path)
                if 'expected_assists' in data.columns:
                    for _, row in data.iterrows():
                        opponent_team = row['opponent_team']
                        expected_assists = row['expected_assists']
                        if row['was_home']:
                            home_expected_assists[opponent_team] = home_expected_assists.get(opponent_team, []) + [expected_assists]
                        else:
                            away_expected_assists[opponent_team] = away_expected_assists.get(opponent_team, []) + [expected_assists]

        home_avg_assists = {team: sum(assists) / len(assists) for team, assists in home_expected_assists.items()}
        away_avg_assists = {team: sum(assists) / len(assists) for team, assists in away_expected_assists.items()}
        overall_home_avg_assists = sum(home_avg_assists.values()) / len(home_avg_assists) if home_avg_assists else 0
        overall_away_avg_assists = sum(away_avg_assists.values()) / len(away_avg_assists) if away_avg_assists else 0

        self.home_multiplier = {team: avg_assists / overall_home_avg_assists for team, avg_assists in
                                home_avg_assists.items()} if overall_home_avg_assists else {}
        self.away_multiplier = {team: avg_assists / overall_away_avg_assists for team, avg_assists in
                                away_avg_assists.items()} if overall_away_avg_assists else {}

    def save_multipliers_to_csv(self):
        home_df = pd.DataFrame(list(self.home_multiplier.items()), columns=['Opponent_Team_ID', 'Multiplier_Home'])
        away_df = pd.DataFrame(list(self.away_multiplier.items()), columns=['Opponent_Team_ID', 'Multiplier_Away'])

        # Merge the dataframes into one
        result_df = home_df.merge(away_df, on='Opponent_Team_ID', how='outer')

        # Save the result dataframe to CSV
        result_df.to_csv(f'expected_assists_multipliers_gw{self.gameweek}.csv', index=False)


folder_path = 'Fantasy-Premier-League-master/data/2023-24/gws'

for gameweek in range(1, 39):
    multiplier_calculator = MultiplierCalculator(folder_path, gameweek)
    multiplier_calculator.calculate_multipliers()
    multiplier_calculator.save_multipliers_to_csv()
