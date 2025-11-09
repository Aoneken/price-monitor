// ========================================
// PRICE MONITOR - Main Application Logic
// ========================================

// State Management
let state = {
  currentWorkspace: null,
  currentSeason: null,
  deleteCallback: null,
  selectedListings: new Set(),
  charts: {},
  websockets: {},
};

// ========================================
// INITIALIZATION
// ========================================

document.addEventListener("DOMContentLoaded", () => {
  console.log("🚀 Price Monitor initialized");
  loadWorkspaces();
  setupEventListeners();
});

function setupEventListeners() {
  // Workspace selector
  const focusSelect = document.getElementById("focus-select");
  if (focusSelect) {
    focusSelect.addEventListener("change", (e) =>
      selectWorkspace(e.target.value)
    );
  }

  // Season selector
  const seasonSelect = document.getElementById("season-select");
  if (seasonSelect) {
    seasonSelect.addEventListener("change", (e) => {
      if (e.target.value) {
        state.currentSeason = { id: parseInt(e.target.value, 10) };
        updateUIState();
      } else {
        state.currentSeason = null;
      }
    });
  }

  // Provider selector in scraping tab
  const providerSelect = document.getElementById("bulk-provider");
  if (providerSelect) {
    providerSelect.addEventListener("change", () => {
      // Clear selections when provider changes
      state.selectedListings.clear();
      loadScrapingListings();
    });
  }

  // New focus form
  const newFocusForm = document.getElementById("new-focus-form");
  if (newFocusForm) {
    newFocusForm.addEventListener("submit", createWorkspace);
  }

  // Bulk scrape form
  const bulkScrapeForm = document.getElementById("bulk-scrape-form");
  if (bulkScrapeForm) {
    bulkScrapeForm.addEventListener("submit", startBulkScrape);
  }

  // Close modals on outside click
  document.querySelectorAll(".modal").forEach((modal) => {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) {
        closeModal(modal.id);
      }
    });
  });
}

// ========================================
// TAB MANAGEMENT
// ========================================

function switchTab(tabName, ev) {
  // Update tab buttons
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.classList.remove("active");
  });
  if (ev && ev.target) {
    const button = ev.target.closest(".tab");
    if (button) button.classList.add("active");
  }

  // Update tab content
  document.querySelectorAll(".tab-content").forEach((content) => {
    content.classList.remove("active");
  });
  const el = document.getElementById(tabName + "-tab");
  if (el) el.classList.add("active");

  // Load tab-specific data
  if (tabName === "scraping") {
    loadScrapingTab();
  } else if (tabName === "jobs") {
    loadJobs();
  } else if (tabName === "analytics") {
    loadAnalyticsTab();
  }
}

function switchConfigSubtab(name, ev) {
  // Toggle subtab button style
  document.querySelectorAll(".subtab-btn").forEach((b) => {
    b.classList.remove("active");
  });
  if (ev && ev.target) {
    const button = ev.target.closest(".subtab-btn");
    if (button) button.classList.add("active");
  }

  // Hide all subtab containers
  document.querySelectorAll(".subtab-content").forEach((c) => {
    c.style.display = "none";
  });
  const target = document.getElementById(`config-${name}`);
  if (target) target.style.display = "block";
}

// ========================================
// MODAL MANAGEMENT
// ========================================

function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.add("active");
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.remove("active");
}

function openNewFocusModal() {
  openModal("new-focus-modal");
}

function openDeleteModal(message, callback) {
  const messageEl = document.getElementById("delete-message");
  if (messageEl) messageEl.textContent = message;
  state.deleteCallback = callback;
  openModal("delete-modal");
}

function confirmDelete() {
  if (state.deleteCallback) {
    state.deleteCallback();
    state.deleteCallback = null;
  }
  closeModal("delete-modal");
}

// ========================================
// WORKSPACE MANAGEMENT
// ========================================

async function loadWorkspaces() {
  try {
    const response = await fetch("/api/workspaces");
    const workspaces = await response.json();

    const select = document.getElementById("focus-select");
    if (!select) return;

    select.innerHTML = '<option value="">Seleccionar workspace...</option>';

    workspaces.forEach((ws) => {
      const option = document.createElement("option");
      option.value = ws.id;
      option.textContent = ws.name;
      if (state.currentWorkspace && state.currentWorkspace.id === ws.id) {
        option.selected = true;
      }
      select.appendChild(option);
    });

    // Auto-select if only one workspace
    if (workspaces.length === 1 && !state.currentWorkspace) {
      select.value = workspaces[0].id;
      await selectWorkspace(workspaces[0].id);
    }
  } catch (error) {
    console.error("Error loading workspaces:", error);
    showToast("Error al cargar workspaces", "danger");
  }
}

async function selectWorkspace(workspaceId) {
  if (!workspaceId) {
    state.currentWorkspace = null;
    state.currentSeason = null;
    showEmptyStates();
    hideStats();
    return;
  }

  try {
    const response = await fetch(`/api/workspaces/${workspaceId}`);
    state.currentWorkspace = await response.json();
    await loadWorkspaceData();
    showStats();
    updateStats();
  } catch (error) {
    console.error("Error loading workspace:", error);
    showToast("Error al cargar workspace", "danger");
  }
}

async function createWorkspace(e) {
  e.preventDefault();
  const name = document.getElementById("workspace-name").value;

  try {
    const response = await fetch("/api/workspaces", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });

    if (response.ok) {
      const newWorkspace = await response.json();
      closeModal("new-focus-modal");
      document.getElementById("workspace-name").value = "";
      await loadWorkspaces();

      // Auto-select new workspace
      document.getElementById("focus-select").value = newWorkspace.id;
      await selectWorkspace(newWorkspace.id);

      showToast("✅ Workspace creado correctamente");
    } else {
      showToast("❌ Error al crear workspace", "danger");
    }
  } catch (error) {
    console.error("Error creating workspace:", error);
    showToast("❌ Error al crear workspace", "danger");
  }
}

