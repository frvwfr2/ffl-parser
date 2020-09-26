# gets FFL league info and does luck analysis

#%% 
import requests
import json
import operator
import itertools
import matplotlib.pyplot as plt
import copy

class Team:
    # owners is a list
    def __init__(self, name, abbrev, owners, id):
        self.id = id
        self.owners = owners
        self.name = name
        self.abbrev = abbrev
        # Each key is the week it was scored during
        self.scores = dict()
        self.optimal_scores = dict()

        # Expected record
        self.expected_w = 0
        self.expected_l = 0
        self.expected_t = 0

        # Actual record
        self.actual_w = 0
        self.actual_l = 0
        self.actual_t = 0

        # Expected Optimal vs Actual record
        self.optimal_v_actual_w = 0
        self.optimal_v_actual_l = 0
        self.optimal_v_actual_t = 0

        # Expected Optimal vs Optimal record
        self.optimal_v_optimal_w = 0
        self.optimal_v_optimal_l = 0
        self.optimal_v_optimal_t = 0

    # This function needs to be in the League, and it should just calculate them all, and fill in the attributes
    # for each team
    def get_record(self, type="actual"):
        pass

    def get_avg_score(self):
        avg_score = 0
        weeks = 0
        for week, score in self.scores.items():
            weeks += 1
            avg_score += score
        return avg_score/weeks

    def get_avg_optimal_score(self):
        optimal_avg_score = 0
        weeks = 0
        for week, score in self.optimal_scores.items():
            weeks += 1
            optimal_avg_score += score
        return optimal_avg_score / weeks

    # Print output
    def __repr__(self):
        #get avg score
        avg_score = self.get_avg_score()
        optimal_avg_score = self.get_avg_optimal_score()
        avg_score_pct_diff = 100 * avg_score / optimal_avg_score

        actual_record = f"({self.actual_w}-{self.actual_l}-{self.actual_t})"
        expected_record = f"{self.expected_w:.2f}-{self.expected_l:.2f}-{self.expected_t:.2f}"

        return f"{self.id:>3}. {self.abbrev:>5} {self.name:>30} {avg_score:>6.2f} {optimal_avg_score:>6.2f} [{avg_score_pct_diff:>6.2f}%] {actual_record:>} // ({expected_record}) // {(self.actual_w-self.expected_w):>+4.2f} // {self.optimal_v_optimal_w:>4.2f} // {self.optimal_v_actual_w:>4.2f}"

