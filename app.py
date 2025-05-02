import base64
import io
import shutil
import uuid
from PIL import Image
from flask import Flask, request, jsonify, render_template,json 
import os
from deepface import DeepFace
# from sentiment_search import extract_query_info, filter_images_by_date, filter_images_by_emotion, filter_images_by_location (V1)
from sentiment_search_v2 import extract_query_info, filter_images_by_date, filter_images_by_emotion, filter_images_by_location

app = Flask(__name__)
UPLOAD_CACHE_FOLDER = "static/user_upload_cache"
EVAL_LOG = "user_evaluation.jsonl"
os.makedirs(UPLOAD_CACHE_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/process_query', methods=['POST'])
def process_query():
    for f in os.listdir(UPLOAD_CACHE_FOLDER):
        try:
            file_path = os.path.join(UPLOAD_CACHE_FOLDER, f)
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"⚠️ Error deleting {file_path}: {e}")

    data = request.json
    text = data.get("query")
    uploaded_photos = data.get("uploaded", [])
    print("uploaded: ", len(uploaded_photos))

    result_image = []

    try:
        for item in uploaded_photos:
            base64_data = item.get("url", "").split(",")[-1]
            img_bytes = base64.b64decode(base64_data)
            img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            img_path = os.path.join(UPLOAD_CACHE_FOLDER, f"{uuid.uuid4().hex}.jpg")
            img.save(img_path)

            # result_image.append(img_path)
    except Exception as e:
        print("Error processing uploaded images: ", e)


    emotion_category, month, year, top_n, location = extract_query_info(text)

    location_filter_uploaded = filter_images_by_location(UPLOAD_CACHE_FOLDER,location)
    data_filter_uploaded = filter_images_by_date(UPLOAD_CACHE_FOLDER,month,year)
    filtered_images_uploaded = list(set(location_filter_uploaded) & set(data_filter_uploaded))

    result_image += filtered_images_uploaded
    print('resulted upload image: ',len(result_image))

    folder = "static/images_v2"
    location_filter = filter_images_by_location(folder,location)
    date_filter = filter_images_by_date(folder, month, year)
    filtered_images = list(set(location_filter) & set(date_filter))

    result_image += filtered_images

    search_with_user = "my face" in text.lower()
    face_template_path = "user_face_templates/face_template.jpg"
    use_face_template = search_with_user and os.path.exists(face_template_path)

    if use_face_template:
        print("📸 Using face template for emotion matching...")
        result = DeepFace.analyze(img_path=face_template_path, actions=["emotion"], enforce_detection=False)
        emotion_category = result[0]["dominant_emotion"].lower()
        print("👀 Detected Emotion from User: ",emotion_category)

    top_emotion_results = filter_images_by_emotion(result_image, emotion_category, top_n)

    results = [{
        "image_url": "/" + img['path'].replace("\\", "/"),
        "score": img["score"],
        "dominant": img["dominant"]
    } for img in top_emotion_results]

    # shutil.rmtree(UPLOAD_CACHE_FOLDER, ignore_errors=True)

    return jsonify({
        "emotion": emotion_category,
        "month": month,
        "year": year,
        "top_n": top_n,
        "results": results
    })

UPLOAD_FOLDER = "user_face_templates"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/upload_face_template", methods=["POST"])
def upload_face_template():
    if "image" not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    file = request.files["image"]
    file_path = os.path.join(UPLOAD_FOLDER, "face_template.jpg")
    file.save(file_path)
    return jsonify({"status": "success", "saved_to": file_path})

@app.route("/evaluate_result", methods=["POST"])
def evaluate_result():
    data = request.get_json()
    url = data.get("url")
    expected_emotion = data.get("expected_emotion")
    met = data.get("met_expectation")

    log_entry = {
        "url": url,
        "expected_emotion": expected_emotion,
        "met_expectation": met
    }

    with open(EVAL_LOG, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(debug=True)
