import os
import pandas as pd

class MultiplierCalculator:
    def __init__(self, folder_path, gameweek):
        self.folder_path = folder_path
        self.gameweek = gameweek
        self.gw_csv_files = self.get_gw_files()
        self.home_multiplier = {}
        self.away_multiplier = {}
        self.team_mappings = self.load_team_mappings()
        self.previous_data = self.load_previous_data()

    def load_team_mappings(self):
        teams_csv_path = '/Users/evanmcdermid/PycharmProjects/FantasyPremierLeague/Fantasy-Premier-League-master/data/2024-25/teams.csv'
        teams_df = pd.read_csv(teams_csv_path)
        return {row['id']: row['name'] for _, row in teams_df.iterrows()}

    def load_previous_data(self):
        file_path = '/Users/evanmcdermid/PycharmProjects/FantasyPremierLeague/expected_goals_conceded_multipliers_gw38.csv'
        if os.path.exists(file_path):
            return pd.read_csv(file_path).set_index('Opponent_Team_Name')
        else:
            raise FileNotFoundError(f"Previous data file not found: {file_path}")

    def get_gw_files(self):
        gw_files = []
        for file_name in os.listdir(self.folder_path):
            if file_name.startswith('gw') and file_name.endswith('.csv'):
                file_path = os.path.join(self.folder_path, file_name)
                gw_files.append(file_path)
        return sorted(gw_files, key=lambda x: int(os.path.splitext(os.path.basename(x))[0][2:]))

    def calculate_multipliers(self):
        home_goals_conceded = {team_name: [] for team_name in self.team_mappings.values()}
        away_goals_conceded = {team_name: [] for team_name in self.team_mappings.values()}

        for file_path in self.gw_csv_files:
            gw_number = int(os.path.splitext(os.path.basename(file_path))[0][2:])
            if gw_number <= self.gameweek:
                data = pd.read_csv(file_path)
                if 'expected_goals_conceded' in data.columns:
                    for _, row in data.iterrows():
                        opponent_team = row['opponent_team']
                        opponent_team_name = self.team_mappings.get(opponent_team)
                        expected_goals_conceded = row['expected_goals_conceded']
                        if row['was_home']:
                            home_goals_conceded[opponent_team_name] = home_goals_conceded.get(opponent_team_name, []) + [expected_goals_conceded]
                        else:
                            away_goals_conceded[opponent_team_name] = away_goals_conceded.get(opponent_team_name, []) + [expected_goals_conceded]

        home_avg_goals_conceded = {
            team: (
                    (sum(goals) / len(goals)) * (self.gameweek / 38) +
                    (self.previous_data.at[team, 'Multiplier_Home'] if team in self.previous_data.index else 1) * (
                                (38 - self.gameweek) / 38)
            ) if goals else (self.previous_data.at[team, 'Multiplier_Home'] if team in self.previous_data.index else 1)
            for team, goals in home_goals_conceded.items()
        }

        away_avg_goals_conceded = {
            team: (
                    (sum(goals) / len(goals)) * (self.gameweek / 38) +
                    (self.previous_data.at[team, 'Multiplier_Away'] if team in self.previous_data.index else 1) * (
                                (38 - self.gameweek) / 38)
            ) if goals else (self.previous_data.at[team, 'Multiplier_Away'] if team in self.previous_data.index else 1)
            for team, goals in away_goals_conceded.items()
        }

        overall_home_avg_goals_conceded = sum(home_avg_goals_conceded.values()) / len(home_avg_goals_conceded) if home_avg_goals_conceded else 0
        overall_away_avg_goals_conceded = sum(away_avg_goals_conceded.values()) / len(away_avg_goals_conceded) if away_avg_goals_conceded else 0

        self.home_multiplier = {team: avg_goals / overall_home_avg_goals_conceded for team, avg_goals in home_avg_goals_conceded.items()} if overall_home_avg_goals_conceded else {}
        self.away_multiplier = {team: avg_goals / overall_away_avg_goals_conceded for team, avg_goals in away_avg_goals_conceded.items()} if overall_away_avg_goals_conceded else {}

    def save_multipliers_to_csv(self):
        home_df = pd.DataFrame(list(self.home_multiplier.items()), columns=['Opponent_Team_Name', 'Multiplier_Home'])
        away_df = pd.DataFrame(list(self.away_multiplier.items()), columns=['Opponent_Team_Name', 'Multiplier_Away'])

        # Add opponent team IDs
        home_df['Opponent_Team_ID'] = home_df['Opponent_Team_Name'].map({v: k for k, v in self.team_mappings.items()})
        away_df['Opponent_Team_ID'] = away_df['Opponent_Team_Name'].map({v: k for k, v in self.team_mappings.items()})

        # Merge the dataframes into one
        result_df = home_df.merge(away_df, on='Opponent_Team_Name', how='outer')
        result_df['Opponent_Team_ID'] = result_df['Opponent_Team_ID_x'].combine_first(
            result_df['Opponent_Team_ID_y'])

        # Save the result dataframe to CSV
        result_df.to_csv(f'expected_goals_conceded_multipliers_24_25_gw{self.gameweek}.csv', index=False)


folder_path = 'Fantasy-Premier-League-master/data/2024-25'

for gameweek in range(0, 39):
    multiplier_calculator = MultiplierCalculator(folder_path, gameweek)
    multiplier_calculator.calculate_multipliers()
    multiplier_calculator.save_multipliers_to_csv()