class League:
    def __init__(self, id, year, league_file=None):
        self.id = id
        # Dictionary of Teams, with Team_ID as the key ? 
        self.teams = dict()
        if league_file is None:
            self.raw_league = self.gather_raw_data()
        else:
            with open(league_file) as f:
                self.raw_league = json.load(f)
        self.year = year

        self.analyze_league_info()
        self.get_optimal_scores()
        self.get_expected_records()

    def gather_raw_data(self):
        # League ID = 642470
        # Get League info and Matchup info
        r = requests.get(f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/{year}/segments/0/leagues/{league_id}?view=mSettings&view=mTeam&view=mMatchup")
        # self.raw_league = r.json()
        with open("league.json", "w") as f:
            print(json.dumps(r.json(), indent=4), file=f)
        if "messages" in r.json() and r.json()["messages"][0] == "You are not authorized to view this League.":
            print("You are not authorized to view this league\n")
        return r.json()

    def get_optimal_scores(self):
        players = []
        for week in range(1, self.current_scoring_period):
            print("week: ", week)
            scoring_period = week
            # scoring_period = 2
            r = requests.get(f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/{self.year}/segments/0/leagues/{self.id}?scoringPeriodId={scoring_period}&view=mRoster")
            weekly_rosters = r.json()
            with open("rosters.json", "w") as f:
                print(json.dumps(weekly_rosters, indent=4), file=f)

            for team in weekly_rosters['teams']:
                # print(team["id"])
                for entry in team["roster"]["entries"]:
                    eligible = list()
                    # if entry["playerId"] == 4047365:
                    for slot in entry["playerPoolEntry"]["player"]["eligibleSlots"]:
                        eligible.append(slot)
                    for stat in entry["playerPoolEntry"]["player"]["stats"]:
                        if stat["seasonId"] == 2020 and stat["scoringPeriodId"] == scoring_period and stat["statSourceId"] == 0:
                            players.append(Player(entry["playerId"], entry["playerPoolEntry"]["player"]["fullName"], stat["appliedTotal"], eligible))
                            # print(f'{stat["appliedTotal"]:<6.2f} {entry["playerPoolEntry"]["player"]["fullName"]:>30} {eligible}')
                            # print(json.dumps(stat, indent=4))
                total_slots = []
                for slot, count in self.lineupSlotCounts.items():
                    for i in range(count):
                        total_slots.append(int(slot))
                # print(total_slots)
                    # print(slot * count)
                    # total_slots.append()
                optimal_score = 0
                for slot in total_slots:
                    curr_high_score = 0
                    curr_high_player = None
                    for player in players:
                        if slot in player.eligibleSlots:
                            if player.score > curr_high_score:
                                curr_high_player = player
                                curr_high_score = player.score
                    # If we did find a player to use
                    if curr_high_player is not None:
                        # print(f"{slot:>2} {curr_high_player}")
                        optimal_score += curr_high_player.score
                        players.remove(curr_high_player)
                    # No player found
                    else:
                        pass
                        # print(f'{slot:>2} {0:<6.2f} {"None":>30}')
                # print(f"   {optimal_score:>6.2f}")
                self.teams[team["id"]].optimal_scores[scoring_period] = optimal_score

        # &view=mSettings to get legal positional listings
        # https://fantasy.espn.com/apis/v3/games/ffl/seasons/2020/segments/0/leagues/642470?view=mSettings

    def print_teams(self):
        # for student in (sorted(student_Dict.values(), key=operator.attrgetter('age'))):
        #     print(student.name)
        print(f'{"ID":>3}. {"ABBR":>5} {"Team name":>30} {"Avg":>6} {"Optimal":>6} [{"Pct":>6}] {"Record":>} // ({"Expected"}) // {("Luck rating"):>} // {"Exp W if everyone played perfect // Exp W if this team played perfect"}')
        for team in (sorted(self.teams.values(), reverse=True, key=operator.attrgetter('expected_w'))):
            print(team)
        # for index, team in self.teams.items():
        #     print(team)

    def get_expected_records(self):
        # expected, optimal_vs_optimal, optimal_vs_actual
        # Each key in weekly_scores is a week of scores, value is list of tupes (teamID, score)
        weekly_scores = {'actual': dict(),
                        'optimal': dict()}
        # Build up the weekly_scores dict
        # for each team in the league
        for index, team in self.teams.items():
            # for each week we have a score for
            for week, score in team.scores.items():
                # If the week index doesnt exist yet, put it in there
                if week not in weekly_scores['actual']:
                    weekly_scores['actual'][week] = list()
                # Add this (team.id, score), to the weekly_scores for this week
                weekly_scores['actual'][week].append( (team.id, score) )
            for week, optimal in team.optimal_scores.items():
                if week not in weekly_scores['optimal']:
                    weekly_scores['optimal'][week] = list()
                # Add this (team.id, score), to the weekly_scores for this week
                weekly_scores['optimal'][week].append( (team.id, optimal) )
        # For each week we have scores for 
        # week 1 scores
        # List of team IDs
        for week, scores in weekly_scores['actual'].items():
            # For every possible matchup combination...
            for a, b in itertools.combinations(weekly_scores['actual'][week], 2):
                team_a = self.teams[a[0]]
                team_b = self.teams[b[0]]
                if (a[1] > b[1]):
                    # print("A won")
                    team_a.expected_w += 1/(len(self.teams)-1)
                    team_b.expected_l += 1/(len(self.teams)-1)
                if (b[1] > a[1]):
                    team_b.expected_w += 1/(len(self.teams)-1)
                    team_a.expected_l += 1/(len(self.teams)-1)
                if (a[1] == b[1]):
                    team_a.expected_t += 1/(len(self.teams)-1)
                    team_b.expected_t += 1/(len(self.teams)-1)
                # print(a, b)
        print(weekly_scores['optimal'])
        for week, optimals in weekly_scores['optimal'].items():
            for a, b in itertools.combinations(weekly_scores['optimal'][week], 2):
                team_a = self.teams[a[0]]
                team_b = self.teams[b[0]]
                if (a[1] > b[1]):
                    # print("A won")
                    team_a.optimal_v_optimal_w += 1/(len(self.teams)-1)
                    team_b.optimal_v_optimal_l += 1/(len(self.teams)-1)
                if (b[1] > a[1]):
                    team_b.optimal_v_optimal_w += 1/(len(self.teams)-1)
                    team_a.optimal_v_optimal_l += 1/(len(self.teams)-1)
                if (a[1] == b[1]):
                    team_a.optimal_v_optimal_t += 1/(len(self.teams)-1)
                    team_b.optimal_v_optimal_t += 1/(len(self.teams)-1)
        # Copy the weekly scores, so we can compare optimal vs actual
        for id, team in self.teams.items():
            # print(team)
            for week, scores in weekly_scores['actual'].items():
                team_optimal_score = team.optimal_scores[week]
                # print(team_optimal_score)
                for score in scores:
                    # If the team id is the one we are comparing, ignore this one
                    if score[0] == team.id:
                        pass
                    else:
                        # If this team scored higher, add 1 to W's
                        if team_optimal_score > score[1]:
                            team.optimal_v_actual_w += 1/(len(self.teams)-1)
                        # If this team scored lower, add 1 to L's
                        elif team_optimal_score < score[1]:
                            team.optimal_v_actual_l += 1/(len(self.teams)-1)
                        else:
                            team.optimal_v_actual_t += 1/(len(self.teams)-1)
            # print(cp_weekly_scores)
                # print(a, b)

        # For each team
        # for team in self.teams:
            # Create a copy of the weekly scores
        #     cp_weekly_scores = copy.deepcopy(weekly_scores)

        # Using this Editable object, modify it to have each team's Optimal scores. After each team is compared, reset the whole dict to the original.

        # Need another loop for each team, replace that team's value with their optimal, and run the same comparison
        # Then we need to replace every team with Optimal, and run the same comparison again
        # print(weekly_scores)
        pass

    def analyze_league_info(self):
        self.name = self.raw_league["settings"]["name"]
        self.current_scoring_period = self.raw_league["scoringPeriodId"]
        self.lineupSlotCounts = self.raw_league["settings"]["rosterSettings"]["lineupSlotCounts"]
        # Remove slot 20, as that is the bench
        self.lineupSlotCounts.pop("20", None)
        print(f"League name: {self.name}")
        members_dict = dict()
        for member in self.raw_league["members"]:
            members_dict[member["id"]] = member["displayName"]
        # print(members_dict)

        for team in self.raw_league["teams"]:
            team_name = team["location"] + " " + team["nickname"]
            team_owners = team["owners"]
            team_id = team["id"]
            team_abbrev = team["abbrev"]

            t = Team(team_name, team_abbrev, team_owners, team_id)
            self.teams[team_id] = t
            # teams_dict[team_name] = members_dict[team["owners"][0]]

        for matchup in self.raw_league["schedule"]:
            matchup_period = matchup["matchupPeriodId"]
            winner = matchup["winner"]
            # print(matchup)
            # If this matchup isn't decided, don't try to get scoring info
            if winner == "UNDECIDED":
                pass
                # print("skipping bc undecided")
            else:
                # print("Parsing week")
                home = matchup["home"]
                away = matchup["away"]
                home_team_id = home["teamId"]
                home_score = home["pointsByScoringPeriod"][str(matchup_period)]
                away_team_id = away["teamId"]
                away_score = away["pointsByScoringPeriod"][str(matchup_period)]
                home_team = self.teams[home_team_id]
                home_team.scores[matchup_period] = home_score
                away_team = self.teams[away_team_id]
                away_team.scores[matchup_period] = away_score

                if home_score > away_score:
                    home_team.actual_w += 1
                    away_team.actual_l += 1
                elif away_score > home_score:
                    away_team.actual_w += 1
                    home_team.actual_l += 1
                elif away_score == home_score:
                    away_team.actual_t += 1
                    home_team.actual_t += 1


    def calculate_records(self):
        pass

    def show_scores_chart(self):
        #### CHART STUFF IS BELOW ####
        # Get the list of avg scores, ordered by... Team ID
        # Get the list of optimal scores, ordered by Team ID
        avgs = []
        optimals = []
        team_names = []
        for team in self.teams:
            team_names.append(self.teams[team].name)
            avgs.append(self.teams[team].get_avg_score())
            optimals.append(self.teams[team].get_avg_optimal_score())
        # print(team_names, avgs, optimals)

        width = .8
        plt.style.use('dark_background')
        plt.bar(team_names, avgs, width=.8*width, color='tab:gray', label="Avg")
        plt.bar(team_names, optimals, width=.5*width, color='tab:red', label="Optimal")
        plt.subplots_adjust(left=0.2)

        plt.legend()
        # plt.tight_layout()
        plt.xticks(
            rotation=45,
            horizontalalignment='right',
            fontweight='light',
            fontsize='x-large'
        )

        # Call the function above, to add numeric labels to each bar
        ax = plt.gca()

        add_value_labels(ax)
        plt.title('Team Scores')
        plt.show()

    def show_records_chart(self):
        actuals = []
        expected = []
        optimals_v_optimals = []
        optimals_v_actuals = []
        team_names = []
        luck_values = []
        for team in (sorted(self.teams.values(), reverse=False, key=operator.attrgetter('actual_w'))):
            team_names.append(team.name)
            actuals.append(team.actual_w)
            optimals_v_optimals.append(team.optimal_v_optimal_w)
            optimals_v_actuals.append(team.optimal_v_actual_w)
            expected.append(team.expected_w)
            luck_values.append(team.actual_w - team.expected_w)

        
        height = .8
        # plt.style.use('dark_background')
        # Need to go from best to worst
        plt.barh(team_names, expected, height=.8*height, color="tab:purple", label="Expected")
        plt.barh(team_names, optimals_v_actuals, height=.5*height, color="tab:blue", label="Optimal v Actual")
        plt.barh(team_names, optimals_v_optimals, height=.5*height, color="tab:green",label="Optimal v Optimal")
        plt.barh(team_names, actuals, height=.8*height, label="Actual", fc=(0, 0, 0, 0), lw=3, ls="-", edgecolor="black")
        # plt.barh(team_names, luck_values, height=.1*height, label="Luck Rating", color="white", left=expected, alpha=.5)
        # plt.subplots_adjust(bottom=0.3)

        plt.legend()
        # plt.tight_layout()
        plt.xticks(
            rotation=45,
            horizontalalignment='right',
            fontweight='light',
            fontsize='x-large'
        )

        # Call the function above, to add numeric labels to each bar
        ax = plt.gca()
        add_value_labels(ax, spacing=15, hv='h')
        plt.title('Team Win Counts')
        plt.show()

        
class Player:
    def __init__(self, id, name, score, eligibleSlots):
        self.id = id
        self.name = name
        self.score = score
        self.eligibleSlots = eligibleSlots
    
    def __repr__(self):
        return f'{self.score:>6.2f} {self.name:>30} {self.eligibleSlots}'


def analyze_matchups(d):
    pass
    # league_name


def add_value_labels(ax, spacing=5, hv='v'):
    """Add labels to the end of each bar in a bar chart.

    Arguments:
        ax (matplotlib.axes.Axes): The matplotlib object containing the axes
            of the plot to annotate.
        spacing (int): The distance between the labels and the bars.
        hv ('h' or 'v'): Whether this is a horizontal or vertical barchart
    """

    # For each bar: Place a label
    for rect in ax.patches:
        # Get X and Y placement of label from rect.
        y_value = rect.get_height()
        x_value = rect.get_x() + rect.get_width() / 2
        # If it's a vertical bar chart...
        if hv == 'v':
            y_value = rect.get_height()
            x_value = rect.get_x() + rect.get_width() / 2
            # Vertical alignment for positive values
            va = 'bottom'

            # If value of bar is negative: Place label below bar
            if y_value < 0:
                # Invert space to place label below
                space *= -1
                # Vertically align label at top
                va = 'top'

            # Use Y value as label and format number with one decimal place
            label = "{:.2f}".format(y_value)
                    # Number of points between bar and label. Change to your liking.
            space = spacing


            # Create annotation
            ax.annotate(
                label,                      # Use `label` as label
                (x_value, y_value),         # Place label at end of the bar
                xytext=(0, space),          # Vertically shift label by `space`
                textcoords="offset points", # Interpret `xytext` as offset in points
                ha='center',                # Horizontally center label
                va=va)                      # Vertically align label differently for
                                            # positive and negative values.
        # If it's a horizontal bar chart
        elif hv == 'h':
            y_value = rect.get_y() + rect.get_height() / 2
            x_value = rect.get_width()

            # Vertical alignment for positive values
            va = 'center'

            # If value of bar is negative: Place label below bar
            if x_value < 0:
                # Invert space to place label below
                space *= -1
                # Vertically align label at top
                va = 'center'

            # Use Y value as label and format number with one decimal place
            label = "{:.2f}".format(x_value)
                    # Number of points between bar and label. Change to your liking.
            space = spacing


            # Create annotation
            ax.annotate(
                label,                      # Use `label` as label
                (x_value, y_value),         # Place label at end of the bar
                xytext=(space, 0),          # Horizontally shift label by `space`
                textcoords="offset points", # Interpret `xytext` as offset in points
                ha='center',                # Horizontally center label
                va=va)                      # Vertically align label differently for
                                            # positive and negative values.




if __name__ == "__main__":
    # run code
    matchups_file = ""
    # matchups_file = "D:/projects/current_matchups.json"
    # league_file = "D:/projects/league_teams.json"
    league_id = "642470" # Lindsay's league
    # league_id = "252353" # 
    year = 2020

    # if matchups_file:
    #     l = parse_league_info(league_file)
    #     d = open_league_json(matchups_file)
    # else:
    #     d, l = get_league_json(league_id, year)
    if True:
        league = League(league_id, year)
        # Gets the basic info, like current W/L, Expected W/L
        league.print_teams()
        # league.show_scores_chart()
        plt.rcParams.update(plt.rcParamsDefault)
        league.show_records_chart()
        # Plot them overlapping
