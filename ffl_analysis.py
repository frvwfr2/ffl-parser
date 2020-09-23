# gets FFL league info and does luck analysis

#%% 
import requests
import json
import operator
import itertools

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
    
    # types are actual, optimal, expected ?
    def get_record(self, type="actual"):
        pass

    # Print output
    def __repr__(self):
        #get avg score
        avg_score = 0
        weeks = 0
        for week, score in self.scores.items():
            weeks += 1
            avg_score += score
        avg_score = avg_score/weeks
        optimal_avg_score = 0
        weeks = 0
        for week, score in self.optimal_scores.items():
            weeks += 1
            optimal_avg_score += score
        optimal_avg_score = optimal_avg_score/weeks

        actual_record = f"({self.actual_w}-{self.actual_l}-{self.actual_t})"
        expected_record = f"{self.expected_w:.2f}-{self.expected_l:.2f}-{self.expected_t:.2f}"

        return f"{self.id:>3}. {self.abbrev:>5} {self.name:>30} {avg_score:>6.2f} ({optimal_avg_score:>6.2f}) {actual_record:>} // ({expected_record}) // {(self.actual_w-self.expected_w):>+4.2f}"

class League:
    def __init__(self, id, year):
        self.id = id
        # Dictionary of Teams, with Team_ID as the key ? 
        self.teams = dict()
        self.gather_raw_data()
        self.year = year

    def gather_raw_data(self):
        # League ID = 642470
        # Get League info and Matchup info
        r = requests.get(f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/{year}/segments/0/leagues/{league_id}?view=mSettings&view=mTeam&view=mMatchup")
        self.raw_league = r.json()
        with open("league.json", "w") as f:
            print(json.dumps(self.raw_league, indent=4), file=f)
        if "messages" in self.raw_league and self.raw_league["messages"][0]=="You are not authorized to view this League.":
            print("You are not authorized to view this league")


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
                print(team["id"])
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
                print(f"   {optimal_score:>6.2f}")
                self.teams[team["id"]].optimal_scores[scoring_period] = optimal_score

        # &view=mSettings to get legal positional listings
        # https://fantasy.espn.com/apis/v3/games/ffl/seasons/2020/segments/0/leagues/642470?view=mSettings

    def print_teams(self):
        # for student in (sorted(student_Dict.values(), key=operator.attrgetter('age'))):
        #     print(student.name)
        print(f'{"ID":>3}. {"ABBR":>5} {"Team name":>30} {"Avg":>6} ({"Optimal":>6}) {"Record":>} // ({"Expected"}) // {("Luck rating"):>}')
        for team in (sorted(self.teams.values(), reverse=True, key=operator.attrgetter('expected_w'))):
            print(team)
        # for index, team in self.teams.items():
        #     print(team)

    def get_expected_records(self):
        # Generate the weekly scores, as a list, with (teamID, score) formatted tuple
        weekly_scores = dict()
        # for each team in the league
        for index, team in self.teams.items():
            # for each week we have a score for
            for week, score in team.scores.items():
                if week not in weekly_scores:
                    weekly_scores[week] = list()
                weekly_scores[week].append( (team.id, score) )
        # For each week we have scores for 
        for week, scores in weekly_scores.items():
            # For 
            for a, b in itertools.combinations(weekly_scores[week], 2):
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
            # print(home_team, home_score, away_team, away_score)
            # break

        self.get_expected_records()
        # for k, v in self.teams.items():
        #     print(v)
        # print(self.teams)
        pass

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

if __name__ == "__main__":
    # run code
    matchups_file = ""
    # matchups_file = "D:/projects/current_matchups.json"
    league_file = "D:/projects/league_teams.json"
    league_id = "642470"
    year = 2020

    # if matchups_file:
    #     l = parse_league_info(league_file)
    #     d = open_league_json(matchups_file)
    # else:
    #     d, l = get_league_json(league_id, year)
    if True:
        league = League(league_id, year)
        # Gets the basic info, like current W/L, Expected W/L
        league.analyze_league_info()
        # Populates each team with the Optimal score of the week
        league.get_optimal_scores()
        league.print_teams()