async function updateWorkspace(e) {
  e.preventDefault();
  const name = document.getElementById("edit-workspace-name").value;

  try {
    await fetch(`/api/workspaces/${state.currentWorkspace.id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
    state.currentWorkspace.name = name;
    loadWorkspaces();
    showToast("✅ Workspace actualizado");
  } catch (error) {
    showToast("❌ Error al actualizar workspace", "danger");
  }
}

async function deleteWorkspace() {
  openDeleteModal(
    `Se eliminará el workspace "${state.currentWorkspace.name}" y todos sus datos asociados.`,
    async () => {
      try {
        await fetch(`/api/workspaces/${state.currentWorkspace.id}`, {
          method: "DELETE",
        });
        state.currentWorkspace = null;
        state.currentSeason = null;
        document.getElementById("focus-select").value = "";
        loadWorkspaces();
        showEmptyStates();
        hideStats();
        showToast("✅ Workspace eliminado");
      } catch (error) {
        showToast("❌ Error al eliminar workspace", "danger");
      }
    }
  );
}

// ========================================
// WORKSPACE DATA LOADING
// ========================================

async function loadWorkspaceData() {
  if (!state.currentWorkspace) return;

  loadConfigTab();
  loadSeasonsTab();
  loadListingsTab();
}

function showEmptyStates() {
  const configTab = document.getElementById("config-tab");
  if (!configTab) return;

  // Restore default empty state
  const settingsEl = document.getElementById("config-settings");
  if (settingsEl) {
    settingsEl.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">🎯</div>
        <h3>Selecciona o crea un Workspace</h3>
        <p>Los workspaces te permiten organizar tus temporadas y establecimientos.</p>
        <button class="btn btn-primary" onclick="openNewFocusModal()">
          ➕ Crear Primer Workspace
        </button>
      </div>
    `;
  }
}

function loadConfigTab() {
  if (!state.currentWorkspace) return;

  const settingsEl = document.getElementById("config-settings");
  if (!settingsEl) return;

  settingsEl.innerHTML = `
    <div class="form-section">
      <h3>⚙️ Configuración del Workspace</h3>
      <div class="info-box" style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:1rem;">
        <div class="stat-card">
          <div class="stat-icon">📝</div>
          <div class="stat-content">
            <div class="stat-label">Nombre</div>
            <div class="stat-value" style="font-size:1.25rem;">${
              state.currentWorkspace.name
            }</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">📅</div>
          <div class="stat-content">
            <div class="stat-label">Creado</div>
            <div class="stat-value" style="font-size:1.25rem;">${new Date(
              state.currentWorkspace.created_at
            ).toLocaleDateString()}</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">🔑</div>
          <div class="stat-content">
            <div class="stat-label">ID</div>
            <div class="stat-value" style="font-size:1.25rem;">#${
              state.currentWorkspace.id
            }</div>
          </div>
        </div>
      </div>
      <form id="edit-workspace-form" style="margin-top:2rem;">
        <div class="form-group">
          <label>Renombrar Workspace</label>
          <input type="text" id="edit-workspace-name" value="${escapeHtml(
            state.currentWorkspace.name
          )}" />
        </div>
        <div class="form-actions">
          <button type="button" class="btn btn-danger" onclick="deleteWorkspace()">🗑️ Eliminar Workspace</button>
          <button type="submit" class="btn btn-success">💾 Guardar Cambios</button>
        </div>
      </form>
    </div>
  `;

  const form = document.getElementById("edit-workspace-form");
  if (form) form.addEventListener("submit", updateWorkspace);
}

// ========================================
// SEASONS MANAGEMENT
// ========================================

function loadSeasonsTab() {
  if (!state.currentWorkspace) return;

  const container = document.getElementById("config-seasons");
  if (!container) return;

  container.innerHTML = `
    <div class="form-section">
      <h3>➕ Nueva Temporada</h3>
      <form id="new-season-form">
        <div class="form-grid">
          <div class="form-group">
            <label>Nombre *</label>
            <input type="text" id="season-name" placeholder="Ej: Temporada Alta 2025" required />
          </div>
          <div class="form-group">
            <label>Fecha Inicio *</label>
            <input type="date" id="season-start" required />
          </div>
          <div class="form-group">
            <label>Fecha Fin *</label>
            <input type="date" id="season-end" required />
          </div>
        </div>
        <div class="form-actions">
          <button type="submit" class="btn btn-success">➕ Crear Temporada</button>
        </div>
      </form>
    </div>

    <div class="mt-2">
      <h3 style="margin-bottom: 1rem;">📅 Temporadas Existentes</h3>
      <div class="table-container">
        <table class="data-table" id="seasons-table">
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Fecha Inicio</th>
              <th>Fecha Fin</th>
              <th>Duración</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody id="seasons-tbody">
            <tr>
              <td colspan="5" class="text-center text-muted">Cargando...</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  `;

  const form = document.getElementById("new-season-form");
  if (form) form.addEventListener("submit", createSeason);

  loadSeasons();
}

async function loadSeasons() {
  if (!state.currentWorkspace) return;

  try {
    const response = await fetch(
      `/api/workspaces/${state.currentWorkspace.id}/seasons`
    );
    const seasons = await response.json();

    // Update header season selector
    const seasonSelect = document.getElementById("season-select");
    if (seasonSelect) {
      seasonSelect.innerHTML = "";
      if (!seasons || seasons.length === 0) {
        const opt = document.createElement("option");
        opt.value = "";
        opt.textContent = "No hay temporadas";
        opt.disabled = true;
        seasonSelect.appendChild(opt);
        seasonSelect.disabled = true;
        state.currentSeason = null;
      } else {
        const placeholder = document.createElement("option");
        placeholder.value = "";
        placeholder.textContent = "Seleccionar temporada...";
        seasonSelect.appendChild(placeholder);

        seasons.forEach((s) => {
          const opt = document.createElement("option");
          opt.value = s.id;
          opt.textContent = `${s.name} (${s.start_date} → ${s.end_date})`;
          seasonSelect.appendChild(opt);
        });
        seasonSelect.disabled = false;

        // Auto-select if only one
        if (!state.currentSeason && seasons.length === 1) {
          seasonSelect.value = seasons[0].id;
          state.currentSeason = { id: seasons[0].id };
        } else if (state.currentSeason) {
          seasonSelect.value = state.currentSeason.id;
        }
      }
    }

    const tbody = document.getElementById("seasons-tbody");
    if (!tbody) return;

    if (seasons.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="5" class="text-center text-muted">
            No hay temporadas. Crea una usando el formulario arriba.
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = seasons
      .map((season) => {
        const start = new Date(season.start_date);
        const end = new Date(season.end_date);
        const days = Math.ceil((end - start) / (1000 * 60 * 60 * 24));

        return `
        <tr>
          <td><strong>${escapeHtml(season.name)}</strong></td>
          <td>${season.start_date}</td>
          <td>${season.end_date}</td>
          <td>${days} días</td>
          <td class="table-actions">
            <button class="btn btn-danger btn-small" onclick="deleteSeason(${
              season.id
            }, '${escapeForJs(season.name)}')">
              🗑️ Eliminar
            </button>
          </td>
        </tr>
      `;
      })
      .join("");

    updateStats();
  } catch (error) {
    console.error("Error loading seasons:", error);
  }
}

async function createSeason(e) {
  e.preventDefault();
  const data = {
    name: document.getElementById("season-name").value,
    start_date: document.getElementById("season-start").value,
    end_date: document.getElementById("season-end").value,
  };

  try {
    await fetch(`/api/workspaces/${state.currentWorkspace.id}/seasons`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    document.getElementById("new-season-form").reset();
    loadSeasons();
    showToast("✅ Temporada creada");
  } catch (error) {
    showToast("❌ Error al crear temporada", "danger");
  }
}

async function deleteSeason(seasonId, seasonName) {
  openDeleteModal(`Se eliminará la temporada "${seasonName}".`, async () => {
    try {
      await fetch(`/api/seasons/${seasonId}`, {
        method: "DELETE",
      });
      loadSeasons();
      showToast("✅ Temporada eliminada");
    } catch (error) {
      showToast("❌ Error al eliminar temporada", "danger");
    }
  });
}

// ========================================
// LISTINGS MANAGEMENT
// ========================================

function loadListingsTab() {
  if (!state.currentWorkspace) return;

  const container = document.getElementById("config-listings");
  if (!container) return;

  container.innerHTML = `
    <div class="form-section">
      <h3>➕ Nuevo Establecimiento</h3>
      <form id="new-listing-form">
        <div class="form-grid">
          <div class="form-group">
            <label>Nombre *</label>
            <input type="text" id="listing-name" placeholder="Ej: Cabaña Lago Azul" required />
          </div>
          <div class="form-group">
            <label>ID del Listing *</label>
            <input type="text" id="listing-id" placeholder="Ej: 1234567890" required />
          </div>
          <div class="form-group">
            <label>URL</label>
            <input type="url" id="listing-url" placeholder="https://www.airbnb.com.ar/rooms/..." />
          </div>
          <div class="form-group">
            <label>Proveedor</label>
            <select id="listing-provider">
              <option value="airbnb">Airbnb</option>
              <option value="booking">Booking</option>
              <option value="expedia">Expedia</option>
            </select>
          </div>
        </div>
        <div class="form-actions">
          <button type="submit" class="btn btn-success">➕ Agregar Establecimiento</button>
        </div>
      </form>
    </div>

    <div class="mt-2">
      <h3 style="margin-bottom: 1rem;">🏠 Establecimientos</h3>
      <div class="table-container">
        <table class="data-table" id="listings-table">
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Listing ID</th>
              <th>Proveedor</th>
              <th>URL</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody id="listings-tbody">
            <tr>
              <td colspan="5" class="text-center text-muted">Cargando...</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  `;

  const form = document.getElementById("new-listing-form");
  if (form) form.addEventListener("submit", createListing);

  loadListings();
}

async function loadListings() {
  if (!state.currentWorkspace) return;

  try {
    const response = await fetch("/api/listings");
    let listings = await response.json();

    // Filter by current workspace if available
    if (state.currentWorkspace) {
      listings = listings.filter(
        (l) => l.workspace_id === state.currentWorkspace.id
      );
    }

    const tbody = document.getElementById("listings-tbody");
    if (!tbody) return;

    if (listings.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="5" class="text-center text-muted">
            No hay establecimientos. Agrega uno usando el formulario arriba.
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = listings
      .map((listing) => {
        // Generate provider badges from platform_sources
        let providerBadges = "";
        if (listing.platform_sources && listing.platform_sources.length > 0) {
          providerBadges = listing.platform_sources
            .map((ps) => {
              const isSupported = ps.extra_data?.supported !== false;
              const badgeClass = isSupported
                ? "badge-success"
                : "badge-secondary";
              const platformLabel = ps.platform.toUpperCase();
              const supportLabel = isSupported ? "" : " (sin soporte)";
              return `<span class="badge ${badgeClass}">${platformLabel}${supportLabel}</span>`;
            })
            .join(" ");
        } else {
          // Fallback to legacy provider field
          providerBadges = `<span class="badge badge-primary">${listing.provider}</span>`;
        }

        return `
        <tr>
          <td><strong>${escapeHtml(listing.name)}</strong></td>
          <td><code>${escapeHtml(listing.listing_id)}</code></td>
          <td>${providerBadges}</td>
          <td>
            ${
              listing.url
                ? `<a href="${escapeHtml(
                    listing.url
                  )}" target="_blank" style="color: var(--primary);">🔗 Ver</a>`
                : "-"
            }
          </td>
          <td class="table-actions">
            <button class="btn btn-primary btn-small" onclick="viewListingPrices(${
              listing.id
            })">📊 Precios</button>
            <button class="btn btn-danger btn-small" onclick="deleteListing(${
              listing.id
            }, '${escapeForJs(listing.name)}')">🗑️</button>
          </td>
        </tr>
      `;
      })
      .join("");

    updateStats();
  } catch (error) {
    console.error("Error loading listings:", error);
  }
}

async function createListing(e) {
  e.preventDefault();
  const data = {
    listing_id: document.getElementById("listing-id").value,
    name: document.getElementById("listing-name").value,
    url: document.getElementById("listing-url").value,
    provider: document.getElementById("listing-provider").value,
    workspace_id: state.currentWorkspace.id,
  };

  try {
    await fetch("/api/listings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    document.getElementById("new-listing-form").reset();
    loadListings();
    showToast("✅ Establecimiento agregado");
  } catch (error) {
    showToast("❌ Error al agregar establecimiento", "danger");
  }
}

async function deleteListing(listingId, listingName) {
  openDeleteModal(
    `Se eliminará el establecimiento "${listingName}".`,
    async () => {
      try {
        await fetch(`/api/listings/${listingId}`, {
          method: "DELETE",
        });
        loadListings();
        showToast("✅ Establecimiento eliminado");
      } catch (error) {
        showToast("❌ Error al eliminar establecimiento", "danger");
      }
    }
  );
}

function viewListingPrices(listingId) {
  // Switch to analytics tab and load prices for this listing
  switchTab("analytics", null);
  const select = document.getElementById("analytics-listing");
  if (select) {
    select.value = listingId;
    loadAnalytics();
  }
}

// ========================================
// SCRAPING TAB
// ========================================

function loadScrapingTab() {
  if (!state.currentWorkspace) {
    const selector = document.getElementById("scraping-listings-selector");
    if (selector) {
      selector.innerHTML =
        '<p class="text-muted">Selecciona un workspace primero...</p>';
    }
    return;
  }

  loadScrapingListings();
}

async function loadScrapingListings() {
  const selector = document.getElementById("scraping-listings-selector");
  if (!selector) return;

  try {
    const response = await fetch("/api/listings");
    let listings = await response.json();

    if (state.currentWorkspace) {
      listings = listings.filter(
        (l) => l.workspace_id === state.currentWorkspace.id
      );
    }

    if (listings.length === 0) {
      selector.innerHTML = `
        <p class="text-muted">No hay establecimientos.
        <a href="#" onclick="switchTab('config', null); switchConfigSubtab('listings', null); return false;">Añade uno aquí</a>
        </p>
      `;
      return;
    }

    // Get selected provider
    const providerSelect = document.getElementById("bulk-provider");
    const selectedProvider = providerSelect ? providerSelect.value : "airbnb";

    // Filter listings by selected provider availability
    const availableListings = listings.filter((listing) => {
      if (!listing.platform_sources || listing.platform_sources.length === 0) {
        return selectedProvider === "airbnb"; // Fallback to airbnb for legacy data
      }
      return listing.platform_sources.some(
        (ps) =>
          ps.platform === selectedProvider && ps.extra_data?.supported !== false
      );
    });

    if (availableListings.length === 0) {
      selector.innerHTML = `
        <p class="text-muted">No hay establecimientos con soporte para ${selectedProvider.toUpperCase()}.</p>
      `;
      return;
    }

    selector.innerHTML = availableListings
      .map(
        (listing) => `
        <label class="listing-checkbox">
          <input type="checkbox" value="${
            listing.id
          }" onchange="toggleListingSelection(${listing.id})" />
          <span>${escapeHtml(listing.name)}</span>
        </label>
      `
      )
      .join("");
  } catch (error) {
    console.error("Error loading scraping listings:", error);
  }
}

function toggleListingSelection(listingId) {
  if (state.selectedListings.has(listingId)) {
    state.selectedListings.delete(listingId);
  } else {
    state.selectedListings.add(listingId);
  }
}

async function startBulkScrape(e) {
  e.preventDefault();

  if (!state.currentWorkspace || !state.currentSeason) {
    showToast("Selecciona workspace y temporada primero", "warning");
    return;
  }

  if (state.selectedListings.size === 0) {
    showToast("Selecciona al menos un establecimiento", "warning");
    return;
  }

  const data = {
    establishments: Array.from(state.selectedListings),
    platform: "airbnb",
    params: {
      guests: parseInt(document.getElementById("bulk-guests").value || "2", 10),
      currency: document.getElementById("bulk-currency").value || "USD",
      start_date: document.getElementById("bulk-start").value,
      end_date: document.getElementById("bulk-end").value,
    },
  };

  try {
    const resp = await fetch(`/api/seasons/${state.currentSeason.id}/scrape`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    if (!resp.ok) {
      const txt = await resp.text();
      showToast(`Error: ${txt}`, "danger");
      return;
    }

    const result = await resp.json();
    const jobId = result.id || result.job_id || result.jobId;

    showToast(`✅ Job ${jobId} iniciado`);
    openModal("scrape-modal");

    if (jobId) {
      connectScrapeWS(jobId);
    }

    // Clear selections
    state.selectedListings.clear();
    document
      .querySelectorAll(".listing-checkbox input")
      .forEach((cb) => (cb.checked = false));
  } catch (err) {
    console.error(err);
    showToast("Error al iniciar scrape", "danger");
  }
}

// ========================================
// WEBSOCKET FOR SCRAPE PROGRESS
// ========================================

function connectScrapeWS(jobId) {
  const proto = location.protocol === "https:" ? "wss:" : "ws:";
  const url = `${proto}//${location.host}/ws/scrape-jobs/${jobId}`;

  let ws;
  try {
    ws = new WebSocket(url);
  } catch (e) {
    appendScrapeLog("⚠️ WebSocket no disponible");
    return;
  }

  state.websockets[jobId] = ws;
  appendScrapeLog(`Conectando a job ${jobId}...`);

  ws.onmessage = (ev) => {
    try {
      const data = JSON.parse(ev.data);

      // Handle progress updates
      if (data.type === "progress") {
        if (data.percent !== undefined) {
          setScrapeProgress(data.percent);
        }
        if (data.log) {
          appendScrapeLog(data.log);
        }
        // Update status display if available
        if (data.job && data.job.current_step) {
          appendScrapeLog(`⚙️ ${data.job.current_step}`);
        }
      }

      // Handle completion
      if (data.type === "done") {
        appendScrapeLog(`✅ Job completado exitosamente`);
        showToast(`Job ${jobId} completado`, "success");
        ws.close();
        delete state.websockets[jobId];
        setTimeout(() => {
          loadSeasons();
          loadListings();
          updateStats();
        }, 1500);
      }

      // Handle errors
      if (data.type === "error") {
        const errorMsg = data.job?.error || data.message || "Error desconocido";
        appendScrapeLog(`❌ Error: ${errorMsg}`);
        showToast(`Job ${jobId} falló`, "danger");
        ws.close();
        delete state.websockets[jobId];
      }

      // Legacy status handling (for backwards compatibility)
      if (data.status === "done" || data.status === "completed") {
        appendScrapeLog(`✓ Job finalizado`);
        showToast(`Job ${jobId} completado`, "success");
        ws.close();
        delete state.websockets[jobId];
        setTimeout(() => {
          loadSeasons();
          loadListings();
          updateStats();
        }, 1500);
      }
      if (data.status === "error" || data.status === "failed") {
        appendScrapeLog(`✗ Job falló: ${data.status}`);
        showToast(`Job ${jobId} falló`, "danger");
        ws.close();
        delete state.websockets[jobId];
      }
    } catch (e) {
      console.error("WS message error", e);
    }
  };

  ws.onopen = () => appendScrapeLog("✓ Conectado");
  ws.onclose = () => appendScrapeLog("Desconectado");
  ws.onerror = () => appendScrapeLog("⚠️ Error en conexión");
}

