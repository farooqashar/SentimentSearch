import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from RealtimeSTT import AudioToTextRecorder
import os
from PIL import Image
from PIL.ExifTags import TAGS
from datetime import datetime

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

    return emotion_category, found_month, found_year


def process_text(text):
    """
    Wrapper logic function to process the text that the user spoke with feedback
    """
    print("\n📝 You said:", text)

    emotion_category, month, year = extract_query_info(text)

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

    print("\n✅ Ready to search for matching photos based on sentiment and timeframe...\n")


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
    return matching_images

if __name__ == '__main__':
    print("🎉 Welcome to SentimentSearch!")
    print("🎤 Please wait for the prompt, then speak your query.")
    print("💬 Try something like: 'Show me the not fun pictures from January 2022'\n")

    recorder = AudioToTextRecorder()
    recorder.text(process_text)
