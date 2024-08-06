import os
import pandas as pd
import re
from functools import lru_cache

class FPLPredictor:
    def __init__(self, fixtures_file, player_id_file, players_raw_file, folder_path):
        self.fixtures_data = pd.read_csv(fixtures_file)
        self.player_id_file = player_id_file
        self.players_raw_file = players_raw_file
        self.folder_path = folder_path
        self.team_id_to_name = self.load_team_mappings()
        self.gw_files = self.get_all_gw_files()
        self.multipliers_df = self.load_multipliers_data()


    def load_xg_multipliers_data(self, gameweek):
        while True:
            multipliers_file = f'expected_goals_multipliers_gw{gameweek-1}.csv'
            if os.path.exists(multipliers_file):
                return pd.read_csv(multipliers_file)
            else:
                gameweek-=1
            if gameweek<=0:
                return None

    def load_xa_multipliers_data(self, gameweek):
        multipliers_file = f'expected_assists_multipliers_gw{gameweek - 1}.csv'
        if os.path.exists(multipliers_file):
            return pd.read_csv(multipliers_file)
        else:
            gameweek -= 1
        if gameweek <= 0:
            return None

    def load_xgc_multipliers_data(self, gameweek):
        multipliers_file = f'expected_goals_conceded_multipliers_gw{gameweek - 1}.csv'
        if os.path.exists(multipliers_file):
            return pd.read_csv(multipliers_file)
        else:
            gameweek -= 1
        if gameweek <= 0:
            return None

    def load_multipliers_data(self):
        multipliers_csv_path = '/Users/evanmcdermid/PycharmProjects/FantasyPremierLeague/home_away_points_multipliers_22-23.csv'
        if os.path.exists(multipliers_csv_path):
            return pd.read_csv(multipliers_csv_path)
        else:
            raise FileNotFoundError(f"Multipliers file not found: {multipliers_csv_path}")

    def load_team_mappings(self):
        teams_csv_path = '/Users/evanmcdermid/PycharmProjects/FantasyPremierLeague/Fantasy-Premier-League-master/data/2023-24/teams.csv'
        teams_df = pd.read_csv(teams_csv_path)
        return {row['id']: row['name'] for _, row in teams_df.iterrows()}

    def get_team_multiplier(self,firstname,secondname,position,gameweek):
        player_id = self.get_player_id(firstname, secondname)
        if player_id is None:
            return 1
        team_code = self.get_team_code(player_id)
        opponent_team_code, is_home = self.get_opponent_team_code(team_code, gameweek)
        if opponent_team_code is None:
            return 1
        opponent_team_name=self.team_id_to_name.get(opponent_team_code)
        position_column = f"{position}_Home_Multiplier" if is_home else f"{position}_Away_Multiplier"
        team_row = self.multipliers_df[self.multipliers_df['Team'] == opponent_team_name]

        if team_row.empty or position_column not in team_row.columns:
            return 1.2

        return team_row[position_column].values[0]

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

    def get_opponent_team_code(self, team_code, gameweek):
        gameweek_data = self.fixtures_data[self.fixtures_data['event'] == gameweek]
        if {'team_h', 'team_a'}.issubset(gameweek_data.columns):
            row = gameweek_data[(gameweek_data['team_h'] == team_code) | (gameweek_data['team_a'] == team_code)]
            if not row.empty:
                if row['team_h'].values[0] == team_code:
                    return row['team_a'].values[0], True
                else:
                    return row['team_h'].values[0], False
        return None, None

    def get_expected_minutes_points(self, expected_minutes):
        if expected_minutes > 60:
            return 2
        elif expected_minutes > 0:
            return 1
        else:
            return 0

    def expected_save_points(self, player_name, csv_files, expected_minutes):
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

        return average_saves_per_minute * expected_minutes * (1 / 3)

    def expected_bonus_points(self, player_name, csv_files, expected_minutes):
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

        return average_bonus_per_minute * expected_minutes

    def expected_goals_conceded_points(self, player_name, csv_files, expected_minutes, player_position,xgcmultiplier):
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
            expected_goals_conceded_points = average_xGC_per_minute * expected_minutes * -0.5
        else:
            expected_goals_conceded_points = 0  # No points deduction for other positions

        return expected_goals_conceded_points

    def yellow_card_points(self, player_name, csv_files, expected_minutes, player_position):
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
        expected_yellow_card_points = average_yc_per_minute * expected_minutes * -1

        return max(-1, expected_yellow_card_points)

    def expected_cleansheet_points(self, player_name, csv_files, expected_minutes, player_position, gameweek):
        if expected_minutes > 60:
            cleansheet_percent = self.get_cleansheet_percent(player_name, gameweek)
            if player_position == "FWD":
                return 0
            elif player_position == "MID":
                return cleansheet_percent * 1
            else:
                return cleansheet_percent * 4
        else:
            return 0

    def get_cleansheet_percent(self, player_name, gameweek):
        try:
            cs_data = pd.read_csv(f"gw{gameweek}cs.csv")
            player_name_data = player_name.split()
            team_code = self.get_team_code(self.get_player_id(player_name_data[0], ' '.join(player_name_data[1:])))
            if team_code is not None:
                team_data = cs_data[cs_data['team'] == team_code]
                if not team_data.empty:
                    percent_str = team_data['cspercent'].values[0]
                    return float(percent_str.replace('%', '').strip()) / 100
        except FileNotFoundError:
            print(f"File gw{gameweek}cs.csv not found")
        except Exception as e:
            print(f"Error processing clean sheet data: {e}")
        return 0

    def expected_goals_points(self, player_name, csv_files, expected_minutes, multipliers_data, is_home, player_position, gameweek):
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

        # Get the team of the player


        # Adjust the expected goals points based on the team's performance multiplier
        if player_position == "FWD":
            expected_goals_points = average_xG_per_minute * expected_minutes * 4
        elif player_position == "MID":
            expected_goals_points = average_xG_per_minute * expected_minutes * 5
        else:
            expected_goals_points = average_xG_per_minute * expected_minutes * 6

        return expected_goals_points

    def expected_assists_points(self, player_name, csv_files, expected_minutes, multipliers_data, is_home, player_position, gameweek):
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


        # Adjust the expected assists points based on the team's performance multiplier
        expected_assists_points = average_xA_per_minute * expected_minutes * 3

        return expected_assists_points

    def minutes_per_start(self, player_name, consolidated_csv_path):
        total_starts = 0
        total_minutes = 0

        # Load the consolidated data from the CSV file
        data = pd.read_csv(consolidated_csv_path)
        player_name_data=player_name.split()
        player_id=self.get_player_id(player_name_data[0], ' '.join(player_name_data[1:]))

        # Check if the necessary columns are present in the data
        if {'player_id', 'avg_minutes_per_game'}.issubset(data.columns):
            # Filter the data for the specific player
            player_data = data[data['player_id'] == player_id]

            return(data['avg_minutes_per_game'].values[0])

        return 0


    def expected_points(self, firstname, secondname, gameweek, expectedminutes):
        player_id = self.get_player_id(firstname, secondname)
        if player_id is None:
            return 0
        team_code = self.get_team_code(player_id)
        opponent_team_code, is_home = self.get_opponent_team_code(team_code, gameweek)
        if opponent_team_code is None:
            return 0
        player_name = f"{firstname} {secondname}"
        player_position = self.get_player_position(player_name, gameweek)
        if player_position is None:
            return 0
        minutes_points = self.get_expected_minutes_points(expectedminutes)

        data=pd.read_csv('/Users/evanmcdermid/PycharmProjects/FantasyPremierLeague/2022-23_player_points_per_minute_data.csv')

        player_data = data[data['Name'] == player_name]
        multipliers_data=self.load_xg_multipliers_data(gameweek)
        if opponent_team_code is not None and multipliers_data is not None:
            if is_home:
                xGmultiplier = multipliers_data[multipliers_data['Opponent_Team_ID'] == opponent_team_code]['Multiplier_Home'].values[0]
            else:
                xGmultiplier = multipliers_data[multipliers_data['Opponent_Team_ID'] == opponent_team_code]['Multiplier_Away'].values[0]
        else:
            xGmultiplier = 1.0

        xgcmultiplier=self.load_xgc_multipliers_data(gameweek)
        if opponent_team_code is not None and xgcmultiplier is not None:
            if is_home:
                gcmultiplier = \
                xgcmultiplier[xgcmultiplier['Opponent_Team_ID'] == opponent_team_code]['Multiplier_Home'].values[
                    0]
            else:
                gcmultiplier = \
                xgcmultiplier[xgcmultiplier['Opponent_Team_ID'] == opponent_team_code]['Multiplier_Away'].values[
                    0]
        else:
            gcmultiplier = 1.0

        if pd.isna(gcmultiplier):
            gcmultiplier=1.0

        if pd.isna(xGmultiplier):
            xGmultiplier=1.0



        xP_permin=0
        if not player_data.empty:
            # Access the 'Expected Points Per Minute' value

            xGP_permin = player_data['Goals Points Per Minute'].values[0]*xGmultiplier
            xAP_permin=player_data['Assist Points Per Minute'].values[0]*xGmultiplier
            xGCP_permin = player_data['Goals Conceded Points Per Minute'].values[0]*gcmultiplier
            xOtherP_permin = player_data['Other Points Per Minute'].values[0]
            xP_permin=xOtherP_permin+xGCP_permin+xAP_permin+xGP_permin



        goals_points = self.expected_goals_points(player_name, self.gw_files[:gameweek - 1], expectedminutes,
                                                  None, is_home, player_position, gameweek)*xGmultiplier
        assist_points = self.expected_assists_points(player_name, self.gw_files[:gameweek - 1], expectedminutes,
                                                    None, is_home, player_position, gameweek)*xGmultiplier
        cleansheet_points = self.expected_cleansheet_points(player_name, self.gw_files[:gameweek - 1],
                                                            expectedminutes, player_position, gameweek)
        bonus_points = self.expected_bonus_points(player_name, self.gw_files[:gameweek - 1], expectedminutes)
        save_points = self.expected_save_points(player_name, self.gw_files[:gameweek - 1], expectedminutes)
        yellowcard_points = self.yellow_card_points(player_name, self.gw_files[:gameweek - 1], expectedminutes,
                                                    player_position)
        goals_conceded_points=self.expected_goals_conceded_points(player_name,self.gw_files[:gameweek - 1],expectedminutes,player_position,None)*gcmultiplier
        non_minute_points=(goals_points + assist_points + bonus_points + save_points + yellowcard_points + goals_conceded_points)
        if pd.isna(non_minute_points):
            all_points = (xP_permin * expectedminutes + minutes_points + cleansheet_points)
        elif xP_permin>-1 and gameweek<10:
            all_points=(non_minute_points*(gameweek/38)+(xP_permin*((38-gameweek)/38))*expectedminutes + minutes_points + cleansheet_points)
        elif xP_permin>0 and gameweek<20:
            all_points = (non_minute_points * 3/4 + xP_permin * 1/4 * expectedminutes + minutes_points + cleansheet_points)
        else:
            all_points = non_minute_points + minutes_points + cleansheet_points

        return all_points

    def combine_gw_data(self, gameweek):
        all_player_data = []

        # Construct the file path for the specified gameweek
        gw_file = os.path.join(self.folder_path, f'gw{gameweek}.csv')


        gw_data = pd.read_csv(gw_file)


        for index, row in gw_data.iterrows():
            player_name = row['name']
            position = row['position']
            total_points=row['total_points']
            expected_minutes = row['starts']*self.minutes_per_start(player_name,'combined_player_avg_minutes_per_game.csv')
            print(expected_minutes)
            minutes = row['minutes']
            value=row['value']/10

            names = player_name.split()
            first_name = names[0]
            last_name = ' '.join(names[1:])

            expected_points = self.expected_points(first_name, last_name, gameweek, expected_minutes)
            ppmillion=expected_points/value
            points_next_5=expected_points
            for i in range(4):
                points_next_5+=(self.expected_points(first_name, last_name, gameweek+1+i, expected_minutes))

            all_player_data.append({
                'Name': player_name,
                'Position': position,
                'Minutes': minutes,
                'Expected Minutes': expected_minutes,
                'Total Points': total_points,
                'Expected Points': expected_points,
                'Value': value,
                'Points Per Million': ppmillion,
                'Points Next 5': points_next_5,
            })

        # Create a DataFrame from the collected player data
        df = pd.DataFrame(all_player_data)

        # Sort the DataFrame by Position and Expected Points
        df_sorted = df.sort_values(by=['Expected Points'], ascending=[False])

        # Construct the output file path
        file_output_path = (f'combined_gw{gameweek}_data.csv')

        # Save the sorted DataFrame to a CSV file
        df_sorted.to_csv(file_output_path, index=False, mode='w')


fpl_predictor = FPLPredictor(
            fixtures_file='Fantasy-Premier-League-master/data/2023-24/fixtures.csv',
            player_id_file='Fantasy-Premier-League-master/data/2023-24/player_idlist.csv',
            players_raw_file='Fantasy-Premier-League-master/data/2023-24/players_raw.csv',
            folder_path='Fantasy-Premier-League-master/data/2023-24/gws'
        )
for gameweek in range(1, 39):
    fpl_predictor.combine_gw_data(gameweek)
    print("done "+ str(gameweek))
