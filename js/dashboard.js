(() => {
  const API_BASE = window.location.port === "8000" ? "" : "http://localhost:8000";

  // Estado inicial: Inglés ('en') por defecto y Tema Oscuro ('dark') por defecto
  let currentLang = localStorage.getItem("flame_lang") || "en";
  let currentTheme = localStorage.getItem("flame_theme") || "dark";
  let currentHabitat = "lunar_base";
  let selectedPsiId = null;
  let envelopeChart = null;
  let allTestsCache = [];

  // Diccionario de traducción UI (Inglés por defecto / Español)
  const I18N = {
    en: {
      db_title: "COMBUSTION & FIRE SAFETY INTELLIGENCE",
      db_subtitle: "Comparative analysis of microgravity (0g) flammability and bounding insights for partial-gravity habitats.",
      hab_lunar: "Lunar Base / Rover",
      hab_suit: "EVA Spacesuit",
      hab_iss: "ISS / Spacecraft",
      kpi_inv_label: "PSI Investigations",
      kpi_inv_foot: "Indexed in MySQL & Qdrant",
      kpi_top_label: "Top Habitat Match",
      kpi_top_foot: "Calculating affinity...",
      kpi_o2_label: "Peak O₂ Tested",
      kpi_o2_foot: "Max microgravity oxygen level",
      kpi_grav_label: "Partial-g Bounding",
      kpi_grav_foot: "Bounded via E-FIELD Flames",
      si_title: "SI Semantic Interpreter & Vector Retrieval",
      opt_all_phases: "All Fuel Phases",
      opt_gaseous: "Gaseous",
      opt_liquid: "Liquid",
      opt_solid: "Solid",
      input_placeholder: "Ask in English or Spanish about cool flames, soot in 0g, CO2 suppression, or Lunar Base conditions...",
      default_query: "Which investigations apply to oxygen-enriched atmospheres for a Lunar Base?",
      btn_analyze: "Analyze with SI",
      chip_lunar: "High O₂ Lunar Base",
      chip_flex: "Droplet Suppression (FLEX)",
      chip_bass: "Solids & Airflow (BASS-II)",
      chip_spice: "Microgravity Soot (SPICE)",
      rank_title: "Habitat Relevance Ranking",
      rank_hint: "Click a row to inspect",
      th_acronym: "Acronym",
      th_phase: "Phase",
      th_max_o2: "Max O₂",
      chart_title: "Atmospheric Envelope: Pressure vs. O₂",
      chart_hint: "Lunar Zone ≤10.2 psi / ≥30% O₂",
      insp_title: "Investigation Deep-Dive",
      insp_select: "Select a study",
      insp_empty: "Select any investigation from the ranking table to view its DOI, flight platform, experimental hardware, and vector notes.",
      tests_title: "Normalized Experimental Runs (MySQL)",
      all_inv_opt: "All Investigations",
      th_fuel: "Fuel / Geometry",
      th_press: "Press.",
      th_airflow: "Airflow",
      th_outcome: "Outcome",
      loading_si: "Querying Qdrant vectors and MySQL metrics...",
      no_tests: "No tabular runs registered for this filter.",
      insp_platform: "Platform / Type",
      insp_pillar: "Safety Pillar",
      insp_no_notes: "No additional vector summary loaded yet for this ID.",
      chart_ds_psi: "PSI Experimental Runs (MySQL)",
      chart_ds_ref: "Mission Reference Envelopes",
      chart_x: "Ambient Pressure (psi)",
      chart_y: "Oxygen Concentration (% O₂)",
      theme_to_light: "Light",
      theme_to_dark: "Dark"
    },
    es: {
      db_title: "INTELIGENCIA DE COMBUSTIÓN Y SEGURIDAD CONTRA INCENDIOS",
      db_subtitle: "Análisis comparativo de inflamabilidad en microgravedad (0g) y acotación para hábitats de gravedad parcial.",
      hab_lunar: "Base Lunar / Rover",
      hab_suit: "Traje Espacial EVA",
      hab_iss: "ISS / Nave Espacial",
      kpi_inv_label: "Investigaciones PSI",
      kpi_inv_foot: "Indexadas en MySQL y Qdrant",
      kpi_top_label: "Mayor Afinidad Hábitat",
      kpi_top_foot: "Calculando afinidad...",
      kpi_o2_label: "Máx. O₂ Probado",
      kpi_o2_foot: "Concentración máxima en microgravedad",
      kpi_grav_label: "Acotación Gravedad Parcial",
      kpi_grav_foot: "Acotado vía E-FIELD Flames",
      si_title: "Intérprete Semántico SI y Recuperación Vectorial",
      opt_all_phases: "Todas las Fases",
      opt_gaseous: "Gaseoso",
      opt_liquid: "Líquido",
      opt_solid: "Sólido",
      input_placeholder: "Pregunta en inglés o español sobre llamas frías, hollín en 0g, supresión con CO2 o Base Lunar...",
      default_query: "¿Qué investigaciones aplican a atmósferas enriquecidas en oxígeno para la Base Lunar?",
      btn_analyze: "Analizar con SI",
      chip_lunar: "Alto O₂ Base Lunar",
      chip_flex: "Supresión en Gotas (FLEX)",
      chip_bass: "Sólidos y Flujo de Aire (BASS-II)",
      chip_spice: "Hollín en Microgravedad (SPICE)",
      rank_title: "Ranking de Relevancia por Hábitat",
      rank_hint: "Haz clic en una fila para inspeccionar",
      th_acronym: "Acrónimo",
      th_phase: "Fase",
      th_max_o2: "Máx O₂",
      chart_title: "Envolvente Atmosférica: Presión vs. O₂",
      chart_hint: "Zona Lunar ≤10.2 psi / ≥30% O₂",
      insp_title: "Inspección Detallada de Investigación",
      insp_select: "Selecciona un estudio",
      insp_empty: "Selecciona cualquier investigación de la tabla de ranking para ver su DOI, plataforma de vuelo, hardware y notas vectoriales.",
      tests_title: "Corridas Experimentales Normalizadas (MySQL)",
      all_inv_opt: "Todas las Investigaciones",
      th_fuel: "Combustible / Geometría",
      th_press: "Presión",
      th_airflow: "Flujo Aire",
      th_outcome: "Resultado",
      loading_si: "Consultando vectores en Qdrant y métricas en MySQL...",
      no_tests: "Sin corridas tabulares registradas para este filtro.",
      insp_platform: "Plataforma / Tipo",
      insp_pillar: "Pilar de Seguridad",
      insp_no_notes: "Sin resumen vectorial adicional cargado aún para este ID.",
      chart_ds_psi: "Pruebas Experimentales PSI (MySQL)",
      chart_ds_ref: "Envolventes de Referencia de Misión",
      chart_x: "Presión Ambiente (psi)",
      chart_y: "Concentración de Oxígeno (% O₂)",
      theme_to_light: "Claro",
      theme_to_dark: "Oscuro"
    }
  };

  // Referencias DOM
  const langToggleBtn = document.getElementById("btn-lang-toggle");
  const themeToggleBtn = document.getElementById("btn-theme-toggle");
  const habitatBtns = document.querySelectorAll("#dashboard .habitat-btn");
  const rankingBody = document.getElementById("db-ranking-body");
  const testsBody = document.getElementById("db-tests-body");
  const testPsiFilter = document.getElementById("db-test-psi-filter");
  const siForm = document.getElementById("db-si-form");
  const siInput = document.getElementById("db-si-input");
  const phaseFilter = document.getElementById("db-phase-filter");
  const siAnswer = document.getElementById("db-si-answer");
  const vectorCards = document.getElementById("db-vector-cards");

  // =========================================================
  // A. Gestión de Tema (Dark / Light)
  // =========================================================
  function applyTheme(theme) {
    currentTheme = theme;
    localStorage.setItem("flame_theme", theme);
    const isLight = theme === "light";
    document.body.classList.toggle("light-theme", isLight);

    const iconSun = document.getElementById("icon-sun");
    const iconMoon = document.getElementById("icon-moon");
    const themeLabel = document.getElementById("theme-label");

    if (iconSun && iconMoon && themeLabel) {
      iconSun.hidden = !isLight;
      iconMoon.hidden = isLight;
      themeLabel.textContent = isLight ? I18N[currentLang].theme_to_dark : I18N[currentLang].theme_to_light;
    }

    if (allTestsCache.length > 0) {
      renderEnvelopeChart(allTestsCache);
    }
  }

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener("click", () => {
      applyTheme(currentTheme === "dark" ? "light" : "dark");
    });
  }

  // =========================================================
  // B. Gestión de Idioma (EN por defecto / ES)
  // =========================================================
  function applyLanguage(lang) {
    currentLang = lang;
    localStorage.setItem("flame_lang", lang);
    document.documentElement.lang = lang;

    const dict = I18N[lang];

    // Actualizar indicadores EN / ES en el navbar
    document.querySelectorAll(".navbar .lang-pill").forEach((pill) => {
      pill.classList.toggle("active", pill.dataset.lang === lang);
    });

    // Traducir elementos etiquetados con data-i18n
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.dataset.i18n;
      if (dict[key]) {
        el.textContent = dict[key];
      }
    });

    // Actualizar placeholder y pregunta por defecto si no fue editada manualmente
    siInput.placeholder = dict.input_placeholder;
    const prevDefault = lang === "es" ? I18N.en.default_query : I18N.es.default_query;
    if (siInput.value.trim() === prevDefault || siInput.value.trim() === "") {
      siInput.value = dict.default_query;
    }

    // Actualizar texto del botón de tema
    const themeLabel = document.getElementById("theme-label");
    if (themeLabel) {
      themeLabel.textContent = currentTheme === "light" ? dict.theme_to_dark : dict.theme_to_light;
    }

    // Re-renderizar componentes dinámicos con etiquetas del idioma activo
    renderTestsTable(testPsiFilter.value);
    if (selectedPsiId) {
      loadInvestigationDetail(selectedPsiId);
    }
    if (allTestsCache.length > 0) {
      renderEnvelopeChart(allTestsCache);
    }
  }

  if (langToggleBtn) {
    langToggleBtn.addEventListener("click", () => {
      applyLanguage(currentLang === "en" ? "es" : "en");
    });
  }

  // =========================================================
  // C. Eventos del Dashboard (Hábitats, Chips, Formulario)
  // =========================================================
  habitatBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      habitatBtns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      currentHabitat = btn.dataset.habitat;
      loadRanking();
      runSIInterpretation(siInput.value);
    });
  });

  document.querySelectorAll("#dashboard .db-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      const queryToRun = currentLang === "es" ? chip.dataset.queryEs : chip.dataset.queryEn;
      siInput.value = queryToRun;
      runSIInterpretation(queryToRun);
    });
  });

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

  // =========================================================
  // D. Consumo de Endpoints (MySQL + Qdrant + Gemini)
  // =========================================================
  async function loadRanking() {
    try {
      const res = await fetch(`${API_BASE}/api/ranking?habitat=${currentHabitat}`);
      const data = await res.json();

      document.getElementById("kpi-total-inv").textContent = data.length;
      if (data.length > 0) {
        document.getElementById("kpi-top-study").textContent = `${data[0].psi_id}`;
        document.getElementById("kpi-top-score").textContent = `${data[0].acronym} • Score ${data[0].relevance_score}`;
        const maxO2 = Math.max(...data.map((d) => Number(d.max_o2_tested_pct || 0)));
        document.getElementById("kpi-max-o2").textContent = `${maxO2}% O₂`;
      }

      const currentSelected = testPsiFilter.value;
      testPsiFilter.innerHTML = `<option value="">${I18N[currentLang].all_inv_opt} (${data.length})</option>` +
        data.map((d) => `<option value="${d.psi_id}">${d.psi_id} — ${d.acronym}</option>`).join("");
      testPsiFilter.value = currentSelected;

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

      rankingBody.querySelectorAll("tr").forEach((tr) => {
        tr.addEventListener("click", () => {
          rankingBody.querySelectorAll("tr").forEach((r) => r.classList.remove("selected-row"));
          tr.classList.add("selected-row");
          selectedPsiId = tr.dataset.psi;
          loadInvestigationDetail(selectedPsiId);
        });
      });

      if (data.length > 0) {
        rankingBody.querySelector("tr")?.classList.add("selected-row");
        selectedPsiId = data[0].psi_id;
        loadInvestigationDetail(selectedPsiId);
      }
    } catch (err) {
      rankingBody.innerHTML = `<tr><td colspan="6" class="db-muted">Error connecting to MySQL at ${API_BASE}/api/ranking. Verify main_api.py is running.</td></tr>`;
    }
  }

  async function loadTests() {
    try {
      const res = await fetch(`${API_BASE}/api/tests`);
      allTestsCache = await res.json();
      renderTestsTable("");
      renderEnvelopeChart(allTestsCache);
    } catch (err) {
      testsBody.innerHTML = `<tr><td colspan="7" class="db-muted">Could not load experimental runs.</td></tr>`;
    }
  }

  function renderTestsTable(psiFilter) {
    const filtered = psiFilter
      ? allTestsCache.filter((t) => t.psi_id === psiFilter)
      : allTestsCache;

    if (filtered.length === 0) {
      testsBody.innerHTML = `<tr><td colspan="7" class="db-muted">${I18N[currentLang].no_tests}</td></tr>`;
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

  function renderEnvelopeChart(tests) {
    const ctx = document.getElementById("db-envelope-chart");
    if (!ctx || typeof Chart === "undefined") return;

    const isLight = currentTheme === "light";
    const textColor = isLight ? "#334155" : "#94a3b8";
    const legendColor = isLight ? "#0f172a" : "#cbd5e1";
    const gridColor = isLight ? "rgba(15, 23, 42, 0.1)" : "rgba(148, 163, 184, 0.12)";
    const dict = I18N[currentLang];

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
            label: dict.chart_ds_psi,
            data: psiPoints,
            backgroundColor: isLight ? "#0284c7" : "#38bdf8",
            borderColor: isLight ? "#0369a1" : "#e0f2fe",
            borderWidth: 1,
            pointRadius: 7,
            pointHoverRadius: 9
          },
          {
            label: dict.chart_ds_ref,
            data: referenceEnvironments,
            backgroundColor: isLight ? "#d97706" : "#fbbf24",
            borderColor: isLight ? "#92400e" : "#fef3c7",
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
          legend: { labels: { color: legendColor, font: { family: "Inter", size: 11 } } },
          tooltip: {
            callbacks: {
              label: (context) => `${context.raw.label}: ${context.raw.x} psi | ${context.raw.y}% O₂`
            }
          }
        },
        scales: {
          x: {
            title: { display: true, text: dict.chart_x, color: textColor },
            ticks: { color: textColor },
            grid: { color: gridColor },
            min: 0,
            max: 18
          },
          y: {
            title: { display: true, text: dict.chart_y, color: textColor },
            ticks: { color: textColor },
            grid: { color: gridColor },
            min: 0,
            max: 105
          }
        }
      }
    });
  }

  async function loadInvestigationDetail(psiId) {
    const badge = document.getElementById("insp-psi-badge");
    const container = document.getElementById("db-inspector-content");
    const dict = I18N[currentLang];
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
        : dict.insp_no_notes;

      container.innerHTML = `
        <strong>${inv.title}</strong>
        <div class="insp-meta-grid">
          <div class="insp-meta-item"><span>${dict.insp_platform}</span>${inv.flight_platform} (${inv.project_type})</div>
          <div class="insp-meta-item"><span>${dict.insp_pillar}</span>${inv.safety_pillar}</div>
          <div class="insp-meta-item"><span>Hardware</span>${inv.hardware_rack} — ${inv.hardware_apparatus}</div>
          <div class="insp-meta-item"><span>Dataset DOI</span>${doiHtml}</div>
        </div>
        <p class="db-muted" style="margin: 0.5rem 0 0;">${vectorSummary}</p>
      `;
    } catch (err) {
      container.innerHTML = `<p class="db-muted">Could not load details for ${psiId}.</p>`;
    }
  }

  async function runSIInterpretation(queryText) {
    const q = (queryText || "").trim();
    if (!q) return;

    siAnswer.textContent = I18N[currentLang].loading_si;
    const phase = phaseFilter.value;
    const url = `${API_BASE}/api/interpret?q=${encodeURIComponent(q)}&habitat=${encodeURIComponent(currentHabitat)}&ui_lang=${currentLang}`
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
      siAnswer.textContent = "Error querying SI interpreter. Make sure python main_api.py is running.";
    }
  }

  // Inicialización respetando preferencias (Inglés + Oscuro por defecto)
  applyTheme(currentTheme);
  applyLanguage(currentLang);
  loadRanking();
  loadTests();
  runSIInterpretation(siInput.value);
})();