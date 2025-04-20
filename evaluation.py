import json
from util import complex_emotion_map

def evaluate_session(log_file="session_results.jsonl"):
    stt_total = 0
    stt_correct = 0
    img_total = 0
    img_correct = 0

    with open(log_file, "r") as f:
        for line in f:
            entry = json.loads(line)

            # Evaluate Speech-to-Text
            if entry["type"] == "speech_to_text":
                stt_total += 1
                pred = entry["predicted"]
                exp = entry["expected"]

                if pred == exp:
                    stt_correct += 1

            # Evaluate Image Sentiment
            elif entry["type"] == "image":
                img_total += 1
                pred_emotion = entry["predicted"]
                expected_key = entry["expected"]

                if pred_emotion == expected_key:
                    img_correct += 1
                else:
                    allowed = complex_emotion_map.get(expected_key, [expected_key])
                    if pred_emotion in allowed:
                        img_correct += 1

    print("\n📊 Evaluation Results:")
    if stt_total:
        print(f"🗣️ Speech-to-Text Accuracy: {stt_correct}/{stt_total} = {(stt_correct / stt_total) * 100:.2f}%")
    else:
        print("🗣️ No speech-to-text records found.")

    if img_total:
        print(f"🖼️ Image Sentiment Accuracy: {img_correct}/{img_total} = {(img_correct / img_total) * 100:.2f}%")
    else:
        print("🖼️ No image sentiment records found.")

if __name__ == "__main__":
    # # V1 Evaluation
    # evaluate_session("session_results.jsonl")

    # V2 Evaluation
    evaluate_session("session_results_v2.jsonl")
