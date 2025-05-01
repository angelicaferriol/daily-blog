import os
import json
import datetime
import re
from github import Github

# Setup GitHub API
g = Github(os.environ.get("GITHUB_TOKEN"))
repo_name = os.environ.get("angelicaferriol/Daily-Blog")
repo = g.get_repo(repo_name)

# Load or initialize streak data
streak_data_path = "streak_data.json"
streak_data = {
    "current_streak": 0,
    "longest_streak": 0,
    "last_commit_date": "",
    "daily_commits": {}
}

try:
    streak_data_file = repo.get_contents(streak_data_path)
    streak_data = json.loads(streak_data_file.decoded_content.decode())
except Exception:
    streak_data_file = None  # Means file doesn't exist yet

# Fetch commit dates
commit_dates = []
commits = repo.get_commits()
for commit in commits:
    date_str = commit.commit.author.date.strftime("%Y-%m-%d")
    commit_dates.append(date_str)
    streak_data["daily_commits"][date_str] = streak_data["daily_commits"].get(date_str, 0) + 1

commit_dates = sorted(set(commit_dates))
if not commit_dates:
    print("No commits found.")
    exit(0)

# Update last commit date
streak_data["last_commit_date"] = commit_dates[-1]

# Calculate current streak
today = datetime.datetime.now().date()
yesterday = today - datetime.timedelta(days=1)
most_recent_date = datetime.datetime.strptime(commit_dates[-1], "%Y-%m-%d").date()

streak_data["current_streak"] = 0
if most_recent_date in [today, yesterday]:
    streak = 1
    for i in range(1, 1000):
        check_date = most_recent_date - datetime.timedelta(days=i)
        if check_date.strftime("%Y-%m-%d") in commit_dates:
            streak += 1
        else:
            break
    streak_data["current_streak"] = streak

# Calculate longest streak
longest_streak = 1
current_streak = 1
for i in range(1, len(commit_dates)):
    prev = datetime.datetime.strptime(commit_dates[i - 1], "%Y-%m-%d").date()
    curr = datetime.datetime.strptime(commit_dates[i], "%Y-%m-%d").date()
    if (curr - prev).days == 1:
        current_streak += 1
    else:
        longest_streak = max(longest_streak, current_streak)
        current_streak = 1
longest_streak = max(longest_streak, current_streak)
streak_data["longest_streak"] = longest_streak

# Save streak_data.json
streak_json = json.dumps(streak_data, indent=2)
if streak_data_file:
    repo.update_file(streak_data_path, "Update streak data", streak_json, streak_data_file.sha)
else:
    repo.create_file(streak_data_path, "Create streak data file", streak_json)

# Update README.md
try:
    readme = repo.get_contents("README.md")
    content = readme.decoded_content.decode()

    # Create new streak section
    streak_section = f"""<!-- STREAK-START -->
## 📅 Daily Commit Streak

**Current Streak:** {streak_data["current_streak"]} days  
**Longest Streak:** {streak_data["longest_streak"]} days  
**Last Commit:** {streak_data["last_commit_date"]}

<!-- STREAK-END -->"""

    pattern = r"<!-- STREAK-START -->(.*?)<!-- STREAK-END -->"
    if re.search(pattern, content, flags=re.DOTALL):
        new_content = re.sub(pattern, streak_section, content, flags=re.DOTALL)
    else:
        new_content = content.strip() + "\n\n" + streak_section

    if new_content != content:
        repo.update_file("README.md", "Update streak information", new_content, readme.sha)

except Exception as e:
    print(f"README update failed: {e}")