function appendScrapeLog(msg) {
  const logs = document.getElementById("scrape-logs");
  if (!logs) return;
  const el = document.createElement("div");
  el.textContent = msg;
  logs.appendChild(el);
  logs.scrollTop = logs.scrollHeight;
}

function setScrapeProgress(pct) {
  const prog = document.getElementById("scrape-progress");
  if (!prog) return;
  const clamped = Math.max(0, Math.min(100, pct));
  prog.style.width = `${clamped}%`;
}

// ========================================
// JOBS TAB
// ========================================

async function loadJobs() {
  const container = document.getElementById("jobs-list");
  if (!container) return;

  container.innerHTML = '<p class="text-muted">Cargando jobs...</p>';

  try {
    // Note: Assuming there's an endpoint to list jobs
    // If not implemented yet, show placeholder
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">📋</div>
        <h3>Historial de Jobs</h3>
        <p>Aquí aparecerá el historial de todos los scrapes ejecutados.</p>
        <p class="text-muted">Función en desarrollo - pronto disponible.</p>
      </div>
    `;
  } catch (error) {
    console.error("Error loading jobs:", error);
    container.innerHTML = '<p class="text-muted">Error al cargar jobs.</p>';
  }
}

// ========================================
// ANALYTICS TAB
// ========================================

// ========================================
// ANALYTICS TAB
// ========================================

const analyticsState = {
  selectedListings: new Set(),
  listingsData: [],
  colors: [
    "#3ecf8e", // Green
    "#667eea", // Purple
    "#f56565", // Red
    "#ed8936", // Orange
    "#48bb78", // Darker green
    "#4299e1", // Blue
    "#9f7aea", // Violet
    "#ed64a6", // Pink
    "#38b2ac", // Teal
    "#ecc94b", // Yellow
  ],
};

async function loadAnalyticsTab() {
  try {
    const response = await fetch("/api/listings");
    let listings = await response.json();

    if (state.currentWorkspace) {
      listings = listings.filter(
        (l) => l.workspace_id === state.currentWorkspace.id
      );
    }

    analyticsState.listingsData = listings;
    renderAnalyticsListings(listings);

    // Set default date range (last 30 days)
    const today = new Date();
    const monthAgo = new Date();
    monthAgo.setDate(monthAgo.getDate() - 30);

    const startInput = document.getElementById("analytics-start");
    const endInput = document.getElementById("analytics-end");

    if (startInput && !startInput.value) {
      startInput.value = monthAgo.toISOString().split("T")[0];
    }
    if (endInput && !endInput.value) {
      endInput.value = today.toISOString().split("T")[0];
    }
  } catch (error) {
    console.error("Error loading analytics listings:", error);
  }
}

function renderAnalyticsListings(listings) {
  const container = document.getElementById("analytics-listings-container");
  if (!container) return;

  container.innerHTML = listings
    .map((listing, index) => {
      const color = analyticsState.colors[index % analyticsState.colors.length];
      return `
      <label class="analytics-listing-item">
        <input
          type="checkbox"
          value="${listing.id}"
          onchange="toggleAnalyticsListing(${listing.id})"
        />
        <div class="analytics-listing-color" style="background-color: ${color};"></div>
        <span class="analytics-listing-name">${listing.name}</span>
      </label>
    `;
    })
    .join("");
}

function toggleAnalyticsListing(listingId) {
  if (analyticsState.selectedListings.has(listingId)) {
    analyticsState.selectedListings.delete(listingId);
  } else {
    analyticsState.selectedListings.add(listingId);
  }

  // Auto-reload if dates are set
  const startDate = document.getElementById("analytics-start")?.value;
  const endDate = document.getElementById("analytics-end")?.value;

  if (startDate && endDate && analyticsState.selectedListings.size > 0) {
    loadAnalytics();
  }
}

async function loadAnalytics() {
  const startDate = document.getElementById("analytics-start")?.value;
  const endDate = document.getElementById("analytics-end")?.value;
  const provider =
    document.getElementById("analytics-provider")?.value || "all";

  if (!startDate || !endDate) {
    showToast("Selecciona fechas", "warning");
    return;
  }

  if (analyticsState.selectedListings.size === 0) {
    showToast("Selecciona al menos un establecimiento", "warning");
    return;
  }

  try {
    // Fetch prices for all selected listings
    const promises = Array.from(analyticsState.selectedListings).map(
      (listingId) => {
        let url = `/api/prices/${listingId}?start_date=${startDate}&end_date=${endDate}`;
        if (provider !== "all") {
          url += `&provider=${provider}`;
        }
        return fetch(url)
          .then((res) => res.json())
          .then((prices) => ({ listingId, prices }));
      }
    );

    const results = await Promise.all(promises);
    renderAnalyticsChart(results);
    renderAnalyticsStats(results);
  } catch (error) {
    console.error("Error loading analytics:", error);
    showToast("Error al cargar análisis", "danger");
  }
}

function renderAnalyticsChart(results) {
  const canvas = document.getElementById("analyticsChart");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");

  // Destroy existing chart
  if (state.charts.analytics) {
    state.charts.analytics.destroy();
  }

  // Get all unique dates from all listings
  const allDates = new Set();
  results.forEach(({ prices }) => {
    prices.forEach((p) => allDates.add(p.date));
  });
  const sortedDates = Array.from(allDates).sort();

  // Create datasets for each listing
  const datasets = results.map(({ listingId, prices }, index) => {
    const listing = analyticsState.listingsData.find((l) => l.id === listingId);
    const color =
      analyticsState.colors[
        analyticsState.listingsData.indexOf(listing) %
          analyticsState.colors.length
      ];

    // Create a map of dates to prices
    const priceMap = new Map();
    prices.forEach((p) => {
      priceMap.set(p.date, p.price_per_night);
    });

    // Map all dates to prices (null if no price)
    const data = sortedDates.map((date) => {
      const price = priceMap.get(date);
      return price !== null && price !== undefined ? price : null;
    });

    return {
      label: listing ? listing.name : `Listing ${listingId}`,
      data: data,
      borderColor: color,
      backgroundColor: color + "20", // Add transparency
      tension: 0.1,
      fill: false,
      pointRadius: 3,
      pointHoverRadius: 5,
      spanGaps: false, // This makes the line discontinuous when data is null
      segment: {
        borderDash: (ctx) => {
          // Make dashed line when connecting across gaps
          const prev = ctx.p0.parsed.y;
          const curr = ctx.p1.parsed.y;
          return prev === null || curr === null ? [5, 5] : [];
        },
      },
    };
  });

  state.charts.analytics = new Chart(ctx, {
    type: "line",
    data: {
      labels: sortedDates,
      datasets: datasets,
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      interaction: {
        mode: "index",
        intersect: false,
      },
      plugins: {
        legend: {
          display: true,
          position: "top",
        },
        title: {
          display: true,
          text: "Evolución de Precios por Establecimiento",
          font: { size: 14, weight: 600 },
        },
        tooltip: {
          callbacks: {
            label: function (context) {
              let label = context.dataset.label || "";
              if (label) {
                label += ": ";
              }
              if (context.parsed.y !== null) {
                label += "$" + context.parsed.y.toFixed(2);
              } else {
                label += "Sin precio";
              }
              return label;
            },
          },
        },
      },
      scales: {
        x: {
          ticks: {
            maxRotation: 45,
            minRotation: 45,
            font: { size: 10 },
          },
        },
        y: {
          beginAtZero: false,
          ticks: {
            callback: (value) => "$" + value.toFixed(0),
          },
        },
      },
    },
  });
}

function renderAnalyticsStats(results) {
  const container = document.getElementById("analytics-stats");
  if (!container) return;

  // Calculate stats per establishment
  const statsByListing = [];
  let totalDays = 0;
  let totalAvailableDays = 0;
  let allPrices = [];

  results.forEach(({ listing_name, prices }) => {
    let listingDays = 0;
    let listingAvailableDays = 0;
    let listingPrices = [];

    prices.forEach((p) => {
      listingDays++;
      totalDays++;
      if (p.available) {
        listingAvailableDays++;
        totalAvailableDays++;
      }
      if (p.price_per_night) {
        listingPrices.push(p.price_per_night);
        allPrices.push(p.price_per_night);
      }
    });

    const avgPrice =
      listingPrices.length > 0
        ? listingPrices.reduce((a, b) => a + b, 0) / listingPrices.length
        : 0;
    const minPrice = listingPrices.length > 0 ? Math.min(...listingPrices) : 0;
    const maxPrice = listingPrices.length > 0 ? Math.max(...listingPrices) : 0;
    const availabilityRate =
      listingDays > 0
        ? ((listingAvailableDays / listingDays) * 100).toFixed(1)
        : 0;

    statsByListing.push({
      name: listing_name,
      avgPrice,
      minPrice,
      maxPrice,
      availabilityRate,
      availableDays: listingAvailableDays,
      totalDays: listingDays,
    });
  });

  // Calculate overall stats
  const overallAvgPrice =
    allPrices.length > 0
      ? allPrices.reduce((a, b) => a + b, 0) / allPrices.length
      : 0;
  const overallMinPrice = allPrices.length > 0 ? Math.min(...allPrices) : 0;
  const overallMaxPrice = allPrices.length > 0 ? Math.max(...allPrices) : 0;
  const overallAvailabilityRate =
    totalDays > 0 ? ((totalAvailableDays / totalDays) * 100).toFixed(1) : 0;

  // Build HTML - Table structure
  let html = `
    <div class="analytics-stats-table">
      <div class="analytics-stats-header">
        <div class="stat-col stat-col-name"></div>
        <div class="stat-col">Promedio</div>
        <div class="stat-col">Mínimo</div>
        <div class="stat-col">Máximo</div>
        <div class="stat-col">Disponibilidad</div>
      </div>
  `;

  // Individual establishment rows
  statsByListing.forEach((stats) => {
    html += `
      <div class="analytics-stats-row">
        <div class="stat-col stat-col-name">${stats.name}</div>
        <div class="stat-col stat-value">$${stats.avgPrice.toFixed(2)}</div>
        <div class="stat-col stat-value">$${stats.minPrice.toFixed(2)}</div>
        <div class="stat-col stat-value">$${stats.maxPrice.toFixed(2)}</div>
        <div class="stat-col stat-value">
          ${stats.availabilityRate}%
          <span class="stat-sublabel">${stats.availableDays}/${
      stats.totalDays
    } días</span>
        </div>
      </div>
    `;
  });

  // Overall row
  if (statsByListing.length > 1) {
    html += `
      <div class="analytics-stats-row analytics-stats-total">
        <div class="stat-col stat-col-name"><strong>TOTAL GENERAL</strong></div>
        <div class="stat-col stat-value"><strong>$${overallAvgPrice.toFixed(
          2
        )}</strong></div>
        <div class="stat-col stat-value"><strong>$${overallMinPrice.toFixed(
          2
        )}</strong></div>
        <div class="stat-col stat-value"><strong>$${overallMaxPrice.toFixed(
          2
        )}</strong></div>
        <div class="stat-col stat-value">
          <strong>${overallAvailabilityRate}%</strong>
          <span class="stat-sublabel">${totalAvailableDays}/${totalDays} días</span>
        </div>
      </div>
    `;
  }

  html += `</div>`;
  container.innerHTML = html;
}

async function exportAnalyticsData() {
  if (analyticsState.selectedListings.size === 0) {
    showToast("Selecciona al menos un establecimiento", "warning");
    return;
  }

  const startDate = document.getElementById("analytics-start")?.value;
  const endDate = document.getElementById("analytics-end")?.value;
  const provider =
    document.getElementById("analytics-provider")?.value || "all";

  if (!startDate || !endDate) {
    showToast("Selecciona fechas", "warning");
    return;
  }

  try {
    // Fetch all data
    const promises = Array.from(analyticsState.selectedListings).map(
      (listingId) => {
        let url = `/api/prices/${listingId}?start_date=${startDate}&end_date=${endDate}`;
        if (provider !== "all") {
          url += `&provider=${provider}`;
        }
        return fetch(url)
          .then((res) => res.json())
          .then((prices) => ({ listingId, prices }));
      }
    );

    const results = await Promise.all(promises);

    // Generate CSV
    let csv =
      "Fecha,Establecimiento,Precio por Noche,Disponible,Min Noches,Total Estadía\n";

    results.forEach(({ listingId, prices }) => {
      const listing = analyticsState.listingsData.find(
        (l) => l.id === listingId
      );
      const listingName = listing ? listing.name : `Listing ${listingId}`;

      prices.forEach((p) => {
        csv += `${p.date},${listingName},${p.price_per_night || ""},${
          p.available ? "Sí" : "No"
        },${p.min_nights || ""},${p.stay_total || ""}\n`;
      });
    });

    // Download
    const blob = new Blob([csv], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `analytics_${startDate}_${endDate}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);

    showToast("✅ CSV exportado", "success");
  } catch (error) {
    console.error("Error exporting:", error);
    showToast("Error al exportar", "danger");
  }
}

