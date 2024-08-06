import os
import pandas as pd
import re
from functools import lru_cache

class YearlyStats:
    def __init__(self, fixtures_file, player_id_file, players_raw_file, folder_path):
        self.fixtures_data = pd.read_csv(fixtures_file)
        self.player_id_file = player_id_file
        self.players_raw_file = players_raw_file
        self.folder_path = folder_path
        self.gw_files = self.get_all_gw_files()

    def get_all_gw_files(self):
        gw_files = []
        for file_name in os.listdir(self.folder_path):
            if file_name.startswith('gw') and file_name.endswith('.csv'):
                file_path = os.path.join(self.folder_path, file_name)
                gw_files.append(file_path)
        gw_files.sort(key=lambda x: int(re.findall(r'\d+', os.path.basename(x))[0]))
        return gw_files

    @lru_cache(maxsize=None)
    def get_player_id(self, first_name, second_name):
        data = pd.read_csv(self.player_id_file)
        if {'first_name', 'second_name', 'id'}.issubset(data.columns):
            player_data = data[(data['first_name'] == first_name) & (data['second_name'] == second_name)]
            if not player_data.empty:
                return player_data['id'].values[0]
        return None

    @lru_cache(maxsize=None)
    def get_team_code(self, player_id):
        data = pd.read_csv(self.players_raw_file)
        if {'id', 'team'}.issubset(data.columns):
            player_data = data[data['id'] == player_id]
            if not player_data.empty:
                return player_data['team'].values[0]
        return None

    @lru_cache(maxsize=None)
    def get_player_position(self, player_name, gameweek):
        file_path = os.path.join(self.folder_path, f'gw{gameweek}.csv')
        data = pd.read_csv(file_path)
        if {'name', 'position'}.issubset(data.columns):
            player_data = data[data['name'] == player_name]
            if not player_data.empty:
                return player_data['position'].values[0]
        return None

    def expected_save_points_permin(self, player_name, csv_files, expected_minutes):
        total_saves = 0
        total_minutes = 0

        for file_path in csv_files:
            data = pd.read_csv(file_path)
            if {'name', 'saves', 'minutes'}.issubset(data.columns):
                player_data = data[(data['name'] == player_name)]
                if not player_data.empty:
                    total_saves += player_data['saves'].sum()
                    total_minutes += player_data['minutes'].sum()

        average_saves_per_minute = total_saves / total_minutes if total_minutes > 0 else 0

        return average_saves_per_minute * (1 / 3)

    def expected_bonus_points_permin(self, player_name, csv_files, expected_minutes):
        total_bonus_points = 0
        total_minutes = 0

        for file_path in csv_files:
            data = pd.read_csv(file_path)
            if {'name', 'bonus', 'minutes'}.issubset(data.columns):
                player_data = data[(data['name'] == player_name)]
                if not player_data.empty:
                    total_bonus_points += player_data['bonus'].sum()
                    total_minutes += player_data['minutes'].sum()

        average_bonus_per_minute = total_bonus_points / total_minutes if total_minutes > 0 else 0

        return average_bonus_per_minute

    def expected_goals_conceded_points_permin(self, player_name, csv_files, expected_minutes, player_position,xgcmultiplier):
        total_expected_goals_conceded = 0
        total_minutes = 0
        for file_path in csv_files:
            data = pd.read_csv(file_path)
            if {'name', 'expected_goals_conceded', 'minutes'}.issubset(data.columns):
                player_data = data[(data['name'] == player_name) & (data['position'] == player_position)]
                if not player_data.empty:
                    total_expected_goals_conceded += player_data['expected_goals_conceded'].sum()
                    total_minutes += player_data['minutes'].sum()

        average_xGC_per_minute = total_expected_goals_conceded / total_minutes if total_minutes > 0 else 0


        # Calculate expected points lost due to goals conceded for defenders and goalkeepers
        if player_position in ["DEF", "GK"]:
            expected_goals_conceded_points_permin = average_xGC_per_minute * -0.5
        else:
            expected_goals_conceded_points_permin = 0  # No points deduction for other positions

        return expected_goals_conceded_points_permin

    def yellow_card_points_permin(self, player_name, csv_files, expected_minutes, player_position):
        total_yellow_cards = 0
        total_minutes = 0
        for file_path in csv_files:
            data = pd.read_csv(file_path)
            if {'name', 'yellow_cards', 'minutes'}.issubset(data.columns):
                player_data = data[(data['name'] == player_name) & (data['position'] == player_position)]
                if not player_data.empty:
                    total_yellow_cards += player_data['yellow_cards'].sum()
                    total_minutes += player_data['minutes'].sum()

        average_yc_per_minute = total_yellow_cards / total_minutes if total_minutes > 0 else 0

        # Multiply the average yellow cards per minute by expected minutes and then by -1 to get the points
        expected_yellow_card_points_permin = average_yc_per_minute * -1

        return expected_yellow_card_points_permin

    def expected_cleansheet_points_permin(self, player_name, csv_files, expected_minutes, player_position, gameweek):
        total_clean_sheets = 0
        total_minutes = 0
        for file_path in csv_files:
            data = pd.read_csv(file_path)
            if {'name', 'clean_sheets', 'minutes'}.issubset(data.columns):
                player_data = data[(data['name'] == player_name) & (data['position'] == player_position)]
                if not player_data.empty:
                    total_clean_sheets += player_data['clean_sheets'].sum()
                    total_minutes += player_data['minutes'].sum()
        if player_position in ["DEF", "GK"]:
            if total_minutes!=0:
                expected_cleansheet_points_permin=(total_clean_sheets/total_minutes)*4
            else:
                expected_cleansheet_points_permin = 0
        else:
            expected_cleansheet_points_permin=0

        return expected_cleansheet_points_permin

    def expected_goals_points_permin(self, player_name, csv_files, expected_minutes, multipliers_data, is_home, player_position, gameweek):
        total_expected_goals = 0
        total_minutes = 0
        for file_path in csv_files:
            data = pd.read_csv(file_path)
            if {'name', 'expected_goals', 'minutes'}.issubset(data.columns):
                player_data = data[(data['name'] == player_name) & (data['position'] == player_position)]
                if not player_data.empty:
                    total_expected_goals += player_data['expected_goals'].sum()
                    total_minutes += player_data['minutes'].sum()

        average_xG_per_minute = total_expected_goals / total_minutes if total_minutes > 0 else 0

        if player_position == "FWD":
            expected_goals_points_permin = average_xG_per_minute * 4
        elif player_position == "MID":
            expected_goals_points_permin = average_xG_per_minute * 5
        else:
            expected_goals_points_permin = average_xG_per_minute * 6

        return expected_goals_points_permin

    def expected_assists_points_permin(self, player_name, csv_files, expected_minutes, multipliers_data, is_home, player_position, gameweek):
        total_expected_assists = 0
        total_minutes = 0
        for file_path in csv_files:
            data = pd.read_csv(file_path)
            if {'name', 'expected_assists', 'minutes'}.issubset(data.columns):
                player_data = data[(data['name'] == player_name) & (data['position'] == player_position)]
                if not player_data.empty:
                    total_expected_assists += player_data['expected_assists'].sum()
                    total_minutes += player_data['minutes'].sum()

        average_xA_per_minute = total_expected_assists / total_minutes if total_minutes > 0 else 0


        expected_assists_points_permin = average_xA_per_minute * 3

        return expected_assists_points_permin

    def expected_points_permin(self, firstname, secondname, gameweek, expectedminutes):
        player_id = self.get_player_id(firstname, secondname)
        if player_id is None:
            return [0,0,0,0]
        team_code = self.get_team_code(player_id)
        opponent_team_code, is_home = 0,0
        if opponent_team_code is None:
            return [0,0,0,0]
        player_name = f"{firstname} {secondname}"
        position = self.get_player_position(player_name, gameweek)
        if position is None:
            return [0,0,0,0]

        # Calculate goals points using multipliers data
        goals_points_permin = self.expected_goals_points_permin(player_name, self.gw_files, expectedminutes,
                                                  None, is_home, position, gameweek)
        assist_points_permin = self.expected_assists_points_permin(player_name, self.gw_files, expectedminutes,
                                                    None, is_home, position, gameweek)
        bonus_points_permin = self.expected_bonus_points_permin(player_name, self.gw_files, expectedminutes)
        save_points_permin = self.expected_save_points_permin(player_name, self.gw_files, expectedminutes)
        yellowcard_points_permin = self.yellow_card_points_permin(player_name, self.gw_files, expectedminutes,
                                                    position)
        goals_conceded_points_permin=self.expected_goals_conceded_points_permin(player_name,self.gw_files,expectedminutes,position,None)
        all_points_permin=[goals_points_permin, assist_points_permin, goals_conceded_points_permin, bonus_points_permin+ save_points_permin+ yellowcard_points_permin]

        return all_points_permin

    def combine_gw_data(self, gameweek):
        all_player_data = []

        # Construct the file path for the specified gameweek
        gw_file = os.path.join(self.folder_path, f'gw{gameweek}.csv')


        gw_data = pd.read_csv(gw_file)


        for index, row in gw_data.iterrows():
            player_name = row['name']
            position = row['position']
            expected_minutes = row['minutes']

            names = player_name.split()
            first_name = names[0]
            last_name = ' '.join(names[1:])

            all_points_permin = self.expected_points_permin(first_name, last_name, gameweek, expected_minutes)
            if all_points_permin!=0:

                all_player_data.append({
                    'Name': player_name,
                    'Position': position,
                    'Goals Points Per Minute': all_points_permin[0],
                    'Assist Points Per Minute': all_points_permin[1],
                    'Goals Conceded Points Per Minute': all_points_permin[2],
                    'Other Points Per Minute': all_points_permin[3],
                })

        # Create a DataFrame from the collected player data
        df = pd.DataFrame(all_player_data)

        # Construct the output file path
        file_output_path = (f'2023-24_player_points_per_minute_data.csv')

        # Save the sorted DataFrame to a CSV file
        df.to_csv(file_output_path, index=False, mode='w')


fpl_predictor = YearlyStats(
            fixtures_file='Fantasy-Premier-League-master/data/2023-24/fixtures.csv',
            player_id_file='Fantasy-Premier-League-master/data/2023-24/player_idlist.csv',
            players_raw_file='Fantasy-Premier-League-master/data/2023-24/players_raw.csv',
            folder_path='Fantasy-Premier-League-master/data/2023-24/gws'
        )
fpl_predictor.combine_gw_data(38)