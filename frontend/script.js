
"use strict";

// ============================================================
// CROWD EVACUATION SIMULATION - FRONTEND
// ============================================================

const $ = (id) => document.getElementById(id);

const scenarioSelect = $("scenarioSelect");
const populationInput = $("populationInput");
const methodSelect = $("methodSelect");
const runButton = $("runSimulationBtn");
const statusBox = $("statusBox");

const scenarioDescription = $("scenarioDescription");
const methodHint = $("methodHint");
const comparisonPanel = $("comparisonPanel");
const comparisonTableBody = $("comparisonTableBody");

const evacuationChart = $("evacuationChart");
const chartSummary = $("chartSummary");
const densityCanvas = $("densityCanvas");
const environmentScene = $("environmentScene");
const liveCanvas = $("liveSimulationCanvas");

const exitUsageList = $("exitUsageList");
const speedControl = $("speedControl");
const densityToggle = $("densityToggle");

const state = {
  result: null,
  frameIndex: 0,
  playing: false,
  timerId: null,
  lastTimestamp: 0,
  accumulator: 0
};

const descriptions = {
  normal: "Baseline evacuation across a two-exit building.",
  high_crowd: "A larger population increases crowd density.",
  blocked_exit: "One exit is unavailable.",
  three_exits: "People can use three exits.",
  exit_locations: "Different exit positions test building geometry.",
  euler_vs_rk4: "Compare Euler and RK4 numerical methods."
};

function num(value, fallback = 0) {
  const result = Number(value);
  return Number.isFinite(result) ? result : fallback;
}

function fmt(value, suffix = "") {
  return `${num(value).toFixed(2)}${suffix}`;
}

function setStatus(message, type = "ready") {
  if (!statusBox) return;
  statusBox.textContent = message;
  statusBox.dataset.type = type;
}

function svg(tag, attrs = {}, text = "") {
  const element = document.createElementNS(
    "http://www.w3.org/2000/svg",
    tag
  );

  for (const [key, value] of Object.entries(attrs)) {
    element.setAttribute(key, String(value));
  }

  if (text !== "") element.textContent = text;
  return element;
}

function updateMethodState() {
  const scenario = scenarioSelect.value;
  const comparison = scenario === "euler_vs_rk4";

  methodSelect.disabled = comparison;
  if (comparison) methodSelect.value = "euler";

  methodHint.textContent = comparison
    ? "Both methods will be compared."
    : "Choose Euler or RK4.";

  scenarioDescription.textContent =
    descriptions[scenario] || descriptions.normal;

  comparisonPanel.classList.toggle("hidden", !comparison);
}

async function loadScenarios() {
  try {
    const response = await fetch("/api/scenarios");
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Unable to load scenarios.");
    }

    updateMethodState();
  } catch (error) {
    console.error("Scenario loading error:", error);
  }
}

function renderMetrics(data) {
  $("totalPeople").textContent = data.total_people ?? "-";
  $("evacuatedPeople").textContent = data.evacuated_people ?? "-";
  $("evacuationTime").textContent = fmt(data.evacuation_time, " s");
  $("averageSpeed").textContent = fmt(data.average_speed, " m/s");
  $("maximumDensity").textContent =
    fmt(data.maximum_density, " persons/m²");
  $("averageDensity").textContent =
    fmt(data.average_density, " persons/m²");

  const total = num(data.total_people);
  const evacuated = num(data.evacuated_people);
  const percentage = total > 0
    ? Math.min(100, evacuated / total * 100)
    : 0;

  $("progressBar").style.width = `${percentage}%`;
  $("progressValue").textContent = `${percentage.toFixed(1)}%`;
  $("progressText").textContent = `${evacuated} / ${total} people evacuated`;
}

function renderExitUsage(exitUsage) {
  exitUsageList.replaceChildren();

  if (!exitUsage || typeof exitUsage !== "object" ||
    Object.keys(exitUsage).length === 0) {
    exitUsageList.textContent = "No exit usage data available.";
    return;
  }

  for (const [label, value] of Object.entries(exitUsage)) {
    const percentage = Math.max(0, num(value));
    const row = document.createElement("div");
    row.className = "exit-item";

    const name = document.createElement("span");
    name.textContent = label;

    const track = document.createElement("div");
    track.className = "exit-bar-track";

    const bar = document.createElement("div");
    bar.className = "exit-bar";
    bar.style.width = `${Math.min(100, percentage)}%`;

    const amount = document.createElement("strong");
    amount.textContent = `${percentage.toFixed(1)}%`;

    track.appendChild(bar);
    row.append(name, track, amount);
    exitUsageList.appendChild(row);
  }
}

