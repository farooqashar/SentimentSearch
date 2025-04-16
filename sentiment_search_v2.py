import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from RealtimeSTT import AudioToTextRecorder
import os
from PIL import Image
from PIL.ExifTags import TAGS
from datetime import datetime
from deepface import DeepFace
import json
import cv2
import threading

## GLOBAL EVALUATION TRACKERS ##
total_speech_to_text_accuracy = 0
total_image_retrieval_accuracy = 0
num_queries = 0


# CUSTOM BLENDED EMOTIONS
complex_emotion_map = {
        "goofy": ["happy", "surprise", "neutral"],
        "goofiest": ["happy", "surprise", "neutral"],
        "silly": ["happy", "surprise"],
        "melancholy": ["sad", "neutral"],
        "nostalgia": ["surprise", "neutral", "happy", "sad"]
    }


## CACHING ##
def load_cache(cache_file="emotion_cache.json"):
    """
    Load a simple image analysis cache
    """
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            return json.load(f)
    return {}

def save_cache(cache, cache_file="emotion_cache.json"):
    """
    Save a simple cache"""
    with open(cache_file, "w") as f:
        json.dump(cache, f, indent=2)


## SPEECH TO TEXT ##
def extract_query_info(text):
    """
    Extract emotion category and timeframe from the user-spoken text
    """

    text = text.lower()
    analyzer = SentimentIntensityAnalyzer()
    sentiment = analyzer.polarity_scores(text)

    deepface_emotions = [
        "happy", "sad", "angry", "surprise", "fear", "disgust", "neutral"
    ]

    # Extract keyword or blended emotion
    words = text.split()
    detected_emotion = "neutral"
    for word in words:
        if word in complex_emotion_map or word in deepface_emotions:
            detected_emotion = word
            break

    # Checking for any negation
    if any(neg in text for neg in ["not", "no", "never"]):
        detected_emotion = "neutral"

    # Fallback to sentiment polarity for general happy vs sad categories of emotion
    if detected_emotion == "neutral":
        compound = sentiment["compound"]
        if compound >= 0.3:
            detected_emotion = "happy"
        elif compound <= -0.3:
            detected_emotion = "sad"

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

    return detected_emotion, found_month, found_year, top_n

def word_to_number(word):
    """
    Converts a word numeric to an actual numberic
    """
    number_words = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
    }
    return number_words.get(word.lower(), None)

## EVALUATION OF SPEECH TO TEXT
def confirm_and_evaluate_parsing(emotion_category, month, year, top_n):
    print("\n🔍 Evaluation Time For Speech To Text:")
    print("Please confirm the following parsed values:")

    ground_truth = {}
    ground_truth['emotion'] = input(f"→ Was the emotion '{emotion_category}' correct? (enter 'yes' or 'no'): ").strip().lower()
    ground_truth['month'] = input(f"→ Was the month '{month}' correct? (enter 'yes' or 'no'): ").strip().lower()
    ground_truth['year'] = input(f"→ Was the year '{year}' correct? (enter 'yes' or 'no'): ").strip().lower()
    ground_truth['top_n'] = input(f"→ Was the top_n value '{top_n}' correct? (enter 'yes' or 'no'): ").strip().lower()

    correct = 0
    total = 4

    if ground_truth['emotion'] == "yes": correct += 1
    if ground_truth['month'] == "yes": correct += 1
    if ground_truth['year'] == "yes": correct += 1
    if ground_truth['top_n'] == "yes": correct += 1

    accuracy = (correct / total) * 100
    print(f"\n📊 Speech To Text Parsing Accuracy: {accuracy:.2f}%")
    return accuracy


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

