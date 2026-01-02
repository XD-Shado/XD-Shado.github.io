def analyze_sentiment(text):
    positive_words = ["good", "great", "proud", "tried", "showed up", "progress"]
    negative_words = ["bad", "hate", "lazy", "tired"]

    score = 0
    text = text.lower()

    for word in positive_words:
        if word in text:
            score += 2

    for word in negative_words:
        if word in text:
            score -= 1

    return score