// ========================================
// STATS & UI STATE
// ========================================

function showStats() {
  const statsCards = document.getElementById("stats-cards");
  if (statsCards) statsCards.style.display = "grid";
}

function hideStats() {
  const statsCards = document.getElementById("stats-cards");
  if (statsCards) statsCards.style.display = "none";
}

async function updateStats() {
  if (!state.currentWorkspace) return;

  try {
    // Count listings
    const listingsResp = await fetch("/api/listings");
    const allListings = await listingsResp.json();
    const listings = allListings.filter(
      (l) => l.workspace_id === state.currentWorkspace.id
    );

    // Count seasons
    const seasonsResp = await fetch(
      `/api/workspaces/${state.currentWorkspace.id}/seasons`
    );
    const seasons = await seasonsResp.json();

    // Update stats
    const statListings = document.getElementById("stat-listings");
    if (statListings) statListings.textContent = listings.length;

    const statSeasons = document.getElementById("stat-seasons");
    if (statSeasons) statSeasons.textContent = seasons.length;

    // Jobs and prices would need dedicated endpoints
    const statJobs = document.getElementById("stat-jobs");
    if (statJobs) statJobs.textContent = "0"; // Placeholder

    const statPrices = document.getElementById("stat-prices");
    if (statPrices) statPrices.textContent = "-"; // Placeholder
  } catch (error) {
    console.error("Error updating stats:", error);
  }
}