def filter_images_by_emotion(image_paths, desired_emotion, top_n=3):
    """
    Detecting dominant emotion in images and collecting top n matching images
    """
    cache = load_cache()

    scored_images = []
    expected_emotions = complex_emotion_map.get(desired_emotion, [desired_emotion])

    for path in image_paths:
        print(f"🖼️ Analyzing: {os.path.basename(path)}")
        path_key = os.path.abspath(path)
        try:
            if path_key in cache:
                result = cache[path_key]
                print("↪ Using cached result")
            else:
                result = DeepFace.analyze(img_path=path, actions=["emotion"], enforce_detection=False)
                cache[path_key] = result


            emotion_scores = result[0]["emotion"]  # dictionary of emotion: score
            dominant_emotion = result[0]["dominant_emotion"].lower()

            # Score based on how well image matches desired emotional blend
            relevant_score = sum(emotion_scores.get(e, 0) for e in expected_emotions)

            if relevant_score > 0:
                scored_images.append({
                    "path": path,
                    "dominant": dominant_emotion,
                    "score": relevant_score
                })

                print(f"→ Detected: {dominant_emotion} | Score: {relevant_score:.2f}")

        except Exception as e:
            print(f"❌ Error analyzing {path}: {e}")

    save_cache(cache)

    # Sort images by strength score (descending)
    top_images = sorted(scored_images, key=lambda x: x["score"], reverse=True)

    return top_images[:top_n]

## PROCESSING LOGIC FLOW ##

# EVALUATION FOR IMAGE RETRIEVAL SENTIMENT MATCHES #
def show_images_with_feedback(image_results, expected_emotion):
    correct = 0
    for r in image_results:
        img = cv2.imread(r["path"])

        fixed_width = 800
        height, width = img.shape[:2]
        scale = fixed_width / width
        new_dims = (fixed_width, int(height * scale))
        img = cv2.resize(img, new_dims)

        label = f"{os.path.basename(r['path'])} ({r['dominant']} - {r['score']:.2f})"
        cv2.imshow(label, img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

        feedback = input(f"✅ Does this image match '{expected_emotion}' sentiment? (yes/no): ").strip().lower()
        if feedback == "yes":
            correct += 1

    accuracy = (correct / len(image_results)) * 100 if image_results else 0
    print(f"\n🧪 Emotion Matching Photos Retrieval Accuracy: {accuracy:.2f}%")
    return accuracy

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

    speech_to_text_accuracy = confirm_and_evaluate_parsing(emotion_category, month, year, top_n)

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

    image_retrieval_accuracy = None
    if top_emotion_results:
        print("\n🖼️ Displaying top results...")
        image_retrieval_accuracy = show_images_with_feedback(top_emotion_results, emotion_category)
    else:
        print("⚠️ No matching images to display.")

    return speech_to_text_accuracy, image_retrieval_accuracy

if __name__ == '__main__':
    print("🎉 Welcome to SentimentSearch!")
    print("🎤 Please wait for the prompt, then speak your query.")
    print("💬 Try something like: 'Show me the top 4 not negative pictures from February of 2025'\n")

    recorder = AudioToTextRecorder()

    while True:
        done_event = threading.Event()

        def wrapped_process_logic(text):
            global total_speech_to_text_accuracy, total_image_retrieval_accuracy, num_queries

            speech_acr, image_acr = process_logic(text)

            total_speech_to_text_accuracy += speech_acr
            total_image_retrieval_accuracy += image_acr
            num_queries += 1

            done_event.set()

        # Wait Until The Logic Has Been Processed Before Asking The User For Potentially Another Query
        recorder.text(wrapped_process_logic)
        done_event.wait()

        cont = input("\n🔁 Do you want to try another query? (yes/no): ").strip().lower()
        if cont not in ["yes", "y"]:
            if num_queries != 0:
                avg_speech_to_text_acr = total_speech_to_text_accuracy / num_queries
                avg_img_acr = total_image_retrieval_accuracy / num_queries
                print(f"\n📊 Session Summary:")
                print(f"• Average Speech To Text Parsing Accuracy: {avg_speech_to_text_acr:.2f}%")
                print(f"• Average Image Sentiment Matching Accuracy: {avg_img_acr:.2f}%")
                print("👋 Goodbye! Thanks for using SentimentSearch.")
            break
