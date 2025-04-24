from flask import Flask, request, jsonify, render_template
import os
from deepface import DeepFace
# from sentiment_search import extract_query_info, filter_images_by_date, filter_images_by_emotion, filter_images_by_location
from sentiment_search_v2 import extract_query_info, filter_images_by_date, filter_images_by_emotion, filter_images_by_location

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/process_query', methods=['POST'])
def process_query():
    data = request.json
    text = data.get("query")

    emotion_category, month, year, top_n, location = extract_query_info(text)
    folder = "static/images_v2"
    location_filter = filter_images_by_location(folder,location)
    date_filter = filter_images_by_date(folder, month, year)
    filtered_images = list(set(location_filter) & set(date_filter))

    search_with_user = "my face" in text.lower()
    face_template_path = "user_face_templates/face_template.jpg"
    use_face_template = search_with_user and os.path.exists(face_template_path)

    if use_face_template:
        print("📸 Using face template for emotion matching...")
        result = DeepFace.analyze(img_path=face_template_path, actions=["emotion"], enforce_detection=False)
        emotion_category = result[0]["dominant_emotion"].lower()
        print("👀 Detected Emotion from User: ",emotion_category)

    top_emotion_results = filter_images_by_emotion(filtered_images, emotion_category, top_n)

    results = [{
        "image_url": "/" + img['path'].replace("\\", "/"),
        "score": img["score"],
        "dominant": img["dominant"]
    } for img in top_emotion_results]

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

if __name__ == "__main__":
    app.run(debug=True)
