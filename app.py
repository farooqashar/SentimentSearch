from flask import Flask, request, jsonify, render_template
from sentiment_search import extract_query_info, filter_images_by_date, filter_images_by_emotion

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/process_query', methods=['POST'])
def process_query():
    data = request.json
    text = data.get("query")

    emotion_category, month, year, top_n = extract_query_info(text)
    folder = "static/images"
    filtered_images = filter_images_by_date(folder, month, year)
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
