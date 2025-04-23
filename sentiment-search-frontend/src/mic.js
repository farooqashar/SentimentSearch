import React, { useState } from "react";
import MicRecorder from "mic-recorder-to-mp3";
import axios from "axios";

const recorder = new MicRecorder({ bitRate: 128 });

export default function Recorder() {
  const [isRecording, setIsRecording] = useState(false);
  const [transcription, setTranscription] = useState("");

  const startRecording = () => {
    recorder.start().then(() => {
      setIsRecording(true);
    });
  };

  const stopRecording = () => {
    recorder.stop().getMp3().then(([buffer, blob]) => {
      setIsRecording(false);
      const file = new File(buffer, "recording.wav", {
        type: blob.type,
        lastModified: Date.now()
      });

      const formData = new FormData();
      formData.append("audio", file);

      axios.post("http://127.0.0.1:5000/transcribe", formData).then(res => {
        alert("Transcription: " + res.data.text);
        setTranscription(res.data.text);
      });
    });
  };

  return (
    <div>
      <button onClick={startRecording} disabled={isRecording}>🎙️ Start</button>
      <button onClick={stopRecording} disabled={!isRecording}>🛑 Stop</button>
      <h2>Please confirm if our transcription is correct</h2>
      <input
        type="text"
        defaultValue={transcription}
        style={{ width: "400px", marginRight: "1rem" }}
      />
    </div>
  );
}
