// static/script.js
let ws = null;
let statsInterval = null;

async function initialize() {
  showSpinner(true);
  const knownFaces = [
    {
      name: "bhupen",
      path: "/home/bhupen/Productivity_tracker_edited/pRODUCTIVITY-mONITORING/app/known_faces/bhupend.jpeg",
    }, // Adjust for your Linux path
    {
      name: "tushar",
      path: "/home/bhupen/Productivity_tracker_edited/pRODUCTIVITY-mONITORING/app/known_faces/2025-01-31_11_09_17.jpg",
    },
    {
      name: "bhupendra",
      path: "/home/bhupen/Productivity_tracker_edited/pRODUCTIVITY-mONITORING/app/known_faces/bhupendra.jpeg",
    },
    {
      name: "shubham",
      path: "/home/bhupen/Productivity_tracker_edited/pRODUCTIVITY-mONITORING/app/known_faces/shubham.jpeg",
    },
  ];

  try {
    const response = await fetch("/initialize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(knownFaces),
    });
    const result = await response.json();
    updateStatus(`Status: ${result.message}`);
  } catch (error) {
    updateStatus(`Error: ${error.message}`);
  } finally {
    showSpinner(false);
  }
}

async function startRecognition() {
  showSpinner(true);
  try {
    const response = await fetch("/recognize");
    const result = await response.json();
    updateStatus(`Status: ${result.message}\nUser: ${result.user_id}`);
    document.getElementById("videoFeed").classList.remove("active");
    if (ws) {
      ws.close();
      ws = null;
    }
    startStatsUpdates();
  } catch (error) {
    updateStatus(`Error: ${error.message}`);
  } finally {
    showSpinner(false);
  }
}

async function getStats() {
  try {
    const response = await fetch("/stats");
    const stats = await response.json();
    updateStatsTable(stats);
  } catch (error) {
    updateStatus(`Error: ${error.message}`);
  }
}

function startStatsUpdates() {
  if (statsInterval) clearInterval(statsInterval);
  statsInterval = setInterval(async () => {
    await getStats();
  }, 2000);
}

async function stopMonitoring() {
  showSpinner(true);
  try {
    const response = await fetch("/stop", { method: "POST" });
    const result = await response.json();
    updateStatus(`Status: ${result.message}`);
    const videoFeed = document.getElementById("videoFeed");
    if (ws) {
      ws.close();
      ws = null;
    }
    videoFeed.classList.remove("active");
    videoFeed.src = "";
    clearInterval(statsInterval);
    document.getElementById("stats-container").style.display = "none";
  } catch (error) {
    updateStatus(`Error: ${error.message}`);
  } finally {
    showSpinner(false);
  }
}

async function toggleDebug() {
  try {
    const response = await fetch("/toggle_debug", { method: "POST" });
    const result = await response.json();
    const videoFeed = document.getElementById("videoFeed");
    if (result.debug_mode) {
      videoFeed.classList.add("active");
      if (!ws) {
        ws = new WebSocket("ws://localhost:8000/video");
        ws.onmessage = (event) => {
          console.log("Received frame data");
          videoFeed.src = `data:image/jpeg;base64,${event.data}`;
        };
        ws.onerror = (error) => {
          console.error("WebSocket error:", error);
          updateStatus("WebSocket error");
        };
        ws.onclose = () => {
          videoFeed.classList.remove("active");
          ws = null;
          console.log("WebSocket closed");
        };
      }
    } else {
      if (ws) {
        ws.close();
        ws = null;
      }
      videoFeed.classList.remove("active");
      videoFeed.src = "";
    }
  } catch (error) {
    updateStatus(`Error: ${error.message}`);
  }
}

async function shutdown() {
  showSpinner(true);
  const secret = prompt("Enter shutdown secret key:");
  try {
    const response = await fetch("/shutdown", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ secret: secret }),
    });
    const result = await response.json();
    updateStatus(`Status: ${result.message}`);
  } catch (error) {
    updateStatus(`Error: ${error.message}`);
  } finally {
    showSpinner(false);
  }
}

function updateStatus(message) {
  document.getElementById("status").innerText = message;
}

function updateStatsTable(stats) {
  const tbody = document.getElementById("stats-table-body");
  const totalClosedTime =
    stats.total_closed_time !== undefined
      ? stats.total_closed_time.toFixed(1)
      : "0.0";
  tbody.innerHTML = `
        <tr><td>User State</td><td>${stats.current_state || "N/A"}</td></tr>
        <tr><td>Total Closed Time</td><td>${totalClosedTime}s</td></tr>
        <tr><td>State Since</td><td>${stats.state_since || "N/A"}</td></tr>
        <tr><td>Recent Logs</td><td>${stats.pending_logs && stats.pending_logs.length > 0 ? stats.pending_logs.map((log) => `${log.start} - ${log.end} (${log.duration}s)`).join("<br>") : "No logs yet"}</td></tr>
    `;
  document.getElementById("stats-container").style.display = "block";
}

function showSpinner(show) {
  document.getElementById("spinner").style.display = show ? "block" : "none";
}
