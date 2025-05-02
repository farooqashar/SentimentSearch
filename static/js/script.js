const sendQuery = () => {
    const query = document.getElementById("query").value.trim();
    const searchBtn = document.querySelector(".search-button");
    if (!query) {
        showToast("Please enter or speak a query first!");
        return;
    }

    searchBtn.disabled = true;
    searchBtn.innerText = "Searching...";

    saveQueryToHistory(query);

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
        showToast("Search completed!");
        data.results.forEach(img => {
            resultsDiv.innerHTML += `
                <div class="result">
                    <img src="${img.image_url}" alt="Image">
                    <p><strong>${img.dominant}</strong> (${img.score.toFixed(2)})</p>
                    <button onclick="addToFavorites('${img.image_url}', '${img.dominant}', ${img.score})">⭐ Favorite</button>
                </div>
            `;
        });
    })
    .catch(err=>{
        showToast("something went wrong while searching.")
    }).finally(()=>{
        searchBtn.disabled = false;
        searchBtn.innerText = "Search";
    });
}

const startListening = () => {
    if (!('webkitSpeechRecognition' in window)) {
        showToast("Sorry, your browser doesn't support speech recognition.");
        return;
    }
    const micButton = document.querySelector('.mic-button');
    const recognition = new webkitSpeechRecognition();
    recognition.lang = "en-US";
    recognition.start();

    micButton.classList.add('listening');
    recognition.onstart = function () {
        micButton.classList.add('listening');
    };

    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        document.getElementById("query").value = transcript;
        sendQuery();
    };

    recognition.onend = function () {
        micButton.classList.remove('listening');
    };

    recognition.onerror = function(event) {
        showToast("Speech recognition error: " + event.error);
    };
}

const addToFavorites = (url, emotion, score) => {
    let favorites = JSON.parse(localStorage.getItem("favorites") || "[]");
    favorites.push({ url, emotion, score });
    localStorage.setItem("favorites", JSON.stringify(favorites));
    showToast("Added to favorites!");
    showFavorites();
}

const saveQueryToHistory = (query) => {
    let history = JSON.parse(localStorage.getItem("history") || "[]");
    history.push({ query: query, time: new Date().toLocaleString() });
    localStorage.setItem("history", JSON.stringify(history));
    showHistory();
}

const showFavorites = () => {
    const favDiv = document.getElementById("favorites");
    let favorites = JSON.parse(localStorage.getItem("favorites") || "[]");


    favDiv.innerHTML = "<h3>Your Favorites</h3>";
    if (favorites.length === 0) {
        favDiv.innerHTML += "<p>No favorites yet.</p>";
        return;
    }

    favorites.forEach(img => {
        favDiv.innerHTML += `
            <div class="result">
                <img src="${img.url}" alt="Favorite">
                <p><strong>${img.emotion}</strong> (${img.score.toFixed(2)})</p>
            </div>
        `;
    });
}


const showHistory = () => {
    const histDiv = document.getElementById("history");
    let history = JSON.parse(localStorage.getItem("history") || "[]");
    histDiv.innerHTML = "<h3>Query History</h3>";
    if (history.length === 0) {
        histDiv.innerHTML += "<p>No past queries.</p>";
        return;
    }
    history.forEach(item => {
        histDiv.innerHTML += `<p onclick="repeatQuery('${item.query}')">🕑 ${item.query} <small>(${item.time})</small></p>`;
    });
}

const repeatQuery = (query) => {
    document.getElementById("query").value = query;
    sendQuery();
    showTab('results');
}

const showTab = (tabName) => {
    document.getElementById("results").style.display = "none";
    document.getElementById("favorites").style.display = "none";
    document.getElementById("history").style.display = "none";

    document.getElementById(tabName).style.display = "block";

    if (tabName === 'favorites') showFavorites();
    if (tabName === 'history') showHistory();
}

function openCameraModal() {
    const modal = document.getElementById("cameraModal");
    const video = document.getElementById("video");

    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            videoStream = stream;
            video.srcObject = stream;
            modal.style.display = "flex";
        })
        .catch(err => showToast("Cannot access camera: " + err));
}

function closeCameraModal() {
    const modal = document.getElementById("cameraModal");
    modal.style.display = "none";
    if (videoStream) {
        videoStream.getTracks().forEach(track => track.stop());
    }
}

function capturePhoto() {
    const video = document.getElementById("video");
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(blob => {
        const formData = new FormData();
        formData.append("image", blob, "face_template.jpg");

        fetch("/upload_face_template", {
            method: "POST",
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            showToast("Face saved successfully!");
            closeCameraModal();
        })
        .catch(() => showToast("Upload failed."));
    }, "image/jpeg");
}

function closeIntroModal() {
    document.getElementById("introModal").style.display = "none";
    localStorage.setItem("seenIntro", "true");
}

const showToast = (message, duration = 3000) => {
    const toast = document.getElementById("toast");
    toast.innerText = message;
    toast.classList.remove("hidden");
    toast.classList.add("show");

    setTimeout(() => {
        toast.classList.remove("show");
        toast.classList.add("hidden");
    }, duration);
}

window.onload = function() {
    if (!localStorage.getItem("seenIntro")) {
        document.getElementById("introModal").style.display = "block";
    }
};

showTab('results');
