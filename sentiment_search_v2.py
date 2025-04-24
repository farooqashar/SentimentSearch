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
from util import complex_emotion_map

## CONFIGURATION ##
debug = True
session_log_path = "session_results_v2.jsonl"
open(session_log_path, "w").close()  # Clear log file each session

def debug_print(*args, **kwargs):
    if debug:
        print(*args, **kwargs)

## CACHING ##
def load_cache(cache_file="emotion_cache_v2.json"):
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            return json.load(f)
    return {}

def save_cache(cache, cache_file="emotion_cache_v2.json"):
    with open(cache_file, "w") as f:
        json.dump(cache, f, indent=2)

## LOGGING ##
def log_prediction(entry_type, input_data, predicted, expected=None, path=session_log_path):
    with open(path, "a") as f:
        json.dump({
            "type": entry_type,
            "input": input_data,
            "predicted": predicted,
            "expected": expected
        }, f)
        f.write("\n")

## SPEECH PARSING ##
def extract_query_info(text):
    text = text.lower()
    analyzer = SentimentIntensityAnalyzer()
    sentiment = analyzer.polarity_scores(text)

    deepface_emotions = ["happy", "sad", "angry", "surprise", "fear", "disgust", "neutral"]

    words = text.split()
    detected_emotion = "neutral"
    for word in words:
        if word in complex_emotion_map or word in deepface_emotions:
            detected_emotion = word
            break

    if any(neg in text for neg in ["not", "no", "never"]):
        detected_emotion = "neutral"

    if detected_emotion == "neutral":
        compound = sentiment["compound"]
        if compound >= 0.3:
            detected_emotion = "happy"
        elif compound <= -0.3:
            detected_emotion = "sad"

    months = [
        "january", "february", "march", "april", "may", "june",
        "july", "august", "september", "october", "november", "december"
    ]
    found_month = next((month for month in months if month in text), None)

    year_match = re.search(r"\b(20\d{2}|19\d{2})\b", text)
    found_year = int(year_match.group(1)) if year_match else None

    top_n = 3
    match = re.search(r"top\s+(\d+)", text)
    if match:
        top_n = int(match.group(1))
    else:
        for word in words:
            if word in {
                "one", "two", "three", "four", "five",
                "six", "seven", "eight", "nine", "ten"
            } and "top" in text:
                top_n = word_to_number(word)
                break

    return detected_emotion, found_month, found_year, top_n

def word_to_number(word):
    number_words = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
    }
    return number_words.get(word.lower(), None)

## IMAGE FILTERING ##
def get_image_date(image_path):
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
        debug_print(f"⚠️ Could not get date from {image_path}: {e}")
    return None

def filter_images_by_date(folder, target_month, target_year):
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
            matching_images.append(path)

    return matching_images

## EMOTION MATCHING ##
def filter_images_by_emotion(image_paths, desired_emotion, top_n=3):
    cache = load_cache()
    scored_images = []
    expected_emotions = complex_emotion_map.get(desired_emotion, [desired_emotion])

    for path in image_paths:
        debug_print(f"🖼️ Analyzing: {os.path.basename(path)}")
        path_key = os.path.abspath(path)
        try:
            if path_key in cache:
                result = cache[path_key]
                debug_print("↪ Using cached result")
            else:
                result = DeepFace.analyze(img_path=path, actions=["emotion"], enforce_detection=False)
                cache[path_key] = result

            emotion_scores = result[0]["emotion"]
            dominant_emotion = result[0]["dominant_emotion"].lower()
            relevant_score = sum(emotion_scores.get(e, 0) for e in expected_emotions)

            if relevant_score > 0:
                scored_images.append({
                    "path": path,
                    "dominant": dominant_emotion,
                    "score": relevant_score
                })
                debug_print(f"→ Detected: {dominant_emotion} | Score: {relevant_score:.2f}")

        except Exception as e:
            debug_print(f"❌ Error analyzing {path}: {e}")

    save_cache(cache)
    return sorted(scored_images, key=lambda x: x["score"], reverse=True)[:top_n]

## DISPLAY ##
def show_images(image_results):
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

## OVERALL LOGIC FLOW ##
def process_logic(text):
    print("\n📝 You said:", text)

    detected_emotion, month, year, top_n = extract_query_info(text)
    debug_print(f"😄 Emotion Detected: {detected_emotion}")

    if month and year:
        debug_print(f"📆 Timeframe detected: {month.title()} {year}")
    elif month:
        debug_print(f"📆 Month detected: {month.title()} (year missing)")
    elif year:
        debug_print(f"📆 Year detected: {year} (month missing)")
    else:
        debug_print("📆 No clear date found.")

    debug_print(f"🏆 Top {top_n} results requested")

    predicted_speech_to_text = {
        "emotion": detected_emotion,
        "month": month,
        "year": year,
        "top_n": top_n
    }
    expected_speech_to_text = {
        "emotion": None,
        "month": None,
        "year": None,
        "top_n": None
    }
    log_prediction("speech_to_text", text, predicted_speech_to_text, expected_speech_to_text)

    folder = "static/images_v2"
    debug_print("\n✅ Ready to search for matching photos...\n")
    filtered_images = filter_images_by_date(folder, month, year)

    debug_print(f"\n📂 Found {len(filtered_images)} images from {month.title()} {year}:")
    for f in filtered_images:
        debug_print(" -", f)

    top_emotion_results = filter_images_by_emotion(filtered_images, detected_emotion, top_n)

    debug_print(f"\n✅ Top {top_n} {detected_emotion} images:")
    for r in top_emotion_results:
        debug_print(f" - {r['path']} (Score: {r['score']:.2f}, Emotion: {r['dominant']})")
        predicted_image_emotion = r["path"].split("_")[1].split('\\')[1]
        log_prediction("image", r["path"], predicted=predicted_image_emotion, expected=detected_emotion)

    if top_emotion_results:
        print("\n🖼️ Displaying top results...")
        show_images(top_emotion_results)
    else:
        print("⚠️ No matching images to display.")

if __name__ == '__main__':
    print("🎉 Welcome to SentimentSearch!")
    print("🎤 Please wait for the prompt, then speak your query.")
    print("💬 Try something like: 'Show me the top 4 not negative pictures from February of 2025'\n")

    recorder = AudioToTextRecorder()

    while True:
        done_event = threading.Event()

        def wrapped_process_logic(text):
            process_logic(text)
            done_event.set()

        recorder.text(wrapped_process_logic)
        done_event.wait()

        cont = input("\n🔁 Do you want to try another query? (yes/no): ").strip().lower()
        if cont not in ["yes", "y"]:
            print("👋 Goodbye! Thanks for using SentimentSearch.")
            break
