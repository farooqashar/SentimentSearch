import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from RealtimeSTT import AudioToTextRecorder
import os
from PIL import Image
from PIL.ExifTags import TAGS
from datetime import datetime
from deepface import DeepFace


## SPEECH TO TEXT ##
def extract_query_info(text):
    """
    Extract emotion category and timeframe from the user-spoken text
    """

    text = text.lower()
    analyzer = SentimentIntensityAnalyzer()
    sentiment = analyzer.polarity_scores(text)

    # Determine sentiment category of what the user said
    if sentiment['compound'] >= 0.3:
        emotion_category = "positive"
    elif sentiment['compound'] <= -0.3:
        emotion_category = "negative"
    else:
        emotion_category = "neutral"

    # Search for month
    months = [ "january", "february", "march", "april", "may", "june",
               "july", "august", "september", "october", "november", "december" ]

    # Find the month if it appears in what the user says
    found_month = next((month for month in months if month in text), None)

    # Use regex to find 4-digit year
    year_match = re.search(r"\b(20\d{2}|19\d{2})\b", text)
    found_year = int(year_match.group(1)) if year_match else None

    # Detect "top N"
    top_n = 3  # default fallback of top 3 outputs to the user
    match = re.search(r"top\s+(\d+)", text)
    if match:
        top_n = int(match.group(1))
    else:
        # Try matching number words
        for word in text.split():
            if word in {"one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"}:
                if "top" in text:
                    top_n = word_to_number(word)
                    break

    return emotion_category, found_month, found_year, top_n

def word_to_number(word):
    """
    Converts a word numeric to an actual numberic
    """
    number_words = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
    }
    return number_words.get(word.lower(), None)

## PROCESSING IMAGES ##
def get_image_date(image_path):
    """
    Extract EXIF capture date
    """
    try:
        img = Image.open(image_path)
        exif_data = img._getexif()
        if not exif_data:
            return None
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            if tag == "DateTimeOriginal":
                return datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
    except Exception as e:
        print(f"⚠️ Could not get date from {image_path}: {e}")
    return None

def filter_images_by_date(folder, target_month, target_year):
    """
    Filter images by month and year
    """
    matching_images = []
    for fname in os.listdir(folder):
        if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
            continue

        path = os.path.join(folder, fname)
        date = get_image_date(path)
        if date:
            if (date.strftime('%B').lower() == target_month.lower() and date.year == target_year):
                matching_images.append(path)
        else:
            # If not date was found for the image, we will consider it part of what could be returned to user
            matching_images.append(path)

    return matching_images

## EMOTION DETECTION ##

# Map DeepFace emotions to high-level sentiment categories
emotion_map = {
    "happy": "positive",
    "surprise": "positive",
    "neutral": "neutral",
    "sad": "negative",
    "angry": "negative",
    "fear": "negative",
    "disgust": "negative"
}

def filter_images_by_emotion(image_paths, desired_category, top_n=3):
    """
    Detecting dominant emotion in images and collecting top n matching images
    """
    scored_images = []

    for path in image_paths:
        print(f"🖼️ Analyzing: {os.path.basename(path)}")
        try:
            result = DeepFace.analyze(img_path=path, actions=["emotion"], enforce_detection=False)
            emotion_scores = result[0]["emotion"]  # dictionary of emotion: score
            dominant_emotion = result[0]["dominant_emotion"].lower()

            # Get overall sentiment category of dominant emotion
            mapped_category = emotion_map.get(dominant_emotion, "neutral")

            if mapped_category == desired_category:
                # Score = confidence in the matching emotion category
                relevant_emotions = [k for k, v in emotion_map.items() if v == desired_category]
                strength_score = sum(emotion_scores.get(e, 0) for e in relevant_emotions)

                scored_images.append({
                    "path": path,
                    "dominant": dominant_emotion,
                    "score": strength_score
                })

                print(f"   → Detected: {dominant_emotion} | Score: {strength_score:.2f}")

        except Exception as e:
            print(f"   ❌ Error analyzing {path}: {e}")

    # Sort images by strength score (descending)
    top_images = sorted(scored_images, key=lambda x: x["score"], reverse=True)

    return top_images[:top_n]

## PROCESSING LOGIC FLOW ##
def process_logic(text):
    """
    Wrapper logic function to manage the flow and provide feedback to the user
    """
    print("\n📝 You said:", text)

    emotion_category, month, year, top_n = extract_query_info(text)

    # Show results to the user
    match emotion_category:
        case "positive":
            print("😄 Sentiment detected: POSITIVE (happy, joyful, etc.)")
        case "negative":
            print("😞 Sentiment detected: NEGATIVE (sad, angry, etc.)")
        case _:
            print("😐 Sentiment detected: NEUTRAL")

    if month and year:
        print(f"📆 Timeframe detected: {month.title()} {year}")
    elif month:
        print(f"📆 Month detected: {month.title()} (year missing)")
    elif year:
        print(f"📆 Year detected: {year} (month missing)")
    else:
        print("📆 No clear date found.")

    print(f"🏆 Top {top_n} results requested")

    print("\n✅ Ready to search for matching photos based on sentiment and timeframe...\n")

    folder = "images"
    filtered_images = filter_images_by_date(folder, month, year)

    print(f"\n📂 Found {len(filtered_images)} images from {month.title()} {year}:")
    for f in filtered_images:
        print(" -", f)

    top_emotion_results = filter_images_by_emotion(filtered_images, emotion_category, top_n)

    print(f"\n✅ Top {top_n} {emotion_category} images:")
    for r in top_emotion_results:
        print(f" - {r['path']} (Score: {r['score']:.2f}, Emotion: {r['dominant']})")

if __name__ == '__main__':
    print("🎉 Welcome to SentimentSearch!")
    print("🎤 Please wait for the prompt, then speak your query.")
    print("💬 Try something like: 'Show me the top 4 not fun pictures from January 2022'\n")

    recorder = AudioToTextRecorder()
    recorder.text(process_logic)
