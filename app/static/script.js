// app/static/script.js
const API_ENDPOINTS = {
  INITIALIZE: "/initialize",
  RECOGNIZE: "/recognize",
  STATS: "/stats",
  STOP: "/stop",
  TOGGLE_DEBUG: "/toggle_debug",
  SHUTDOWN: "/shutdown",
};

let statsInterval = null;
let productivityChart = null;
let closureTimelineChart = null;
let dailyClosureChart = null;

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

  let presenceStatus = "Absent";
  if (stats.current_state === "open" || stats.current_state === "closed") {
    presenceStatus = "Present";
  }

  tbody.innerHTML = `
    <tr><td>User State</td><td>${stats.current_state || "N/A"}</td></tr>
    <tr><td>Presence</td><td>${presenceStatus}</td></tr>
    <tr><td>Total Closed Time</td><td>${totalClosedTime}s</td></tr>
    <tr><td>State Since</td><td>${stateSince}</td></tr>
    <tr><td>Recent Logs</td><td>${recentLogs}</td></tr>
  `;
  if (stats.productivity_data) {
    tbody.innerHTML += `
      <tr><td>Total Session Time</td><td>${stats.productivity_data.total_session_time.toFixed(1)}s</td></tr>
      <tr><td>Productivity Score</td><td>${stats.productivity_data.productivity_score.toFixed(1)}%</td></tr>
    `;
    updateProductivityChart(stats.productivity_data);
    updateClosureTimeline(stats.productivity_data);
    updateDailyClosureChart(stats.productivity_data);
  }
  document.getElementById("stats-container").style.display = "block";
}

function updateProductivityChart(data) {
  const ctx = document.getElementById("productivityChart").getContext("2d");
  if (productivityChart) {
    productivityChart.destroy();
  }
  productivityChart = new Chart(ctx, {
    type: "pie",
    data: {
      labels: ["Productive", "Closed"],
      datasets: [
        {
          data: [data.productivity_score, 100 - data.productivity_score],
          backgroundColor: ["#36A2EB", "#FF6384"],
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: "top" },
        title: { display: true, text: `${data.name}'s Productivity` },
      },
    },
  });
}

function updateClosureTimeline(data) {
  const ctx = document.getElementById("closureTimelineChart").getContext("2d");
  if (closureTimelineChart) {
    closureTimelineChart.destroy();
  }
  closureTimelineChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: data.closure_events.map((event) =>
        event.start.split("T")[1].substring(0, 8),
      ),
      datasets: [
        {
          label: "Closure Duration (s)",
          data: data.closure_events.map((event) => event.duration),
          borderColor: "#FF6384",
          fill: false,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: "top" },
        title: { display: true, text: "Closure Events Over Time" },
      },
      scales: {
        x: { title: { display: true, text: "Time" } },
        y: { title: { display: true, text: "Duration (s)" } },
      },
    },
  });
}

function updateDailyClosureChart(data) {
  const ctx = document.getElementById("dailyClosureChart").getContext("2d");
  if (dailyClosureChart) {
    dailyClosureChart.destroy();
  }

  const hourlyClosures = {};
  data.closure_events.forEach((event) => {
    const hour = event.start.split("T")[1].substring(0, 2);
    hourlyClosures[hour] = (hourlyClosures[hour] || 0) + event.duration;
  });

  const labels = Object.keys(hourlyClosures).sort();
  const durations = labels.map((hour) => hourlyClosures[hour]);

  dailyClosureChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Total Closure Time (s)",
          data: durations,
          backgroundColor: "#36A2EB",
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: "top" },
        title: { display: true, text: "Hourly Closure Totals" },
      },
      scales: {
        x: { title: { display: true, text: "Hour" } },
        y: { title: { display: true, text: "Total Closed Time (s)" } },
      },
    },
  });
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
  try {
    const result = await fetchWithSpinner(API_ENDPOINTS.RECOGNIZE);
    updateStatus(
      `Status: ${result.message}\nUser: ${result.name || "Unknown"} (ID: ${result.employee_id || "N/A"})`,
    );
    startStatsUpdates();
  } catch (error) {
    console.error("Recognition failed:", error);
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