function updateUIState() {
  // Called when season changes or other state updates
  // Reload relevant tabs
  const activeTab = document.querySelector(".tab.active");
  if (activeTab) {
    const tabName = activeTab.textContent.toLowerCase().includes("scraping")
      ? "scraping"
      : null;
    if (tabName === "scraping") {
      loadScrapingTab();
    }
  }
}

// ========================================
// TOASTS & NOTIFICATIONS
// ========================================

function showToast(message, type = "primary", timeout = 4000) {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const el = document.createElement("div");
  el.className = "toast";
  el.textContent = message;

  // Could add different styling based on type
  if (type === "danger") {
    el.style.borderLeftColor = "var(--danger)";
  } else if (type === "warning") {
    el.style.borderLeftColor = "var(--warning)";
  }

  container.appendChild(el);

  setTimeout(() => {
    el.style.opacity = "0";
    setTimeout(() => el.remove(), 300);
  }, timeout);
}

// ========================================
// UTILITIES
// ========================================

function escapeHtml(text) {
  if (!text) return "";
  const map = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  };
  return text.replace(/[&<>"']/g, (m) => map[m]);
}

function escapeForJs(text) {
  if (!text) return "";
  return text.replace(/'/g, "\\'").replace(/"/g, '\\"').replace(/\\/g, "\\\\");
}

// ========================================
// DATABASE TAB
// ========================================

const dbState = {
  currentTable: "prices",
  currentPage: 1,
  pageSize: 50,
  totalRecords: 0,
  filters: {},
  customFilters: [],
  sortColumn: null,
  sortDirection: "asc", // 'asc' or 'desc'
};

async function loadDatabaseTable() {
  const table = document.getElementById("db-table").value;
  dbState.currentTable = table;
  dbState.currentPage = 1;
  dbState.filters = {};

  // Show/hide relevant filters
  updateFilterVisibility(table);

  // Load listings for filter
  if (table === "prices" || table === "jobs") {
    await loadListingsForFilter();
  }

  // Load data
  await fetchDatabaseData();
}

function updateFilterVisibility(table) {
  const listingFilter = document.getElementById("db-listing-filter");
  const dateStartFilter = document.getElementById("db-date-start-filter");
  const dateEndFilter = document.getElementById("db-date-end-filter");

  if (table === "prices") {
    listingFilter.style.display = "block";
    dateStartFilter.style.display = "block";
    dateEndFilter.style.display = "block";
  } else if (table === "jobs") {
    listingFilter.style.display = "block";
    dateStartFilter.style.display = "block";
    dateEndFilter.style.display = "block";
  } else {
    listingFilter.style.display = "none";
    dateStartFilter.style.display = "none";
    dateEndFilter.style.display = "none";
  }
}

async function loadListingsForFilter() {
  try {
    const response = await fetch("/api/listings");
    const listings = await response.json();

    const select = document.getElementById("db-listing");
    select.innerHTML = '<option value="">Todos</option>';
    listings.forEach((listing) => {
      const option = document.createElement("option");
      option.value = listing.id;
      option.textContent = listing.name;
      select.appendChild(option);
    });
  } catch (error) {
    console.error("Error loading listings:", error);
  }
}

function applyDatabaseFilters() {
  const listingId = document.getElementById("db-listing").value;
  const dateStart = document.getElementById("db-date-start").value;
  const dateEnd = document.getElementById("db-date-end").value;

  // Apply header filters based on current workspace/season
  if (state.currentWorkspace) {
    dbState.filters.workspace_id = state.currentWorkspace.id;
  }
  if (state.currentSeason) {
    dbState.filters.season_id = state.currentSeason.id;
  }

  if (listingId) {
    dbState.filters.listing_id = listingId;
  } else {
    delete dbState.filters.listing_id;
  }

  if (dateStart) {
    dbState.filters.date_start = dateStart;
  } else {
    delete dbState.filters.date_start;
  }

  if (dateEnd) {
    dbState.filters.date_end = dateEnd;
  } else {
    delete dbState.filters.date_end;
  }

  dbState.currentPage = 1;
  fetchDatabaseData();
}

async function fetchDatabaseData() {
  const container = document.getElementById("database-table");
  container.innerHTML = '<div class="loading">Cargando datos...</div>';

  try {
    let url = "";
    const params = new URLSearchParams();
    params.append("page", dbState.currentPage);
    params.append("page_size", dbState.pageSize);

    // Add filters
    Object.keys(dbState.filters).forEach((key) => {
      if (dbState.filters[key]) {
        params.append(key, dbState.filters[key]);
      }
    });

    // Add sort parameters
    if (dbState.sortColumn) {
      params.append("sort_by", dbState.sortColumn);
      params.append("sort_order", dbState.sortDirection);
    }

    // Build URL based on table
    switch (dbState.currentTable) {
      case "prices":
        url = `/api/database/prices?${params}`;
        break;
      case "listings":
        url = `/api/database/listings?${params}`;
        break;
      case "jobs":
        url = `/api/database/jobs?${params}`;
        break;
      case "seasons":
        url = `/api/database/seasons?${params}`;
        break;
      case "workspaces":
        url = `/api/workspaces?${params}`;
        break;
    }

    const response = await fetch(url);
    if (!response.ok) throw new Error("Error al cargar datos");

    const data = await response.json();
    dbState.totalRecords = data.total || data.length;

    renderDatabaseTable(data.items || data);
    updatePaginationInfo();
  } catch (error) {
    console.error("Error:", error);
    container.innerHTML =
      '<div class="error">Error al cargar datos de la base de datos</div>';
    showToast("Error al cargar datos", "error");
  }
}

function renderDatabaseTable(data) {
  const container = document.getElementById("database-table");

  if (!data || data.length === 0) {
    container.innerHTML = '<div class="loading">No hay datos disponibles</div>';
    return;
  }

  const table = document.createElement("table");
  const thead = document.createElement("thead");
  const tbody = document.createElement("tbody");

  // Create headers (clickable for sorting)
  const headers = Object.keys(data[0]);
  const headerRow = document.createElement("tr");
  headers.forEach((header) => {
    const th = document.createElement("th");
    th.style.cursor = "pointer";
    th.style.userSelect = "none";

    // Add sort indicator if this column is sorted
    let sortIndicator = "";
    if (dbState.sortColumn === header) {
      sortIndicator = dbState.sortDirection === "asc" ? " ▲" : " ▼";
    }

    th.textContent = formatHeaderName(header) + sortIndicator;
    th.onclick = () => sortDatabaseTable(header);
    th.title = "Click para ordenar";
    headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);

  // Create rows
  data.forEach((row) => {
    const tr = document.createElement("tr");
    headers.forEach((header) => {
      const td = document.createElement("td");
      td.innerHTML = formatCellValue(header, row[header]);
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });

  table.appendChild(thead);
  table.appendChild(tbody);
  container.innerHTML = "";
  container.appendChild(table);
}

function sortDatabaseTable(column) {
  // Toggle sort direction if same column, otherwise reset to asc
  if (dbState.sortColumn === column) {
    dbState.sortDirection = dbState.sortDirection === "asc" ? "desc" : "asc";
  } else {
    dbState.sortColumn = column;
    dbState.sortDirection = "asc";
  }

  fetchDatabaseData();
}

function formatHeaderName(header) {
  const map = {
    id: "ID",
    listing_id: "Listing ID",
    listing_name: "Establecimiento",
    workspace_id: "Workspace",
    season_id: "Temporada",
    date: "Fecha",
    available: "Disponible",
    available_for_checkin: "Check-in",
    available_for_checkout: "Check-out",
    bookable: "Reservable",
    min_nights: "Min Noches",
    max_nights: "Max Noches",
    price_per_night: "Precio/Noche",
    stay_total: "Total",
    currency: "Moneda",
    inserted_at: "Insertado",
    name: "Nombre",
    url: "URL",
    provider: "Proveedor",
    status: "Estado",
    start_date: "Inicio",
    end_date: "Fin",
    guests: "Huéspedes",
    error: "Error",
    completed_at: "Completado",
    created_at: "Creado",
  };
  return map[header] || header.replace(/_/g, " ").toUpperCase();
}

function formatCellValue(header, value) {
  if (value === null || value === undefined) {
    return '<span class="db-cell-null">—</span>';
  }

  // Boolean values
  if (typeof value === "boolean") {
    return `<span class="db-cell-boolean ${value}">${value ? "✓" : "✗"}</span>`;
  }

  // Date fields
  if (header.includes("date") || header.includes("_at")) {
    return `<span class="db-cell-date">${value}</span>`;
  }

  // Price fields
  if (header.includes("price") || header === "stay_total") {
    return `<span class="db-cell-price">$${parseFloat(value).toFixed(
      2
    )}</span>`;
  }

  // Status field
  if (header === "status") {
    const statusClass =
      value === "completed"
        ? "success"
        : value === "failed"
        ? "danger"
        : value === "running"
        ? "warning"
        : "secondary";
    return `<span class="badge badge-${statusClass} db-cell-status">${value}</span>`;
  }

  // URL fields
  if (header === "url" && value) {
    return `<a href="${value}" target="_blank" class="text-primary">🔗 Link</a>`;
  }

  return escapeHtml(String(value));
}

function updatePaginationInfo() {
  const totalPages = Math.ceil(dbState.totalRecords / dbState.pageSize);

  document.getElementById("db-record-count").textContent = `${
    dbState.totalRecords
  } registro${dbState.totalRecords !== 1 ? "s" : ""}`;
  document.getElementById(
    "db-page-info"
  ).textContent = `Página ${dbState.currentPage} de ${totalPages}`;

  // Update buttons
  document.getElementById("db-prev-btn").disabled = dbState.currentPage === 1;
  document.getElementById("db-next-btn").disabled =
    dbState.currentPage >= totalPages;

  // Render page numbers
  renderPageNumbers(totalPages);
}

function renderPageNumbers(totalPages) {
  const container = document.getElementById("db-page-numbers");
  container.innerHTML = "";

  const maxVisible = 5;
  let start = Math.max(1, dbState.currentPage - Math.floor(maxVisible / 2));
  let end = Math.min(totalPages, start + maxVisible - 1);

  if (end - start < maxVisible - 1) {
    start = Math.max(1, end - maxVisible + 1);
  }

  for (let i = start; i <= end; i++) {
    const span = document.createElement("span");
    span.className =
      "page-number" + (i === dbState.currentPage ? " active" : "");
    span.textContent = i;
    span.onclick = () => goToPage(i);
    container.appendChild(span);
  }
}

function prevDatabasePage() {
  if (dbState.currentPage > 1) {
    dbState.currentPage--;
    fetchDatabaseData();
  }
}

function nextDatabasePage() {
  const totalPages = Math.ceil(dbState.totalRecords / dbState.pageSize);
  if (dbState.currentPage < totalPages) {
    dbState.currentPage++;
    fetchDatabaseData();
  }
}

function goToPage(page) {
  dbState.currentPage = page;
  fetchDatabaseData();
}

async function exportDatabaseTable() {
  const table = dbState.currentTable;
  const params = new URLSearchParams(dbState.filters);

  let url = "";
  switch (table) {
    case "prices":
      url = `/api/database/prices/export?${params}`;
      break;
    case "listings":
      url = `/api/database/listings/export?${params}`;
      break;
    case "jobs":
      url = `/api/database/jobs/export?${params}`;
      break;
    default:
      showToast("Exportación no disponible para esta tabla", "warning");
      return;
  }

  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error("Error al exportar");

    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = downloadUrl;
    a.download = `${table}_export_${
      new Date().toISOString().split("T")[0]
    }.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(downloadUrl);

    showToast("Datos exportados exitosamente", "success");
  } catch (error) {
    console.error("Error:", error);
    showToast("Error al exportar datos", "error");
  }
}

// Custom filters
function addCustomFilter() {
  const container = document.getElementById("custom-filters-list");
  const filterId = `filter-${Date.now()}`;

  const filterRow = document.createElement("div");
  filterRow.className = "custom-filter-row";
  filterRow.id = filterId;
  filterRow.innerHTML = `
    <select class="filter-field">
      <option value="listing_id">Establecimiento</option>
      <option value="date">Fecha</option>
      <option value="available">Disponible</option>
      <option value="price_per_night">Precio/Noche</option>
      <option value="status">Estado</option>
    </select>
    <select class="filter-operator">
      <option value="eq">=</option>
      <option value="ne">≠</option>
      <option value="gt">&gt;</option>
      <option value="lt">&lt;</option>
      <option value="gte">≥</option>
      <option value="lte">≤</option>
    </select>
    <input type="text" class="filter-value" placeholder="Valor">
    <button class="btn btn-sm btn-danger" onclick="removeCustomFilter('${filterId}')">✕</button>
  `;

  container.appendChild(filterRow);
}

function removeCustomFilter(filterId) {
  const element = document.getElementById(filterId);
  if (element) {
    element.remove();
  }
}

async function deleteFilteredRecords() {
  const table = dbState.currentTable;

  // Confirm deletion
  const filterDesc =
    Object.keys(dbState.filters).length > 0
      ? "con los filtros aplicados"
      : "TODOS los registros de esta tabla";

  if (
    !confirm(
      `⚠️ ¿Estás seguro de que deseas eliminar los registros ${filterDesc}?\n\nEsta acción NO se puede deshacer.`
    )
  ) {
    return;
  }

  try {
    // Build URL with filters
    const params = new URLSearchParams();
    Object.keys(dbState.filters).forEach((key) => {
      if (dbState.filters[key]) {
        params.append(key, dbState.filters[key]);
      }
    });

    let url;
    switch (table) {
      case "prices":
        url = `/api/database/prices?${params}`;
        break;
      case "listings":
        url = `/api/database/listings?${params}`;
        break;
      case "jobs":
        url = `/api/database/jobs?${params}`;
        break;
      case "seasons":
        url = `/api/database/seasons?${params}`;
        break;
      default:
        showToast("No se puede eliminar de esta tabla", "error");
        return;
    }

    const response = await fetch(url, {
      method: "DELETE",
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Error al eliminar registros");
    }

    const result = await response.json();
    showToast(result.message, "success");

    // Reload table data
    await fetchDatabaseData();
  } catch (error) {
    console.error("Error:", error);
    showToast(error.message || "Error al eliminar registros", "error");
  }
}

// Initialize database tab when loaded
document.addEventListener("DOMContentLoaded", () => {
  // Load initial database view when tab is activated
  const dbTab = document.querySelector('[onclick*="database"]');
  if (dbTab) {
    const originalOnclick = dbTab.onclick;
    dbTab.onclick = function (e) {
      originalOnclick.call(this, e);
      if (
        document.getElementById("database-tab").classList.contains("active")
      ) {
        loadDatabaseTable();
      }
    };
  }
});
