import os
import json
import datetime
from github import Github

# Setup GitHub API
g = Github(os.environ.get("GITHUB_TOKEN"))
repo_name = os.environ.get("angelicaferriol/Daily-Blog") 
repo = g.get_repo("Daily-Blog")

# Check for existing streak data
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
except:
    # File doesn't exist yet, we'll create it
    pass

# Get all commits for the repository
commits = repo.get_commits()
commit_dates = []

for commit in commits:
    # Get date in YYYY-MM-DD format
    commit_date = commit.commit.author.date.strftime("%Y-%m-%d")
    commit_dates.append(commit_date)
    
    # Update daily commit count
    if commit_date in streak_data["daily_commits"]:
        streak_data["daily_commits"][commit_date] += 1
    else:
        streak_data["daily_commits"][commit_date] = 1

# Sort dates in descending order (newest first)
commit_dates.sort(reverse=True)

if commit_dates:
    streak_data["last_commit_date"] = commit_dates[0]
    
    # Calculate current streak
    current_streak = 0
    today = datetime.datetime.now().date()
    yesterday = today - datetime.timedelta(days=1)
    
    # Check if most recent commit is from today or yesterday to start counting streak
    most_recent_date = datetime.datetime.strptime(commit_dates[0], "%Y-%m-%d").date()
    
    if most_recent_date == today or most_recent_date == yesterday:
        current_date = most_recent_date
        current_streak = 1
        
        # Count backwards from most recent commit
        for i in range(1, 1000):  # 1000 is just a safe upper limit
            check_date = (most_recent_date - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            if check_date in commit_dates:
                current_streak += 1
            else:
                break
                
        streak_data["current_streak"] = current_streak
        
    # Calculate longest streak
    longest_streak = 0
    current_streak = 0
    
    # Sort dates in ascending order for streak calculation
    sorted_dates = sorted(set(commit_dates))
    
    for i in range(len(sorted_dates)):
        if i == 0:
            current_streak = 1
            continue
            
        # Check if dates are consecutive
        prev_date = datetime.datetime.strptime(sorted_dates[i-1], "%Y-%m-%d").date()
        curr_date = datetime.datetime.strptime(sorted_dates[i], "%Y-%m-%d").date()
        
        if (curr_date - prev_date).days == 1:
            current_streak += 1
        else:
            longest_streak = max(longest_streak, current_streak)
            current_streak = 1
            
    longest_streak = max(longest_streak, current_streak)
    streak_data["longest_streak"] = longest_streak

# Save updated streak data
updated_content = json.dumps(streak_data, indent=2)
try:
    repo.update_file(
        streak_data_path,
        "Update streak data",
        updated_content,
        streak_data_file.sha if 'streak_data_file' in locals() else None
    )
except:
    repo.create_file(
        streak_data_path,
        "Create streak data file",
        updated_content
    )

# Update README with streak information
try:
    readme = repo.get_contents("README.md")
    readme_content = readme.decoded_content.decode()
    
    # Create or update streak section in README
    streak_section = f"""

## 📅 Daily Commit Streak

**Current Streak:** {streak_data["current_streak"]} days  
**Longest Streak:** {streak_data["longest_streak"]} days  
**Last Commit:** {streak_data["last_commit_date"]}

<!-- Streak data updated by GitHub Actions -->
"""
    
    if "## 📅 Daily Commit Streak" in readme_content:
        # Replace existing section
        start_idx = readme_content.find("## 📅 Daily Commit Streak")
        end_idx = readme_content.find("<!-- Streak data updated by GitHub Actions -->", start_idx) + len("<!-- Streak data updated by GitHub Actions -->")
        
        new_readme = readme_content[:start_idx] + streak_section + readme_content[end_idx:]
    else:
        # Add section to the end
        new_readme = readme_content + "\n" + streak_section
        
    repo.update_file(
        "README.md",
        "Update streak information in README",
        new_readme,
        readme.sha
    )
except Exception as e:
    print(f"Error updating README: {e}")