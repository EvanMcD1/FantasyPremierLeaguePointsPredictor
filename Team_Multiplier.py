import os
import pandas as pd


class MultiplierCalculator:
    def __init__(self, folder_path):
        self.folder_path = folder_path
        self.gw_csv_files = self.get_gw_files()
        self.def_home_multiplier = {}
        self.def_away_multiplier = {}
        self.mid_home_multiplier = {}
        self.mid_away_multiplier = {}
        self.gk_home_multiplier = {}
        self.gk_away_multiplier = {}
        self.fwd_home_multiplier = {}
        self.fwd_away_multiplier = {}
        self.team_id_to_name = {
            1: 'Arsenal', 2: 'Aston Villa', 3: 'Bournemouth', 4: 'Brentford', 5: 'Brighton',
            6: 'Chelsea', 7: 'Crystal Palace', 8: 'Everton', 9: 'Fulham', 10: 'Leeds',
            11: 'Leicester', 12: 'Liverpool', 13: 'Man City', 14: 'Man Utd', 15: 'Newcastle',
            16: 'Nottingham Forest', 17: 'Southampton', 18: 'Spurs', 19: 'West Ham', 20: 'Wolves'
        }

    def get_gw_files(self):
        gw_files = []
        for file_name in os.listdir(self.folder_path):
            if file_name.startswith('gw') and file_name.endswith('.csv'):
                file_path = os.path.join(self.folder_path, file_name)
                gw_files.append(file_path)
        return sorted(gw_files, key=lambda x: int(os.path.splitext(os.path.basename(x))[0][2:]))

    def calculate_position_multipliers(self, position):
        home_points = {}
        away_points = {}

        for file_path in self.gw_csv_files:
            data = pd.read_csv(file_path)
            if {'position', 'minutes', 'total_points', 'opponent_team', 'was_home'}.issubset(data.columns):
                players = data[(data['position'] == position) & (data['minutes'] > 45)]
                for _, row in players.iterrows():
                    opponent_team_id = row['opponent_team']
                    opponent_team_name = self.team_id_to_name.get(opponent_team_id, f"Unknown Team {opponent_team_id}")
                    total_points = row['total_points']
                    if row['was_home']:
                        home_points[opponent_team_name] = home_points.get(opponent_team_name, []) + [total_points]
                    else:
                        away_points[opponent_team_name] = away_points.get(opponent_team_name, []) + [total_points]

        home_avg_points = {team: sum(points) / len(points) for team, points in home_points.items()}
        away_avg_points = {team: sum(points) / len(points) for team, points in away_points.items()}
        overall_home_avg_points = sum(home_avg_points.values()) / len(home_avg_points) if home_avg_points else 0
        overall_away_avg_points = sum(away_avg_points.values()) / len(away_avg_points) if away_avg_points else 0

        home_multiplier = {team: avg_points / overall_home_avg_points for team, avg_points in
                           home_avg_points.items()} if overall_home_avg_points else {}
        away_multiplier = {team: avg_points / overall_away_avg_points for team, avg_points in
                           away_avg_points.items()} if overall_away_avg_points else {}

        return home_multiplier, away_multiplier

    def calculate_all_multipliers(self):
        self.def_home_multiplier, self.def_away_multiplier = self.calculate_position_multipliers('DEF')
        self.mid_home_multiplier, self.mid_away_multiplier = self.calculate_position_multipliers('MID')
        self.gk_home_multiplier, self.gk_away_multiplier = self.calculate_position_multipliers('GK')
        self.fwd_home_multiplier, self.fwd_away_multiplier = self.calculate_position_multipliers('FWD')

    def save_multipliers_to_csv(self):
        def_df = pd.DataFrame(list(self.def_home_multiplier.items()), columns=['Team', 'DEF_Home_Multiplier'])
        def_df['DEF_Away_Multiplier'] = def_df['Team'].map(self.def_away_multiplier)

        mid_df = pd.DataFrame(list(self.mid_home_multiplier.items()), columns=['Team', 'MID_Home_Multiplier'])
        mid_df['MID_Away_Multiplier'] = mid_df['Team'].map(self.mid_away_multiplier)

        gk_df = pd.DataFrame(list(self.gk_home_multiplier.items()), columns=['Team', 'GK_Home_Multiplier'])
        gk_df['GK_Away_Multiplier'] = gk_df['Team'].map(self.gk_away_multiplier)

        fwd_df = pd.DataFrame(list(self.fwd_home_multiplier.items()), columns=['Team', 'FWD_Home_Multiplier'])
        fwd_df['FWD_Away_Multiplier'] = fwd_df['Team'].map(self.fwd_away_multiplier)

        # Merging the dataframes into one
        result_df = def_df.merge(mid_df, on='Team', how='outer').merge(gk_df, on='Team', how='outer').merge(fwd_df,
                                                                                                            on='Team',
                                                                                                            how='outer')

        # Save the result dataframe to CSV
        result_df.to_csv(f'home_away_points_multipliers_22-23.csv', index=False)


folder_path = 'Fantasy-Premier-League-master/data/2022-23/gws'

multiplier_calculator = MultiplierCalculator(folder_path)
multiplier_calculator.calculate_all_multipliers()
multiplier_calculator.save_multipliers_to_csv()
