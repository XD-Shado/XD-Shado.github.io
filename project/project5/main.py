
import json
from sentiment import analyze_sentiment
from gamification import calculate_xp, get_feedback

DATA_FILE = "data.json"

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"xp": 0, "streak": 1}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def main():
    data = load_data()

    print("\nSMART HABIT TRACKER")
    reflection = input("Write your habit reflection:\n> ")

    score = analyze_sentiment(reflection)
    earned_xp = calculate_xp(score, data["streak"])

    data["xp"] += earned_xp
    data["streak"] += 1

    save_data(data)

    print("\nFeedback:", get_feedback(score))
    print(f"XP Earned: {earned_xp}")
    print(f"Total XP: {data['xp']}")
    print(f"Current Streak: {data['streak']} days")

if __name__ == "__main__":
    main()