function renderComparison(data) {
  const summary = data.summary;

  comparisonTableBody.replaceChildren();

  if (!summary?.euler || !summary?.rk4) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 3;
    cell.textContent = "Comparison data is unavailable.";
    row.appendChild(cell);
    comparisonTableBody.appendChild(row);
    return;
  }

  const metrics = [
    ["Evacuation Time", "evacuation_time", " s"],
    ["Average Speed", "average_speed", " m/s"],
    ["Maximum Density", "maximum_density", " persons/m²"],
    ["Average Density", "average_density", " persons/m²"],
    ["Evacuated People", "evacuated_people", " people"]
  ];

  for (const [label, key, unit] of metrics) {
    const row = document.createElement("tr");

    for (const value of [
      label,
      `${fmt(summary.euler[key])}${unit}`,
      `${fmt(summary.rk4[key])}${unit}`
    ]) {
      const cell = document.createElement("td");
      cell.textContent = value;
      row.appendChild(cell);
    }

    comparisonTableBody.appendChild(row);
  }
}

function renderEvacuationChart(history) {
  evacuationChart.replaceChildren();

  const points = Array.isArray(history)
    ? history.filter(item =>
      Number.isFinite(Number(item.time)) &&
      Number.isFinite(Number(item.evacuated_people))
    )
    : [];

  if (!points.length) {
    evacuationChart.appendChild(svg("text", {
      x: 350,
      y: 130,
      "text-anchor": "middle",
      fill: "#64748b"
    }, "No evacuation history available"));

    chartSummary.textContent = "No chart data was returned.";
    return;
  }

  const width = 700;
  const height = 260;
  const margin = { top: 20, right: 25, bottom: 40, left: 55 };

  evacuationChart.setAttribute("viewBox", `0 0 ${width} ${height}`);

  const maxTime = Math.max(1, ...points.map(p => num(p.time)));
  const maxPeople = Math.max(1, ...points.map(
    p => num(p.evacuated_people)
  ));

  const plotW = width - margin.left - margin.right;
  const plotH = height - margin.top - margin.bottom;

  const x = value => margin.left + num(value) / maxTime * plotW;
  const y = value => height - margin.bottom -
    num(value) / maxPeople * plotH;

  evacuationChart.appendChild(svg("rect", {
    x: 0, y: 0, width, height, fill: "#ffffff"
  }));

  for (let i = 0; i <= 4; i++) {
    const gy = margin.top + i * plotH / 4;
    evacuationChart.appendChild(svg("line", {
      x1: margin.left,
      y1: gy,
      x2: width - margin.right,
      y2: gy,
      stroke: "#dbe5f1"
    }));
  }

  evacuationChart.appendChild(svg("line", {
    x1: margin.left,
    y1: margin.top,
    x2: margin.left,
    y2: height - margin.bottom,
    stroke: "#64748b"
  }));

  evacuationChart.appendChild(svg("line", {
    x1: margin.left,
    y1: height - margin.bottom,
    x2: width - margin.right,
    y2: height - margin.bottom,
    stroke: "#64748b"
  }));

  const polyline = points
    .map(p => `${x(p.time)},${y(p.evacuated_people)}`)
    .join(" ");

  evacuationChart.appendChild(svg("polyline", {
    points: polyline,
    fill: "none",
    stroke: "#2563eb",
    "stroke-width": 3,
    "stroke-linejoin": "round"
  }));

  evacuationChart.appendChild(svg("text", {
    x: width / 2,
    y: height - 8,
    "text-anchor": "middle",
    fill: "#475569"
  }, "Time (seconds)"));

  evacuationChart.appendChild(svg("text", {
    x: 15,
    y: height / 2,
    transform: `rotate(-90 15 ${height / 2})`,
    "text-anchor": "middle",
    fill: "#475569"
  }, "Evacuated People"));

  const last = points[points.length - 1];
  chartSummary.textContent =
    `Evacuated: ${last.evacuated_people} people | ` +
    `Time: ${num(last.time).toFixed(2)} seconds`;
}

