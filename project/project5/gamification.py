def calculate_xp(sentiment_score, streak):
    base_xp = max(5, sentiment_score * 10)
    return base_xp * streak

def get_feedback(score):
    if score >= 4:
        return " Amazing discipline. You're building momentum."
    elif score >= 1:
        return " Solid effort. Progress beats perfection."
    else:
        return " Showing up still counts. Keep going."
