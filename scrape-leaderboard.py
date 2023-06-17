import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, date
import csv
import os.path


# Scrape leaderboard data
def scrape_leaderboard():
    # url = "https://www.beatthestreet.me/leicester/leaderboards/"
    url = "https://mb-4.com"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('table')
    rows = []
    if table:
        rows = [row for row in table.find_all('tr')]

    leaderboard_data = []
    for row in rows[1:]:
        position = int(row.find(class_="RowItemstyled__StyledRowRank-sc-p1yhdf-2 igbMLU").text.strip())
        player_id = row.find(class_="RowItemstyled__StyledRowName-sc-p1yhdf-3 lMvLm").text.strip()
        points = int(row.find(class_="RowItemstyled__StyledRowPoints-sc-p1yhdf-5 hJlYCQ").text.strip())

        leaderboard_data.append((position, player_id, points))

    return leaderboard_data


# Converts the number of points into distance (10 points == 500 meters)
def calculate_distance(points):
    return int((points / 10) * 5000)


# Checks if the player participated
def participation_check(points):
    return points > 0


# Main method / Start
def main():
    game_duration = 4
    current_date = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
    end_date = current_date + timedelta(weeks=game_duration)

    leaderboard = {}

    # Read existing data from the CSV file or initialize an empty leaderboard
    if os.path.isfile('leaderboard.csv'):
        with open('leaderboard.csv', 'r', newline='') as file:
            reader = csv.reader(file)
            rows = list(reader)
            player_ids = [row[1] for row in rows[1:]]
            for row in rows[1:]:
                player_id = row[1]
                points_by_day = row[2].split(' ')
                points = {}
                for i in range(0, len(points_by_day), 2):
                    try:
                        date = datetime.strptime(points_by_day[i], '%Y-%m-%d').date()
                        value = int(points_by_day[i + 1])
                        if value != 0:  # Only add non-zero points to the dictionary
                            points[date] = value
                    except ValueError:
                        # Handle unexpected date format or missing date
                        continue

                leaderboard[player_id] = {
                    'points': points,
                    'distance': calculate_distance(sum(points.values())),
                    'participation': participation_check(sum(points.values()))
                }

    while current_date < end_date:
        leaderboard_data = scrape_leaderboard()

        # Create a new dictionary to store the day-to-day points
        daily_points = {}

        for position, player_id, points in leaderboard_data:
            if player_id not in leaderboard:
                leaderboard[player_id] = {
                    'points': {},
                    'distance': 0,
                    'participation': False
                }

            if current_date.date() not in leaderboard[player_id]['points']:
                leaderboard[player_id]['points'][current_date.date()] = 0

            # Add the current day's points to the daily_points dictionary
            daily_points[player_id] = points

        # Update points only if it corresponds to the current day and if the new points are higher
        if current_date.date() == datetime.now().date():
            for player_id, points in daily_points.items():
                if points > leaderboard[player_id]['points'][current_date.date()]:
                    leaderboard[player_id]['points'][current_date.date()] = points

        current_date += timedelta(days=1)

    # Calculate cumulative points, distance, and participation
    for player_id, data in leaderboard.items():
        cumulative_points = sum(data['points'].values())
        data['distance'] = calculate_distance(cumulative_points)
        data['participation'] = participation_check(cumulative_points)

    # Updates leaderboard data in the CSV file
    try:
        with open('leaderboard.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Total Players', 'Player ID', 'Points by Day', 'Cumulative Points', 'Total Distance (m)',
                             'Participation'])
            total_players = len(leaderboard)

            for player_id, data in leaderboard.items():
                cumulative_points = sum(data['points'].values())
                total_distance = calculate_distance(cumulative_points)
                did_participate = participation_check(cumulative_points)
                points_by_day = [f"|{date.strftime('%Y-%m-%d')}:{points}| " for date, points in
                                 sorted(data['points'].items(), key=lambda x: x[0]) if points != 0]  # Filter out points with value 0
                row = [total_players, player_id, ' '.join(points_by_day), cumulative_points, total_distance,
                       did_participate]
                writer.writerow(row)

        print("Leaderboard data updated in leaderboard.csv\n")
    except Exception as e:
        print("An error has occurred.\n", e)


if __name__ == "__main__":
    main()