function renderDensityMatrix(matrix) {
  const ctx = densityCanvas.getContext("2d");
  const width = densityCanvas.width;
  const height = densityCanvas.height;

  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#f1f5f9";
  ctx.fillRect(0, 0, width, height);

  if (!Array.isArray(matrix) || !matrix.length ||
    !Array.isArray(matrix[0]) || !matrix[0].length) {
    ctx.fillStyle = "#64748b";
    ctx.font = "15px Arial";
    ctx.textAlign = "center";
    ctx.fillText("No density data available", width / 2, height / 2);
    return;
  }

  const rows = matrix.length;
  const cols = Math.max(...matrix.map(row =>
    Array.isArray(row) ? row.length : 0
  ));

  if (!cols) return;

  const values = matrix.map(row =>
    Array.from({ length: cols }, (_, c) =>
      Math.max(0, num(row?.[c]))
    )
  );

  const maximum = Math.max(...values.flat());

  if (maximum <= 0) {
    ctx.fillStyle = "#64748b";
    ctx.textAlign = "center";
    ctx.fillText("Density values are zero", width / 2, height / 2);
    return;
  }

  const cellW = width / cols;
  const cellH = height / rows;

  values.forEach((row, r) => {
    row.forEach((value, c) => {
      const intensity = value / maximum;
      ctx.fillStyle = intensity === 0
        ? "#edf4fb"
        : `hsl(${220 - intensity * 220},85%,${94 - intensity * 42}%)`;

      ctx.fillRect(c * cellW, r * cellH, Math.ceil(cellW) + 1,
        Math.ceil(cellH) + 1);
    });
  });
}

function renderEnvironment(data) {
  environmentScene.replaceChildren();

  const width = 600;
  const height = 280;
  const margin = 35;
  const plotW = 530;
  const plotH = 215;

  const building = data.building || {};
  const buildingW = Math.max(1, num(building.width, 100));
  const buildingH = Math.max(1, num(building.height, 60));
  const obstacles = Array.isArray(building.obstacles)
    ? building.obstacles : [];
  const exits = Array.isArray(data.exits) ? data.exits : [];

  const sx = value => margin + num(value) / buildingW * plotW;
  const sy = value => 25 + plotH - num(value) / buildingH * plotH;

  environmentScene.appendChild(svg("rect", {
    x: margin, y: 25, width: plotW, height: plotH,
    rx: 8, fill: "#f0f7ff", stroke: "#64748b", "stroke-width": 2
  }));

  obstacles.forEach(obstacle => {
    if (!Array.isArray(obstacle) || obstacle.length < 4) return;
    const [x1, y1, x2, y2] = obstacle;

    environmentScene.appendChild(svg("rect", {
      x: sx(x1),
      y: sy(y2),
      width: Math.max(2, (x2 - x1) / buildingW * plotW),
      height: Math.max(2, (y2 - y1) / buildingH * plotH),
      fill: "#94a3b8",
      stroke: "#64748b"
    }));
  });

  exits.forEach((exit, index) => {
    const available = exit.available !== false;
    const ex = sx(exit.x);
    const ey = sy(exit.y);

    environmentScene.appendChild(svg("circle", {
      cx: ex, cy: ey, r: 9,
      fill: available ? "#16a34a" : "#dc2626"
    }));

    environmentScene.appendChild(svg("text", {
      x: ex, y: ey - 13,
      "text-anchor": "middle",
      fill: "#0f172a",
      "font-size": 11
    }, available ? `Exit ${exit.id ?? index + 1}` : "Blocked"));
  });

  if (!exits.length) {
    environmentScene.appendChild(svg("text", {
      x: width / 2, y: height / 2,
      "text-anchor": "middle",
      fill: "#64748b"
    }, "No exit data returned"));
  }
}

