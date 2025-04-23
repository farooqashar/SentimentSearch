import React, { useState } from "react";
import axios from "axios";
import Recorder from "./mic.js";

function App() {
  const [query, setQuery] = useState("");
  const [log, setLog] = useState("");

  const handleSearch = async () => {
    try {
      const res = await axios.post("http://127.0.0.1:5000/analyze", { query });
      setLog("Query submitted. Check the backend for image analysis.");
    } catch (error) {
      setLog("Something went wrong: " + error.message);
    }
  };

  return (
    <div style={{ padding: "2rem" }}>
      <h1>SentimentSearch</h1>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="e.g. show me the top 3 happy images from May"
        style={{ width: "400px", marginRight: "1rem" }}
      />
      <button onClick={handleSearch}>Search</button>
      <p>{log}</p>
      <Recorder/>
    </div>
  );
}

export default App;
