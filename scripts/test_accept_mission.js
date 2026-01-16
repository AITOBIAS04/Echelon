// Test script to verify accept mission endpoint
const API_BASE = "http://localhost:8000";
const missionId = "mission_001";
const url = `${API_BASE}/api/situation-room/missions/${missionId}/accept`;

console.log("Testing:", url);

fetch(url, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
})
  .then((res) => {
    console.log("Status:", res.status, res.statusText);
    return res.json();
  })
  .then((data) => {
    console.log("Response:", JSON.stringify(data, null, 2));
  })
  .catch((err) => {
    console.error("Error:", err.message);
  });