function drawLiveFrame(frame) {
  if (!frame || !liveCanvas || !state.result) return;

  const ctx = liveCanvas.getContext("2d");
  const width = liveCanvas.width;
  const height = liveCanvas.height;
  const padding = 36;
  const building = state.result.building || {};

  const buildingW = Math.max(1, num(building.width, 100));
  const buildingH = Math.max(1, num(building.height, 60));
  const plotW = width - 2 * padding;
  const plotH = height - 2 * padding;

  const x = value => padding + num(value) / buildingW * plotW;
  const y = value => height - padding - num(value) / buildingH * plotH;

  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#f6faff";
  ctx.fillRect(0, 0, width, height);

  ctx.strokeStyle = "#d7e6f7";
  for (let i = 0; i <= 10; i++) {
    ctx.beginPath();
    ctx.moveTo(padding + i * plotW / 10, padding);
    ctx.lineTo(padding + i * plotW / 10, height - padding);
    ctx.stroke();
  }

  for (let i = 0; i <= 6; i++) {
    ctx.beginPath();
    ctx.moveTo(padding, padding + i * plotH / 6);
    ctx.lineTo(width - padding, padding + i * plotH / 6);
    ctx.stroke();
  }

  ctx.strokeStyle = "#2857b5";
  ctx.lineWidth = 2;
  ctx.strokeRect(padding, padding, plotW, plotH);

  (building.obstacles || []).forEach(obstacle => {
    if (!Array.isArray(obstacle) || obstacle.length < 4) return;
    const [x1, y1, x2, y2] = obstacle;
    ctx.fillStyle = "#afbaca";
    ctx.fillRect(x(x1), y(y2),
      (x2 - x1) / buildingW * plotW,
      (y2 - y1) / buildingH * plotH);
  });

  if (densityToggle.checked && Array.isArray(frame.density)) {
    const matrix = frame.density;
    const rows = matrix.length;
    const cols = rows && Array.isArray(matrix[0])
      ? matrix[0].length : 0;

    if (rows && cols) {
      const maxDensity = Math.max(0, ...matrix.flat().map(v => num(v)));
      if (maxDensity > 0) {
        matrix.forEach((row, r) => row.forEach((value, c) => {
          const intensity = Math.max(0, num(value)) / maxDensity;
          ctx.fillStyle =
            `hsla(${220 - intensity * 220},85%,${94 - intensity * 42}%,0.7)`;
          ctx.fillRect(
            padding + c * plotW / cols,
            padding + r * plotH / rows,
            plotW / cols + 1,
            plotH / rows + 1
          );
        }));
      }
    }
  }

  (state.result.exits || []).forEach(exit => {
    ctx.fillStyle = exit.available === false ? "#dc2626" : "#16a34a";
    ctx.fillRect(x(exit.x) - 8, y(exit.y) - 12, 16, 24);
  });

  (frame.people || []).forEach(person => {
    if (person.evacuated) return;
    ctx.beginPath();
    ctx.fillStyle = "#1d4ed8";
    ctx.arc(x(person.x), y(person.y), 4, 0, Math.PI * 2);
    ctx.fill();
  });

  ctx.fillStyle = "#10233d";
  ctx.font = "bold 12px Arial";
  ctx.textAlign = "left";
  ctx.fillText(`Time: ${num(frame.time).toFixed(2)} s`, 15, 18);
  ctx.fillText(
    `Evacuated: ${num(frame.evacuated_people)}/${num(state.result.total_people)}`,
    15, 34
  );

  updateLiveMetrics(frame);
}

function updateLiveMetrics(frame) {
  const total = num(state.result?.total_people);
  const evacuated = num(frame.evacuated_people);
  const remaining = Math.max(0, total - evacuated);
  const percentage = total > 0 ? evacuated / total * 100 : 0;

  $("liveSimulationTime").textContent = fmt(frame.time, " s");
  $("liveTotalPeople").textContent = total;
  $("liveEvacuatedPeople").textContent = evacuated;
  $("liveRemainingPeople").textContent = remaining;
  $("liveMaxDensity").textContent = fmt(frame.maximum_density);
  $("liveAverageSpeed").textContent = fmt(frame.average_speed, " m/s");
  $("liveProgressText").textContent = `${evacuated} / ${total}`;
  $("liveProgressValue").textContent = `${percentage.toFixed(1)}%`;
  $("liveProgressBar").style.width = `${Math.min(100, percentage)}%`;
}

function renderFrame(index) {
  const timeline = state.result?.timeline || [];
  if (!timeline.length) return;

  state.frameIndex = Math.max(
    0,
    Math.min(Math.floor(index), timeline.length - 1)
  );

  drawLiveFrame(timeline[state.frameIndex]);
}

function stopAnimation() {
  state.playing = false;
  if (state.timerId !== null) {
    cancelAnimationFrame(state.timerId);
    state.timerId = null;
  }
}

function animationLoop(timestamp) {
  if (!state.playing) return;

  if (!state.lastTimestamp) state.lastTimestamp = timestamp;
  const elapsed = timestamp - state.lastTimestamp;
  state.lastTimestamp = timestamp;

  const speed = Math.max(0.1, num(speedControl.value, 1));
  state.accumulator += elapsed * speed;

  // Each frame advances after approximately 50 ms at 1x speed.
  while (state.accumulator >= 50) {
    state.accumulator -= 50;
    state.frameIndex += 1;

    const timeline = state.result?.timeline || [];
    if (state.frameIndex >= timeline.length) {
      state.frameIndex = timeline.length - 1;
      renderFrame(state.frameIndex);
      stopAnimation();
      setStatus("Animation completed.", "success");
      return;
    }
  }

  renderFrame(state.frameIndex);
  state.timerId = requestAnimationFrame(animationLoop);
}

function startAnimation() {
  const timeline = state.result?.timeline || [];

  if (!timeline.length) {
    setStatus("Run a simulation first.", "error");
    return;
  }

  if (state.playing) return;

  if (state.frameIndex >= timeline.length - 1) {
    state.frameIndex = 0;
  }

  state.playing = true;
  state.lastTimestamp = 0;
  state.accumulator = 0;
  setStatus("Animation is running.", "running");
  state.timerId = requestAnimationFrame(animationLoop);
}

