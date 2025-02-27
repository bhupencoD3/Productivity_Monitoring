// Configuration
const API_ENDPOINTS = {
  INITIALIZE: "/initialize",
  RECOGNIZE: "/recognize",
  STATS: "/stats",
  STOP: "/stop",
  TOGGLE_DEBUG: "/toggle_debug",
  SHUTDOWN: "/shutdown",
};

let statsInterval = null;

// Utility Functions
function showSpinner(show) {
  document.getElementById("spinner").style.display = show ? "block" : "none";
}

function updateStatus(message) {
  document.getElementById("status").innerText = message;
}

function updateStatsTable(stats) {
  const tbody = document.getElementById("stats-table-body");
  const totalClosedTime = stats.total_closed_time?.toFixed(1) || "0.0";
  const stateSince = stats.state_since || "N/A";
  const recentLogs =
    stats.pending_logs
      ?.map((log) => `${log.start} - ${log.end} (${log.duration}s)`)
      .join("<br>") || "No logs yet";

  tbody.innerHTML = `
    <tr><td>User State</td><td>${stats.current_state || "N/A"}</td></tr>
    <tr><td>Total Closed Time</td><td>${totalClosedTime}s</td></tr>
    <tr><td>State Since</td><td>${stateSince}</td></tr>
    <tr><td>Recent Logs</td><td>${recentLogs}</td></tr>
  `;
  document.getElementById("stats-container").style.display = "block";
}

async function fetchWithSpinner(url, options = {}) {
  showSpinner(true);
  try {
    const response = await fetch(url, options);
    if (!response.ok) {
      throw new Error(response.statusText || "Request failed");
    }
    return await response.json();
  } catch (error) {
    updateStatus(`Error: ${error.message}`);
    throw error;
  } finally {
    showSpinner(false);
  }
}

// Main Functions
async function initialize() {
  try {
    const result = await fetchWithSpinner(API_ENDPOINTS.INITIALIZE, {
      method: "POST",
    });
    updateStatus(`Status: ${result.message}`);
  } catch (error) {
    console.error("Initialization failed:", error);
  }
}

async function startRecognition() {
  showSpinner(true);
  try {
    const response = await fetch(API_ENDPOINTS.RECOGNIZE);
    const result = await response.json();
    console.log("Recognition result:", result); // Debug
    if (response.ok) {
      updateStatus(
        `Status: ${result.message}\nUser: ${result.name || "Unknown"} (ID: ${result.employee_id || "N/A"})`,
      );
      startStatsUpdates();
    } else {
      updateStatus(`Status: ${result.detail || "Recognition failed"}`);
    }
  } catch (error) {
    updateStatus(`Error: ${error.message}`);
  } finally {
    showSpinner(false);
  }
}
async function getStats() {
  try {
    const stats = await fetchWithSpinner(API_ENDPOINTS.STATS);
    updateStatsTable(stats);
  } catch (error) {
    console.error("Failed to fetch stats:", error);
  }
}

function startStatsUpdates() {
  if (statsInterval) clearInterval(statsInterval);
  statsInterval = setInterval(getStats, 2000);
}

async function stopMonitoring() {
  try {
    const result = await fetchWithSpinner(API_ENDPOINTS.STOP, {
      method: "POST",
    });
    updateStatus(`Status: ${result.message}`);
    clearInterval(statsInterval);
    document.getElementById("stats-container").style.display = "none";
  } catch (error) {
    console.error("Failed to stop monitoring:", error);
  }
}

async function toggleDebug() {
  try {
    const result = await fetchWithSpinner(API_ENDPOINTS.TOGGLE_DEBUG, {
      method: "POST",
    });
    updateStatus(`Debug mode: ${result.debug_mode}`);
  } catch (error) {
    console.error("Failed to toggle debug mode:", error);
  }
}

async function shutdown() {
  const secret = prompt("Enter shutdown secret key:");
  if (!secret) {
    updateStatus("Shutdown canceled: No secret key provided");
    return;
  }

  try {
    const result = await fetchWithSpinner(API_ENDPOINTS.SHUTDOWN, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ secret }),
    });
    updateStatus(`Status: ${result.message}`);
  } catch (error) {
    console.error("Failed to shutdown:", error);
  }
}
