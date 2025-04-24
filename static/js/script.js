function sendQuery() {
    const query = document.getElementById("query").value.trim();
    if (!query) {
        alert("Please enter or speak a query first!");
        return;
    }
    fetch('/process_query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
    })
    .then(response => response.json())
    .then(data => {
        const resultsDiv = document.getElementById("results");
        resultsDiv.innerHTML = "";
        if (data.results.length === 0) {
            resultsDiv.innerHTML = "<p>No matching images found.</p>";
            return;
        }
        data.results.forEach(img => {
            resultsDiv.innerHTML += `
                <div class="result">
                    <img src="${img.image_url}" alt="Image">
                    <p><strong>${img.dominant}</strong> (${img.score.toFixed(2)})</p>
                </div>
            `;
        });
    });
}

function startListening() {
    if (!('webkitSpeechRecognition' in window)) {
        alert("Sorry, your browser doesn't support speech recognition.");
        return;
    }
    const recognition = new webkitSpeechRecognition();
    recognition.lang = "en-US";
    recognition.start();

    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        document.getElementById("query").value = transcript;
        sendQuery();
    };

    recognition.onerror = function(event) {
        alert("Speech recognition error: " + event.error);
    };
}
