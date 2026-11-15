(() => {
  // Si se abre desde Live Server (puerto 5500) apunta a localhost:8000; si se abre desde FastAPI usa ruta relativa
  const API_BASE = window.location.port === "8000" ? "" : "http://localhost:8000";

  let currentHabitat = "lunar_base";
  let envelopeChart = null;
  let allTestsCache = [];

  const habitatBtns = document.querySelectorAll("#dashboard .habitat-btn");
  const rankingBody = document.getElementById("db-ranking-body");
  const testsBody = document.getElementById("db-tests-body");
  const testPsiFilter = document.getElementById("db-test-psi-filter");
  const siForm = document.getElementById("db-si-form");
  const siInput = document.getElementById("db-si-input");
  const phaseFilter = document.getElementById("db-phase-filter");
  const siAnswer = document.getElementById("db-si-answer");
  const vectorCards = document.getElementById("db-vector-cards");

  // 1. Selector de Hábitat Espacial
  habitatBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      habitatBtns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      currentHabitat = btn.dataset.habitat;
      loadRanking();
      runSIInterpretation(siInput.value);
    });
  });

  // 2. Chips de consulta rápida
  document.querySelectorAll("#dashboard .db-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      siInput.value = chip.dataset.query;
      runSIInterpretation(chip.dataset.query);
    });
  });

  // 3. Formulario del Intérprete SI
  siForm.addEventListener("submit", (e) => {
    e.preventDefault();
    runSIInterpretation(siInput.value);
  });

  phaseFilter.addEventListener("change", () => {
    runSIInterpretation(siInput.value);
  });

  testPsiFilter.addEventListener("change", () => {
    renderTestsTable(testPsiFilter.value);
  });

  // Cargar Ranking desde MySQL
  async function loadRanking() {
    try {
      const res = await fetch(`${API_BASE}/api/ranking?habitat=${currentHabitat}`);
      const data = await res.json();

      // Actualizar KPIs
      document.getElementById("kpi-total-inv").textContent = data.length;
      if (data.length > 0) {
        document.getElementById("kpi-top-study").textContent = `${data[0].psi_id}`;
        document.getElementById("kpi-top-score").textContent = `${data[0].acronym} • Score ${data[0].relevance_score}`;
        const maxO2 = Math.max(...data.map((d) => Number(d.max_o2_tested_pct || 0)));
        document.getElementById("kpi-max-o2").textContent = `${maxO2}% O₂`;
      }

      // Poblar selector de filtro de pruebas
      const currentSelected = testPsiFilter.value;
      testPsiFilter.innerHTML = `<option value="">All Investigations (${data.length})</option>` +
        data.map((d) => `<option value="${d.psi_id}">${d.psi_id} — ${d.acronym}</option>`).join("");
      testPsiFilter.value = currentSelected;

      // Renderizar tabla de Ranking
      rankingBody.innerHTML = data.map((row) => `
        <tr data-psi="${row.psi_id}">
          <td><span class="psi-pill">${row.psi_id}</span></td>
          <td><strong>${row.acronym}</strong></td>
          <td>${row.fuel_phase || "-"}</td>
          <td>${row.hardware_rack || "-"} / ${row.hardware_apparatus || "-"}</td>
          <td>${row.max_o2_tested_pct}%</td>
          <td><span class="score-pill">${row.relevance_score}</span></td>
        </tr>
      `).join("");

      // Evento click en filas para abrir Deep-Dive
      rankingBody.querySelectorAll("tr").forEach((tr) => {
        tr.addEventListener("click", () => {
          rankingBody.querySelectorAll("tr").forEach((r) => r.classList.remove("selected-row"));
          tr.classList.add("selected-row");
          loadInvestigationDetail(tr.dataset.psi);
        });
      });

      // Seleccionar automáticamente el primero en el inspector
      if (data.length > 0) {
        rankingBody.querySelector("tr")?.classList.add("selected-row");
        loadInvestigationDetail(data[0].psi_id);
      }
    } catch (err) {
      rankingBody.innerHTML = `<tr><td colspan="6" class="db-muted">Error conectando con MySQL en ${API_BASE}/api/ranking. Verifica que main_api.py esté activo.</td></tr>`;
    }
  }

  // Cargar Pruebas Experimentales desde MySQL y renderizar gráfico
  async function loadTests() {
    try {
      const res = await fetch(`${API_BASE}/api/tests`);
      allTestsCache = await res.json();
      renderTestsTable("");
      renderEnvelopeChart(allTestsCache);
    } catch (err) {
      testsBody.innerHTML = `<tr><td colspan="7" class="db-muted">No se pudieron cargar las pruebas experimentales.</td></tr>`;
    }
  }

  function renderTestsTable(psiFilter) {
    const filtered = psiFilter
      ? allTestsCache.filter((t) => t.psi_id === psiFilter)
      : allTestsCache;

    if (filtered.length === 0) {
      testsBody.innerHTML = `<tr><td colspan="7" class="db-muted">Sin corridas tabulares registradas para este filtro.</td></tr>`;
      return;
    }

    testsBody.innerHTML = filtered.map((t) => `
      <tr>
        <td><code>${t.sample_or_test_id || t.test_uid}</code></td>
        <td><span class="psi-pill">${t.psi_id}</span></td>
        <td>${t.fuel_material} <span class="db-muted">(${t.sample_geometry || "-"})</span></td>
        <td>${t.ambient_pressure_psi} psi</td>
        <td><strong>${t.o2_percentage}%</strong></td>
        <td>${t.airflow_velocity_cm_s} cm/s</td>
        <td>${t.test_outcome || "-"}</td>
      </tr>
    `).join("");
  }

  // Gráfico Chart.js: Presión (psi) vs Oxígeno (%)
  function renderEnvelopeChart(tests) {
    const ctx = document.getElementById("db-envelope-chart");
    if (!ctx || typeof Chart === "undefined") return;

    const psiPoints = tests.map((t) => ({
      x: Number(t.ambient_pressure_psi),
      y: Number(t.o2_percentage),
      label: `${t.psi_id} (${t.acronym}) - ${t.fuel_material}`
    }));

    const referenceEnvironments = [
      { x: 14.7, y: 21, label: "Earth Sea Level (14.7 psi, 21% O₂)" },
      { x: 10.2, y: 30, label: "Lunar Base / Rover Threshold (10.2 psi, 30% O₂)" },
      { x: 4.3, y: 100, label: "EVA Spacesuit (4.3 psi, 100% O₂)" }
    ];

    if (envelopeChart) envelopeChart.destroy();

    envelopeChart = new Chart(ctx, {
      type: "scatter",
      data: {
        datasets: [
          {
            label: "PSI Experimental Runs (MySQL)",
            data: psiPoints,
            backgroundColor: "#38bdf8",
            borderColor: "#e0f2fe",
            borderWidth: 1,
            pointRadius: 7,
            pointHoverRadius: 9
          },
          {
            label: "Mission Reference Envelopes",
            data: referenceEnvironments,
            backgroundColor: "#fbbf24",
            borderColor: "#fef3c7",
            pointStyle: "rectRot",
            pointRadius: 8,
            pointHoverRadius: 10
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: "#cbd5e1", font: { family: "Inter", size: 11 } } },
          tooltip: {
            callbacks: {
              label: (context) => `${context.raw.label}: ${context.raw.x} psi | ${context.raw.y}% O₂`
            }
          }
        },
        scales: {
          x: {
            title: { display: true, text: "Ambient Pressure (psi)", color: "#94a3b8" },
            ticks: { color: "#94a3b8" },
            grid: { color: "rgba(148, 163, 184, 0.12)" },
            min: 0,
            max: 18
          },
          y: {
            title: { display: true, text: "Oxygen Concentration (% O₂)", color: "#94a3b8" },
            ticks: { color: "#94a3b8" },
            grid: { color: "rgba(148, 163, 184, 0.12)" },
            min: 0,
            max: 105
          }
        }
      }
    });
  }

  // Inspección detallada (MySQL + Qdrant)
  async function loadInvestigationDetail(psiId) {
    const badge = document.getElementById("insp-psi-badge");
    const container = document.getElementById("db-inspector-content");
    badge.textContent = psiId;

    try {
      const res = await fetch(`${API_BASE}/api/investigation/${encodeURIComponent(psiId)}`);
      const data = await res.json();
      const inv = data.investigation;
      if (!inv) return;

      const doiHtml = inv.doi && inv.doi !== "N/A"
        ? `<a href="https://doi.org/${inv.doi}" target="_blank" rel="noopener" class="insp-doi-link">${inv.doi} &nearr;</a>`
        : `<span class="db-muted">N/A</span>`;

      const vectorSummary = data.vector_notes && data.vector_notes.length > 0
        ? data.vector_notes[0].text
        : "Sin resumen vectorial adicional cargado aún para este ID.";

      container.innerHTML = `
        <strong>${inv.title}</strong>
        <div class="insp-meta-grid">
          <div class="insp-meta-item"><span>Platform / Type</span>${inv.flight_platform} (${inv.project_type})</div>
          <div class="insp-meta-item"><span>Safety Pillar</span>${inv.safety_pillar}</div>
          <div class="insp-meta-item"><span>Hardware</span>${inv.hardware_rack} — ${inv.hardware_apparatus}</div>
          <div class="insp-meta-item"><span>Dataset DOI</span>${doiHtml}</div>
        </div>
        <p class="db-muted" style="margin: 0.5rem 0 0;">${vectorSummary}</p>
      `;
    } catch (err) {
      container.innerHTML = `<p class="db-muted">No se pudo cargar el detalle de ${psiId}.</p>`;
    }
  }

  // Ejecutar Intérprete SI (/api/interpret)
  async function runSIInterpretation(queryText) {
    const q = (queryText || "").trim();
    if (!q) return;

    siAnswer.textContent = "Consultando vectores en Qdrant y métricas en MySQL...";
    const phase = phaseFilter.value;
    const url = `${API_BASE}/api/interpret?q=${encodeURIComponent(q)}&habitat=${encodeURIComponent(currentHabitat)}`
              + (phase ? `&fuel_phase=${encodeURIComponent(phase)}` : "");

    try {
      const res = await fetch(url);
      const data = await res.json();

      siAnswer.textContent = data.interpretation;

      vectorCards.innerHTML = (data.vector_matches || []).map((item) => `
        <div class="vector-card">
          <div class="vector-card-top">
            <span>${item.psi_id} • ${item.acronym} (${item.fuel_phase})</span>
            <span>Match: ${(item.score * 100).toFixed(1)}%</span>
          </div>
          <p>${item.text}</p>
        </div>
      `).join("");
    } catch (err) {
      siAnswer.textContent = "Error al consultar el intérprete SI. Asegúrate de que python main_api.py esté ejecutándose.";
    }
  }

  // Inicialización al cargar la página
  loadRanking();
  loadTests();
  runSIInterpretation(siInput.value);
})();