function restartAnimation() {
  stopAnimation();
  state.frameIndex = 0;

  if (state.result?.timeline?.length) {
    renderFrame(0);
    setStatus("Animation restarted.", "ready");
  } else {
    setStatus("Run a simulation first.", "error");
  }
}

async function runSimulation() {
  const population = Number(populationInput.value);
  const scenario = scenarioSelect.value;
  const method = methodSelect.value;

  if (!Number.isInteger(population) || population < 1 || population > 1000) {
    setStatus("Enter a whole-number population from 1 to 1000.", "error");
    populationInput.focus();
    return;
  }

  stopAnimation();
  runButton.disabled = true;
  runButton.textContent = "Running...";
  setStatus("Running simulation...", "running");

  try {
    const response = await fetch("/api/simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario, people: population, method })
    });

    const apiData = await response.json();

    if (!response.ok || apiData.success === false || apiData.error) {
      throw new Error(apiData.error || `HTTP error ${response.status}`);
    }

    // Comparison response contains separate Euler and RK4 results.
    const displayData = scenario === "euler_vs_rk4"
      ? apiData.summary?.euler
      : apiData;

    if (!displayData) {
      throw new Error("The backend did not return simulation results.");
    }

    renderMetrics(displayData);
    renderExitUsage(displayData.exit_usage);
    renderEvacuationChart(displayData.history || []);
    renderComparison(apiData);


    // Get density data from the main simulation result.
    let density = displayData.density_matrix;

    // Check whether a matrix contains any positive density values.
    const hasPositiveDensity = (matrix) =>
      Array.isArray(matrix) &&
      matrix.some(
        row =>
          Array.isArray(row) &&
          row.some(value => Number(value) > 0)
      );

    // If the main matrix is empty or all zeros, inspect animation frames.
    if (!hasPositiveDensity(density)) {
      const frames = Array.isArray(displayData.timeline)
        ? displayData.timeline
        : [];

      let bestDensity = null;
      let bestMaximum = 0;

      for (const frame of frames) {
        if (!hasPositiveDensity(frame.density)) {
          continue;
        }

        const maximum = Math.max(
          ...frame.density.flat().map(value => num(value))
        );

        if (maximum > bestMaximum) {
          bestMaximum = maximum;
          bestDensity = frame.density;
        }
      }

      if (bestDensity !== null) {
        density = bestDensity;
      }
    }

    renderDensityMatrix(density || []);


    if (!Array.isArray(density) || !density.length) {
      const frames = displayData.timeline || [];
      const densityFrames = frames.filter(frame =>
        Array.isArray(frame.density) && frame.density.length
      );

      if (densityFrames.length) {
        density = densityFrames.reduce((best, frame) => {
          const value = Math.max(0, ...frame.density.flat().map(v => num(v)));
          const bestValue = best
            ? Math.max(0, ...best.flat().map(v => num(v)))
            : -1;
          return value > bestValue ? frame.density : best;
        }, null);
      }
    }

    renderDensityMatrix(density || []);
    renderEnvironment(displayData);

    state.result = displayData;
    state.frameIndex = 0;

    if (displayData.timeline?.length) {
      renderFrame(0);
    } else {
      const ctx = liveCanvas.getContext("2d");
      ctx.clearRect(0, 0, liveCanvas.width, liveCanvas.height);
      ctx.fillStyle = "#64748b";
      ctx.textAlign = "center";
      ctx.fillText(
        "No animation frames returned by backend",
        liveCanvas.width / 2,
        liveCanvas.height / 2
      );
    }

    setStatus("Simulation completed successfully.", "success");
  } catch (error) {
    console.error("Simulation error:", error);
    setStatus(`Simulation failed: ${error.message}`, "error");
  } finally {
    runButton.disabled = false;
    runButton.textContent = "▶ Run Simulation";
  }
}

scenarioSelect.addEventListener("change", updateMethodState);
runButton.addEventListener("click", runSimulation);
$("startAnimationBtn").addEventListener("click", startAnimation);
$("pauseAnimationBtn").addEventListener("click", () => {
  stopAnimation();
  setStatus("Animation paused.", "ready");
});
$("restartAnimationBtn").addEventListener("click", restartAnimation);

densityToggle.addEventListener("change", () => {
  if (state.result?.timeline?.length) renderFrame(state.frameIndex);
});

updateMethodState();
loadScenarios();
setStatus("Ready to run", "ready");
