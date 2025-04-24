from flask import Flask, request, jsonify, render_template
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

if __name__ == "__main__":
    app.run(debug=True)
