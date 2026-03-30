const API_URL = ""; // Assuming relative path since it's hosted on the same server

// Core state
let state = {
    empresas: [],
    vigiladores: [],
    asignaciones: [],
    tramites: [],
    biblioteca: [],
    asignacionRoles: [],
    tipoTramites: [],
    roles: [],
    tramiteFilter: "", // Texto de búsqueda
    tramiteDateFilter: "", // Filtro por fecha
    tramiteSort: "newest", // newest, oldest, alphabetical
    empresaSort: { field: 'nombre', order: 'asc' },
    currentUser: null,
    token: localStorage.getItem('lupo_token'),
    uploadContext: null,
    dashboardRiskFilter: 'todos'
};

function getAuthToken() {
    return state.token || localStorage.getItem('lupo_token') || '';
}

function getAuthHeaders(extraHeaders = {}) {
    const token = getAuthToken();
    return token ? { ...extraHeaders, Authorization: `Bearer ${token}` } : { ...extraHeaders };
}

async function initApp() {
    console.log("Iniciando Aplicación...");
    if (state.token) {
        await checkAuth();
    } else {
        showLogin();
    }
}

async function checkAuth() {
    try {
        const res = await fetch(`${API_URL}/users/me`, {
            headers: getAuthHeaders()
        });
        if (res.ok) {
            state.currentUser = await res.json();
            // Mostrar la app primero, luego cargar datos
            hideLogin();
            initNavigation();
            updateUserUI();
            await refreshState();
        } else {
            localStorage.removeItem('lupo_token');
            state.token = null;
            showLogin();
        }
    } catch (e) {
        console.error("Auth error", e);
        showLogin();
    }
}

function updateUserUI() {
    if (!state.currentUser) return;
    
    // Header Info
    document.getElementById('display-user-name').textContent = state.currentUser.username;
    
    let roleText = 'Usuario';
    const rolesMap = { 'Admin': 'Administrador', 'Cliente': 'Empresa', 'Consultor': 'Consultor' };
    roleText = rolesMap[state.currentUser.role] || 'Usuario';
    
    document.getElementById('display-user-role').textContent = roleText;
    document.getElementById('display-user-img').src = `https://ui-avatars.com/api/?name=${state.currentUser.username}&background=3b82f6&color=fff`;

    // Profile Modal Info
    document.getElementById('profile-username').value = state.currentUser.username;
    document.getElementById('profile-role').value = roleText;
    
    const empresaWrap = document.getElementById('profile-empresa-wrap');
    if (state.currentUser.empresa_id) {
        const emp = state.empresas.find(e => e.id === state.currentUser.empresa_id);
        document.getElementById('profile-empresa').value = emp ? emp.nombre : `ID: ${state.currentUser.empresa_id}`;
        empresaWrap.style.display = 'block';
    } else {
        empresaWrap.style.display = 'none';
    }

    // Menu Admin — mostrar menu de Usuarios solo si es Admin
    const navUsuarios = document.getElementById('nav-usuarios');
    if (navUsuarios) {
        navUsuarios.style.display = state.currentUser.role === 'Admin' ? 'flex' : 'none';
    }

    // Body role class for CSS restrictions (privilege-based)
    const priv = (state.currentUser.privilege || 'Ver').toLowerCase();
    document.body.className = `role-${state.currentUser.role.toLowerCase()} priv-${priv}`;
}

window.toggleUserDropdown = function(event) {
    if (event) event.stopPropagation();
    const dropdown = document.getElementById('user-dropdown');
    if (dropdown) dropdown.classList.toggle('active');
}

window.showSection = function(sectionId) {
    const navItem = document.querySelector(`.nav-links li[data-section="${sectionId}"]`);
    if (navItem) {
        navItem.click();
    } else {
        // Fallback for hidden sections
        document.querySelectorAll('.nav-links li').forEach(nav => nav.classList.remove('active'));
        document.querySelectorAll('.content-section').forEach(sec => sec.classList.remove('active'));
        const targetSec = document.getElementById(`sec-${sectionId}`);
        if (targetSec) targetSec.classList.add('active');
        document.getElementById('page-title').innerText = sectionId.charAt(0).toUpperCase() + sectionId.slice(1);
    }
}

document.addEventListener('click', () => {
    const dropdown = document.getElementById('user-dropdown');
    if (dropdown) dropdown.classList.remove('active');
});

function showLogin() {
    document.getElementById('login-overlay').style.display = 'flex';
    const appContainer = document.querySelector('.app-container');
    if (appContainer) appContainer.style.display = 'none';
}

function hideLogin() {
    document.getElementById('login-overlay').style.display = 'none';
    const appContainer = document.querySelector('.app-container');
    if (appContainer) appContainer.style.display = 'flex';
}

function logout() {
    localStorage.removeItem('lupo_token');
    state.token = null;
    state.currentUser = null;
    location.reload();
}

async function handleLogin(e) {
    if (e) e.preventDefault();
    const user = document.getElementById('login-username').value.trim();
    const pass = document.getElementById('login-password').value.trim();
    const errorDiv = document.getElementById('login-error');
    
    const formData = new FormData();
    formData.append('username', user);
    formData.append('password', pass);

    try {
        const res = await fetch(`${API_URL}/token`, { method: 'POST', body: formData });
        if (res.ok) {
            const data = await res.json();
            localStorage.setItem('lupo_token', data.access_token);
            state.token = data.access_token;
            // Limpiar campos
            document.getElementById('login-username').value = '';
            document.getElementById('login-password').value = '';
            
            // Forzar actualización de estado global de token
            state.token = data.access_token;
            
            await checkAuth();
        } else {
            errorDiv.innerText = "Usuario o contraseña inválidos";
            errorDiv.style.display = 'block';
            document.getElementById('login-password').value = '';
        }
    } catch (err) {
        errorDiv.innerText = "Error de conexión";
        errorDiv.style.display = 'block';
    }
}

// Start
document.addEventListener("DOMContentLoaded", () => {
    document.getElementById('form-login').addEventListener('submit', handleLogin);
    const dashboardRiskFilter = document.getElementById('dashboard-risk-filter');
    if (dashboardRiskFilter) {
        dashboardRiskFilter.addEventListener('change', (event) => {
            state.dashboardRiskFilter = event.target.value;
            renderDashboardCharts();
            renderAlertasDashboard();
        });
    }
    initApp();
});

function initNavigation() {
    const navItems = document.querySelectorAll('.nav-links li');
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
            
            document.querySelectorAll('.content-section').forEach(sec => sec.classList.remove('active'));
            const target = item.getAttribute('data-section');
            document.getElementById(`sec-${target}`).classList.add('active');
            
            document.getElementById('page-title').innerText = item.innerText.replace(/[^a-zA-ZáéíóúÁÉÍÓÚ\s]/g, '').trim();
        });
    });
}

// Data Fetching
async function fetchAllData() {
    const headers = getAuthHeaders();
    try {
        const [empRes, vigRes, asigRes, rolRes, tipoRes, tramRes, bibRes] = await Promise.all([
            fetch(`${API_URL}/empresas/`, { headers }),
            fetch(`${API_URL}/vigiladores/`, { headers }),
            fetch(`${API_URL}/asignaciones/`, { headers }),
            fetch(`${API_URL}/roles/`, { headers }),
            fetch(`${API_URL}/tipos-tramites/`, { headers }),
            fetch(`${API_URL}/tramites/`, { headers }),
            fetch(`${API_URL}/biblioteca/`, { headers })
        ]);
        
        state.empresas = await empRes.json();
        state.vigiladores = await vigRes.json();
        state.asignaciones = await asigRes.json();
        state.roles = await rolRes.json();
        state.tipoTramites = await tipoRes.json();
        state.tramites = await tramRes.json();
        state.biblioteca = await bibRes.json();
        
    } catch (e) {
        console.error("Error connecting to API", e);
    }
}

async function refreshState() {
    await fetchAllData();
    renderAll();
}

function renderAll() {
    updateDashboardStats();
    renderDashboardCharts();
    renderAlertasDashboard();
    renderEmpresas();
    renderVigiladores();
    renderAsignaciones();
    renderTramites();
    renderBiblioteca();
    renderUsuarios();
    populateSelects();
}

function updateDashboardStats() {
    document.getElementById('count-empresas').innerText = state.empresas.length;
    document.getElementById('count-vigiladores').innerText = state.vigiladores.length;
    document.getElementById('count-tramites').innerText = state.tramites.length;
}

function renderDashboardCharts() {
    const metricas = buildDashboardMetrics();

    const eficienciaEl = document.getElementById('metric-eficiencia');
    const alertasEl = document.getElementById('metric-alertas');
    const jurisdiccionesEl = document.getElementById('metric-jurisdicciones');
    const totalReqLabel = document.getElementById('req-total-label');
    const riskCaptionEl = document.getElementById('risk-panel-caption');
    const riskFilterEl = document.getElementById('dashboard-risk-filter');

    if (eficienciaEl) eficienciaEl.innerText = `${metricas.eficiencia}%`;
    if (alertasEl) alertasEl.innerText = metricas.totalAlertas;
    if (jurisdiccionesEl) jurisdiccionesEl.innerText = metricas.jurisdiccionesActivas;
    if (totalReqLabel) totalReqLabel.innerText = `${metricas.totalRequisitos} documentos`;
    if (riskCaptionEl) riskCaptionEl.innerText = metricas.riskSnapshot.caption;
    if (riskFilterEl) riskFilterEl.value = metricas.riskSnapshot.filter;

    renderRequisitosDonut(metricas.requisitosEstado, metricas.totalRequisitos);
    renderJurisdiccionesChart(metricas.tramitesPorJurisdiccion);
    renderTimelineChart(metricas.tramitesPorMes);
    renderVencimientosChart(metricas.riskSnapshot.vencimientos);
    renderRiskStory(metricas.riskSnapshot);
}

function buildDashboardMetrics() {
    const requisitosEstado = { Aprobado: 0, Subido: 0, Faltante: 0 };
    let totalRequisitos = 0;

    state.tramites.forEach(tramite => {
        (tramite.requisitos || []).forEach(req => {
            const estado = req.estado || 'Faltante';
            if (!Object.prototype.hasOwnProperty.call(requisitosEstado, estado)) {
                requisitosEstado[estado] = 0;
            }
            requisitosEstado[estado] += 1;
            totalRequisitos += 1;
        });
    });

    const aprobados = requisitosEstado.Aprobado || 0;
    const eficiencia = totalRequisitos ? Math.round((aprobados / totalRequisitos) * 100) : 0;

    const tramitesPorJurisdiccion = state.tramites.reduce((acc, tramite) => {
        const tipo = state.tipoTramites.find(t => t.id === tramite.tipo_tramite_id);
        const nombre = tipo ? tipo.nombre : `Tipo ${tramite.tipo_tramite_id}`;
        acc[nombre] = (acc[nombre] || 0) + 1;
        return acc;
    }, {});

    const tramitesPorMes = getLastMonths(6).map(item => ({ ...item, total: 0 }));
    state.tramites.forEach(tramite => {
        if (!tramite.fecha_creacion) return;
        const fecha = new Date(tramite.fecha_creacion);
        if (Number.isNaN(fecha.getTime())) return;
        const key = `${fecha.getFullYear()}-${String(fecha.getMonth() + 1).padStart(2, '0')}`;
        const found = tramitesPorMes.find(item => item.key === key);
        if (found) found.total += 1;
    });
    const riskSnapshot = buildDashboardRiskSnapshot();

    return {
        requisitosEstado,
        totalRequisitos,
        eficiencia,
        totalAlertas: riskSnapshot.totalAlertas,
        jurisdiccionesActivas: Object.keys(tramitesPorJurisdiccion).length,
        tramitesPorJurisdiccion,
        tramitesPorMes,
        riskSnapshot
    };
}

function renderRequisitosDonut(data, total) {
    const donut = document.getElementById('chart-requisitos-donut');
    const legend = document.getElementById('chart-requisitos-legend');
    if (!donut || !legend) return;

    const segments = [
        { label: 'Aprobado', value: data.Aprobado || 0, color: '#10b981' },
        { label: 'Subido', value: data.Subido || 0, color: '#f59e0b' },
        { label: 'Faltante', value: data.Faltante || 0, color: '#ef4444' }
    ];

    if (!total) {
        donut.innerHTML = `
            <div class="donut-fallback">
                <strong>0</strong>
                <span>Sin requisitos</span>
            </div>
        `;
        legend.innerHTML = '<p class="chart-empty">Todavia no hay documentacion cargada para graficar.</p>';
        return;
    }

    let current = 0;
    const gradientStops = segments.map(segment => {
        const start = Math.round((current / total) * 100);
        current += segment.value;
        const end = Math.round((current / total) * 100);
        return `${segment.color} ${start}% ${end}%`;
    }).join(', ');

    donut.innerHTML = `
        <div class="donut-ring" style="background: conic-gradient(${gradientStops});">
            <div class="donut-hole">
                <strong>${Math.round((segments[0].value / total) * 100)}%</strong>
                <span>Aprobado</span>
            </div>
        </div>
    `;

    legend.innerHTML = segments.map(segment => {
        const percent = Math.round((segment.value / total) * 100);
        return `
            <div class="legend-item">
                <span class="legend-dot" style="background:${segment.color}"></span>
                <div>
                    <strong>${segment.value}</strong>
                    <span>${segment.label} - ${percent}%</span>
                </div>
            </div>
        `;
    }).join('');
}

function renderJurisdiccionesChart(data) {
    const container = document.getElementById('chart-jurisdicciones');
    if (!container) return;

    const items = Object.entries(data).sort((a, b) => b[1] - a[1]).slice(0, 6);
    const max = items.length ? items[0][1] : 0;

    if (!items.length) {
        container.innerHTML = '<p class="chart-empty">No hay tramites iniciados para agrupar por jurisdiccion.</p>';
        return;
    }

    container.innerHTML = items.map(([label, value]) => `
        <div class="stack-row">
            <div class="stack-row-head">
                <span>${label}</span>
                <strong>${value}</strong>
            </div>
            <div class="stack-track">
                <div class="stack-bar" style="width:${Math.max((value / max) * 100, 8)}%"></div>
            </div>
        </div>
    `).join('');
}

function renderTimelineChart(items) {
    const container = document.getElementById('chart-timeline');
    if (!container) return;

    const max = Math.max(...items.map(item => item.total), 0);
    if (!max) {
        container.innerHTML = '<p class="chart-empty">Todavia no hay tramites con fecha de creacion suficiente para mostrar tendencia.</p>';
        return;
    }

    container.innerHTML = items.map(item => `
        <div class="timeline-bar-group">
            <span class="timeline-value">${item.total}</span>
            <div class="timeline-bar-wrap">
                <div class="timeline-bar" style="height:${Math.max((item.total / max) * 100, item.total ? 14 : 4)}%"></div>
            </div>
            <span class="timeline-label">${item.label}</span>
        </div>
    `).join('');
}

function renderVencimientosChart(data) {
    const container = document.getElementById('chart-vencimientos');
    if (!container) return;

    const items = [
        { label: 'Vigente', value: data.vigente, className: 'status-card-ok' },
        { label: 'Por vencer', value: data.porVencer, className: 'status-card-warn' },
        { label: 'Vencido', value: data.vencido, className: 'status-card-danger' },
        { label: 'Sin fecha', value: data.sinFecha, className: 'status-card-muted' }
    ];

    container.innerHTML = items.map(item => `
        <div class="status-card ${item.className}">
            <span>${item.label}</span>
            <strong>${item.value}</strong>
        </div>
    `).join('');
}

function renderRiskStory(snapshot) {
    const container = document.getElementById('dashboard-risk-story');
    if (!container) return;

    const comparison = snapshot.comparison;
    const maxComparison = Math.max(...comparison.map(item => item.value), 0);

    const comparisonHtml = comparison.map(item => `
        <div class="risk-story-bar-row ${item.isSelected ? 'is-selected' : ''}">
            <div class="risk-story-bar-head">
                <span>${item.label}</span>
                <strong>${item.value}</strong>
            </div>
            <div class="risk-story-bar-track">
                <div class="risk-story-bar-fill" style="width:${maxComparison ? Math.max((item.value / maxComparison) * 100, item.value ? 8 : 0) : 0}%"></div>
            </div>
        </div>
    `).join('');

    const storyHtml = snapshot.story.map(text => `<p>${text}</p>`).join('');

    container.innerHTML = `
        <div class="risk-story-copy">
            ${storyHtml}
        </div>
        <div class="risk-story-bars">
            ${comparisonHtml}
        </div>
    `;
}

function classifyExpiry(dateValue) {
    const fecha = parseDashboardDate(dateValue);
    if (!fecha) return 'sinFecha';

    const hoy = new Date();
    hoy.setHours(0, 0, 0, 0);
    const diff = fecha.getTime() - hoy.getTime();
    const DOS_MESES = 60 * 24 * 60 * 60 * 1000;

    if (diff < 0) return 'vencido';
    if (diff < DOS_MESES) return 'porVencer';
    return 'vigente';
}

function getLastMonths(count) {
    const formatter = new Intl.DateTimeFormat('es-AR', { month: 'short' });
    const result = [];
    const base = new Date();
    base.setDate(1);
    for (let i = count - 1; i >= 0; i -= 1) {
        const date = new Date(base.getFullYear(), base.getMonth() - i, 1);
        result.push({
            key: `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`,
            label: formatter.format(date).replace('.', '')
        });
    }
    return result;
}

function parseDashboardDate(dateValue) {
    if (!dateValue) return null;
    if (dateValue instanceof Date && !Number.isNaN(dateValue.getTime())) {
        const normalized = new Date(dateValue);
        normalized.setHours(0, 0, 0, 0);
        return normalized;
    }

    if (typeof dateValue === 'string') {
        const trimmed = dateValue.trim();
        if (/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) {
            const [year, month, day] = trimmed.split('-').map(Number);
            return new Date(year, month - 1, day);
        }
        if (/^\d{2}\/\d{2}\/\d{4}$/.test(trimmed)) {
            const [day, month, year] = trimmed.split('/').map(Number);
            return new Date(year, month - 1, day);
        }
    }

    const fallback = new Date(dateValue);
    if (Number.isNaN(fallback.getTime())) return null;
    fallback.setHours(0, 0, 0, 0);
    return fallback;
}

function getDaysUntilExpiry(dateValue) {
    const fecha = parseDashboardDate(dateValue);
    if (!fecha) return null;
    const hoy = new Date();
    hoy.setHours(0, 0, 0, 0);
    return Math.round((fecha.getTime() - hoy.getTime()) / (24 * 60 * 60 * 1000));
}

function formatDashboardDate(dateValue) {
    const fecha = parseDashboardDate(dateValue);
    return fecha ? fecha.toLocaleDateString('es-AR') : '-';
}

function getDashboardRiskFilterLabel(filter) {
    const labels = {
        todos: 'Empresas y personal',
        empresas: 'Empresas',
        personal: 'Personal'
    };
    return labels[filter] || labels.todos;
}

function getVigiladorEmpresaName(vigiladorId) {
    const asignacion = state.asignaciones.find(item => item.vigilador_id === vigiladorId && item.activo !== false)
        || state.asignaciones.find(item => item.vigilador_id === vigiladorId);
    if (!asignacion) return '';
    const empresa = state.empresas.find(item => item.id === asignacion.empresa_id);
    return empresa ? empresa.nombre : '';
}

function getDashboardRiskEntities(filter = state.dashboardRiskFilter || 'todos') {
    const empresas = state.empresas.map(item => ({
        entityType: 'empresa',
        entityLabel: 'Empresa',
        name: item.nombre,
        secondary: item.cuit || '',
        fecha_vencimiento_hab: item.fecha_vencimiento_hab,
        status: classifyExpiry(item.fecha_vencimiento_hab)
    }));

    const personal = state.vigiladores.map(item => ({
        entityType: 'personal',
        entityLabel: 'Personal',
        name: item.nombre_completo,
        secondary: getVigiladorEmpresaName(item.id),
        fecha_vencimiento_hab: item.fecha_vencimiento_hab,
        status: classifyExpiry(item.fecha_vencimiento_hab)
    }));

    if (filter === 'empresas') return empresas;
    if (filter === 'personal') return personal;
    return [...empresas, ...personal];
}

function buildDashboardRiskSnapshot(filter = state.dashboardRiskFilter || 'todos') {
    const entities = getDashboardRiskEntities(filter);
    const vencimientos = { vigente: 0, porVencer: 0, vencido: 0, sinFecha: 0 };
    const comparisonBase = {
        empresas: getDashboardRiskEntities('empresas').filter(item => ['porVencer', 'vencido'].includes(item.status)).length,
        personal: getDashboardRiskEntities('personal').filter(item => ['porVencer', 'vencido'].includes(item.status)).length
    };

    entities.forEach(item => {
        vencimientos[item.status] += 1;
    });

    const alerts = entities
        .filter(item => item.status === 'porVencer' || item.status === 'vencido')
        .map(item => ({
            ...item,
            daysToExpiry: getDaysUntilExpiry(item.fecha_vencimiento_hab)
        }))
        .sort((a, b) => (a.daysToExpiry ?? 999999) - (b.daysToExpiry ?? 999999));

    const requisitosPendientes = state.tramites.reduce((total, tramite) => {
        return total + (tramite.requisitos || []).filter(req => (req.estado || 'Faltante') !== 'Aprobado').length;
    }, 0);

    const story = [];
    if (!alerts.length) {
        story.push(`No hay alertas activas en ${getDashboardRiskFilterLabel(filter).toLowerCase()}.`);
    } else {
        const critical = alerts[0];
        if ((critical.daysToExpiry ?? 0) < 0) {
            story.push(`${critical.entityLabel} ${critical.name} ya esta vencido y requiere regularizacion inmediata.`);
        } else {
            story.push(`La siguiente alerta vence el ${formatDashboardDate(critical.fecha_vencimiento_hab)} para ${critical.entityLabel.toLowerCase()} ${critical.name}.`);
        }
    }

    if (filter === 'todos') {
        const totalComparado = comparisonBase.empresas + comparisonBase.personal;
        if (totalComparado) {
            const focus = comparisonBase.empresas >= comparisonBase.personal ? 'Empresas' : 'Personal';
            const focusValue = focus === 'Empresas' ? comparisonBase.empresas : comparisonBase.personal;
            const ratio = Math.round((focusValue / totalComparado) * 100);
            story.push(`${focus} concentra ${ratio}% de las alertas activas del tablero.`);
        } else {
            story.push('El universo total no presenta vencimientos proximos ni vencidos.');
        }
    } else if (entities.length) {
        const ratio = Math.round((alerts.length / entities.length) * 100);
        story.push(`${ratio}% del universo filtrado presenta alertas activas.`);
    }

    story.push(`${requisitosPendientes} requisitos siguen pendientes o subidos sin aprobar.`);

    return {
        filter,
        caption: getDashboardRiskFilterLabel(filter),
        vencimientos,
        alerts,
        totalAlertas: alerts.length,
        story,
        comparison: [
            { label: 'Empresas', value: comparisonBase.empresas, isSelected: filter === 'empresas' },
            { label: 'Personal', value: comparisonBase.personal, isSelected: filter === 'personal' }
        ]
    };
}

function renderAlertasDashboard() {
    const grid = document.getElementById('grid-alertas');
    const summary = document.getElementById('alertas-summary');
    if (!grid) return;

    const snapshot = buildDashboardRiskSnapshot();
    if (summary) {
        summary.innerText = `${snapshot.caption}. ${snapshot.totalAlertas} alertas activas en la vista actual.`;
    }

    if (!snapshot.alerts.length) {
        grid.innerHTML = '<p style="color:var(--text-secondary)">No hay vencimientos proximos en el filtro seleccionado.</p>';
        return;
    }

    grid.innerHTML = snapshot.alerts.map(item => {
        const isExpired = item.status === 'vencido';
        const badgeClass = isExpired ? 'badge-danger' : 'badge-warning';
        const badgeLabel = isExpired ? 'VENCIDO' : 'POR VENCER';
        const secondaryLine = item.secondary ? `<p><i class="fa-solid fa-briefcase"></i> ${item.secondary}</p>` : '';
        const daysLine = (item.daysToExpiry ?? 0) < 0
            ? `<p><i class="fa-solid fa-triangle-exclamation"></i> ${Math.abs(item.daysToExpiry)} dias vencido</p>`
            : `<p><i class="fa-solid fa-hourglass-half"></i> ${item.daysToExpiry} dias para vencer</p>`;

        return `
            <div class="tramite-card glass-panel" style="border-top-color: var(--${isExpired ? 'danger' : 'warning'})">
                <div style="display:flex; justify-content:space-between; gap:1rem;">
                    <h4>${item.entityLabel}: ${item.name}</h4>
                    <span class="badge ${badgeClass}">${badgeLabel}</span>
                </div>
                ${secondaryLine}
                <p><i class="fa-solid fa-calendar-xmark"></i> Vto: ${formatDashboardDate(item.fecha_vencimiento_hab)}</p>
                ${daysLine}
            </div>
        `;
    }).join('');
}

// Modals
window.openModal = function(id) { document.getElementById(id).classList.add('active'); }
window.closeModal = function(id) { document.getElementById(id).classList.remove('active'); }

// Forms Submit
document.getElementById('form-empresa').addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
        nombre: document.getElementById('emp-nombre').value,
        cuit: document.getElementById('emp-cuit').value,
        direccion: document.getElementById('emp-direccion').value || null,
        telefono: document.getElementById('emp-telefono').value || null,
        email: document.getElementById('emp-email').value || null,
        fecha_alta: document.getElementById('emp-alta').value || null,
        fecha_vencimiento_hab: document.getElementById('emp-vence').value || null,
        jurisdicciones: Array.from(document.querySelectorAll('input[name="emp-juris"]:checked')).map(i => i.value).join(',')
    };
    await postData('/empresas/', data);
    closeModal('modal-empresa');
    e.target.reset();
    await refreshState();
});

document.getElementById('form-vigilador').addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
        nombre_completo: document.getElementById('vig-nombre').value,
        dni: document.getElementById('vig-dni').value,
        legajo: document.getElementById('vig-legajo').value || null,
        domicilio: document.getElementById('vig-domicilio').value || null,
        telefono: document.getElementById('vig-telefono').value || null,
        fecha_alta: document.getElementById('vig-alta').value || null,
        fecha_vencimiento_hab: document.getElementById('vig-vence').value || null
    };
    await postData('/vigiladores/', data);
    closeModal('modal-vigilador');
    e.target.reset();
    await refreshState();
});

document.getElementById('form-asignacion').addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
        vigilador_id: parseInt(document.getElementById('asig-vigilador').value),
        empresa_id: parseInt(document.getElementById('asig-empresa').value),
        activa: true
    };
    await postData('/asignaciones/', data);
    closeModal('modal-asignacion');
    e.target.reset();
    await refreshState();
});

document.getElementById('form-rol').addEventListener('submit', async (e) => {
    e.preventDefault();
    const asigId = document.getElementById('rol-asignacion-id').value;
    const data = {
        asignacion_id: parseInt(asigId),
        rol_id: parseInt(document.getElementById('rol-select').value),
        activo: true
    };
    await postData(`/asignaciones/${asigId}/roles/`, data);
    closeModal('modal-rol');
    await refreshState();
});

document.getElementById('form-tramite').addEventListener('submit', async (e) => {
    e.preventDefault();
    const selection = document.getElementById('tram-asignacion-rol').value;
    const data = {
        tipo_tramite_id: parseInt(document.getElementById('tram-tipo').value),
        estado: "Pendiente"
    };

    if (selection.startsWith('emp_')) {
        data.empresa_id = parseInt(selection.replace('emp_', ''));
    } else {
        data.asignacion_rol_id = parseInt(selection);
    }

    await postData('/tramites/', data);
    closeModal('modal-tramite');
    await refreshState();
});

// Helpers
async function postData(endpoint, data) {
    try {
        const res = await fetch(`${API_URL}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!res.ok) {
            const err = await res.json();
            alert(`Error: ${err.detail}`);
            throw new Error(err.detail);
        }
        return await res.json();
    } catch(e) { console.error(e); throw e; }
}

async function refreshState() {
    await fetchAllData();
    renderAll();
}

function getEntityStatusInfo(entity) {
    const vto = entity.fecha_vencimiento_hab || '-';
    const hoy = new Date();
    const DOS_MESES = 60 * 24 * 60 * 60 * 1000;
    const vtoDate = entity.fecha_vencimiento_hab ? new Date(entity.fecha_vencimiento_hab) : null;
    const isExpired = vtoDate && vtoDate < hoy;
    const isNear = vtoDate && !isExpired && (vtoDate - hoy) < DOS_MESES;
    const statusClass = isExpired ? 'status-vencido' : (isNear ? 'status-por-vencer' : (vtoDate ? 'status-ok' : ''));

    let estadoLabel = 'Sin fecha';
    let estadoBadge = 'badge-warning';

    if (!entity.activo) {
        estadoLabel = 'Archivado';
        estadoBadge = 'badge-danger';
    } else if (isExpired) {
        estadoLabel = 'Vencido';
        estadoBadge = 'badge-danger';
    } else if (isNear) {
        estadoLabel = 'Por vencer';
        estadoBadge = 'badge-warning';
    } else if (vtoDate) {
        estadoLabel = 'Vigente';
        estadoBadge = 'badge-success';
    }

    return {
        vto,
        statusClass,
        estadoLabel,
        estadoBadge
    };
}

// Render Functions
function renderEmpresas() {
    const tbody = document.getElementById('tbody-empresas');
    if (!tbody) return;
    tbody.innerHTML = '';
    
    let list = [...state.empresas];
    const { field, order } = state.empresaSort;
    
    list.sort((a, b) => {
        let valA = (field === 'vencimiento') ? (a.fecha_vencimiento_hab || '9999-12-31') : (a[field] || '').toString().toLowerCase();
        let valB = (field === 'vencimiento') ? (b.fecha_vencimiento_hab || '9999-12-31') : (b[field] || '').toString().toLowerCase();
        return order === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
    });

    list.forEach(e => {
        const { vto, statusClass, estadoLabel, estadoBadge } = getEntityStatusInfo(e);

        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>${e.nombre}</strong></td>
            <td>${e.cuit}</td>
            <td><small>${e.jurisdicciones || '-'}</small></td>
            <td class="${statusClass}">${vto}</td>
            <td><span class="badge ${estadoBadge}">${estadoLabel}</span></td>
            <td>
                <button class="btn-icon write-action" title="Adjuntar documentacion" onclick="openUploadModal('empresa', ${e.id}, '${e.nombre.replace(/'/g,"\\'")}')"><i class="fa-solid fa-file-arrow-up"></i></button>
                <button class="btn-icon write-action" onclick="openEditEmpresa(${e.id})"><i class="fa-solid fa-pen"></i></button>
                <button class="btn-icon text-danger write-action" onclick="deleteEmpresa(${e.id}, '${e.nombre}')"><i class="fa-solid fa-trash"></i></button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

window.sortEmpresas = function(field) {
    if (state.empresaSort.field === field) {
        state.empresaSort.order = state.empresaSort.order === 'asc' ? 'desc' : 'asc';
    } else {
        state.empresaSort.field = field;
        state.empresaSort.order = 'asc';
    }
    renderEmpresas();
}

function renderVigiladores() {
    const tbody = document.getElementById('tbody-vigiladores');
    if (!tbody) return;
    tbody.innerHTML = (state.vigiladores || []).map(v => {
        const { vto, statusClass, estadoLabel, estadoBadge } = getEntityStatusInfo(v);

        return `
        <tr>
            <td>#${v.id}</td>
            <td><strong>${v.nombre_completo}</strong></td>
            <td>${v.dni}</td>
            <td>${v.legajo || '-'}</td>
            <td class="${statusClass}">${vto}</td>
            <td><span class="badge ${estadoBadge}">${estadoLabel}</span></td>
            <td>
                <button class="btn-icon write-action" title="Adjuntar documentacion" onclick="openUploadModal('vigilador', ${v.id}, '${v.nombre_completo.replace(/'/g,"\\'")}')"><i class="fa-solid fa-file-arrow-up"></i></button>
                <button class="btn-icon write-action" onclick="openEditVigilador(${v.id})"><i class="fa-solid fa-pen"></i></button>
                <button class="btn-icon text-danger write-action" onclick="deleteVigilador(${v.id}, '${v.nombre_completo}')"><i class="fa-solid fa-trash"></i></button>
            </td>
        </tr>
    `}).join('');
}

function renderAsignaciones() {
    const tbody = document.getElementById('tbody-asignaciones');
    if (!tbody) return;
    tbody.innerHTML = (state.asignaciones || []).map(a => {
        const vig = (state.vigiladores || []).find(v => v.id === a.vigilador_id);
        const emp = (state.empresas || []).find(e => e.id === a.empresa_id);
        
        const rolesHtml = (a.roles || []).map(r => {
            const rolData = state.roles.find(ro => ro.id === r.rol_id);
            return `
                <span class="badge" style="background:var(--accent-color); display:inline-flex; align-items:center; gap:8px; padding: 4px 10px;">
                    ${rolData ? rolData.nombre : 'Rol'} 
                    <i class="fa-solid fa-circle-xmark write-action" style="cursor:pointer; opacity:0.7;" onclick="removeRole(${r.id})"></i>
                </span>`;
        }).join(' ');

        return `
        <tr>
            <td>#${a.id}</td>
            <td><strong>${vig ? vig.nombre_completo : '-'}</strong></td>
            <td>${emp ? emp.nombre : '-'}</td>
            <td><div style="display:flex; flex-wrap:wrap; gap:5px;">${rolesHtml || '<small style="opacity:0.5">Sin roles</small>'}</div></td>
            <td>
                <button class="btn-primary btn-sm write-action" onclick="openRolModal(${a.id})"><i class="fa-solid fa-plus"></i> Añadir Rol</button>
            </td>
        </tr>
    `}).join('');
}

window.removeRole = async function(asigRolId) {
    if (!confirm('¿Quitar este rol? Se perderá el historial de trámites asociados.')) return;
    await fetch(`${API_URL}/asignaciones/roles/${asigRolId}`, { method: 'DELETE' });
    await refreshState();
}

window.deleteTramite = async function(id) {
    if (!confirm('¿Eliminar este trámite y todos sus requisitos?')) return;
    await fetch(`${API_URL}/tramites/${id}`, { method: 'DELETE' });
    await refreshState();
}

window.openRolModal = function(asigId) {
    document.getElementById('rol-asignacion-id').value = asigId;
    openModal('modal-rol');
}

// Search / Filter (includes archived records via /todos/)
window.filterTable = async function(tbodyId, query) {
    const q = query.toLowerCase().trim();
    // First filter visible active rows
    const rows = document.querySelectorAll(`#${tbodyId} tr:not(.archived-row)`);
    rows.forEach(row => {
        row.style.display = row.innerText.toLowerCase().includes(q) ? '' : 'none';
    });
    // Remove old archived overlay
    document.querySelectorAll(`#${tbodyId} .archived-row`).forEach(r => r.remove());
    if (q.length < 2) return; // Don't search archive for very short queries
    // Fetch all (including archived) to find matches in archived records
    const entity = tbodyId.includes('empresa') ? 'empresas' : 'vigiladores';
    try {
        const res = await fetch(`${API_URL}/${entity}/todos/`);
        const all = await res.json();
        const archived = all.filter(x => !x.activo);
        const matched = archived.filter(x => {
            const txt = (x.nombre || x.nombre_completo || '') + ' ' + (x.cuit || x.dni || '');
            return txt.toLowerCase().includes(q);
        });
        if (matched.length === 0) return;
        // Build rows for archived results
        matched.forEach(x => {
            const row = document.createElement('tr');
            row.className = 'archived-row';
            row.style.opacity = '0.6';
            row.style.fontStyle = 'italic';
            const nombre = x.nombre || x.nombre_completo;
            const ref = x.cuit || x.dni;
            const toggleFn = entity === 'empresas' ? `restoreEmpresa` : `restoreVigilador`;
            row.innerHTML = `
                <td>#${x.id} <span class="badge pendiente">Archivado</span></td>
                <td>${nombre}</td>
                <td>${ref}</td>
                <td colspan="3"><button class="btn-primary btn-sm" style="background:var(--success)" onclick="${toggleFn}(${x.id})"><i class="fa-solid fa-box-open"></i> Restaurar</button></td>
            `;
            document.getElementById(tbodyId).appendChild(row);
        });
    } catch(e) { console.error(e); }
}

// Restore archived records
window.restoreEmpresa = async function(id) {
    await fetch(`${API_URL}/empresas/${id}/toggle-activo`, { method: 'PATCH' });
    await refreshState();
    // Clear search to show restored record in active list
    document.getElementById('search-empresas').value = '';
    document.querySelectorAll('#tbody-empresas .archived-row').forEach(r => r.remove());
    document.querySelectorAll('#tbody-empresas tr').forEach(r => r.style.display = '');
}

window.restoreVigilador = async function(id) {
    await fetch(`${API_URL}/vigiladores/${id}/toggle-activo`, { method: 'PATCH' });
    await refreshState();
    document.getElementById('search-vigiladores').value = '';
    document.querySelectorAll('#tbody-vigiladores .archived-row').forEach(r => r.remove());
    document.querySelectorAll('#tbody-vigiladores tr').forEach(r => r.style.display = '');
}

// Soft-delete functions
window.deleteEmpresa = async function(id, nombre) {
    if (!confirm(`¿Archivar empresa "${nombre}"? No se borrará, quedará en el sistema.`)) return;
    await fetch(`${API_URL}/empresas/${id}`, { method: 'DELETE' });
    await refreshState();
}

window.deleteVigilador = async function(id, nombre) {
    if (!confirm(`¿Archivar vigilador "${nombre}"? No se borrará, quedará en el sistema.`)) return;
    await fetch(`${API_URL}/vigiladores/${id}`, { method: 'DELETE' });
    await refreshState();
}

window.openEditEmpresa = function(id) {
    const e = state.empresas.find(x => x.id === id);
    if (!e) return;
    document.getElementById('edit-emp-id').value = e.id;
    document.getElementById('edit-emp-nombre').value = e.nombre || '';
    document.getElementById('edit-emp-cuit').value = e.cuit || '';
    document.getElementById('edit-emp-direccion').value = e.direccion || '';
    document.getElementById('edit-emp-telefono').value = e.telefono || '';
    document.getElementById('edit-emp-email').value = e.email || '';
    document.getElementById('edit-emp-alta').value = e.fecha_alta || '';
    document.getElementById('edit-emp-vence').value = e.fecha_vencimiento_hab || '';
    
    // Check jurisdictions
    const juris = (e.jurisdicciones || '').split(',');
    document.querySelectorAll('input[name="edit-emp-juris"]').forEach(cb => {
        cb.checked = juris.includes(cb.value);
    });

    openModal('modal-edit-empresa');
}

window.openEditVigilador = function(id) {
    const v = state.vigiladores.find(x => x.id === id);
    if (!v) return;
    document.getElementById('edit-vig-id').value = v.id;
    document.getElementById('edit-vig-nombre').value = v.nombre_completo || '';
    document.getElementById('edit-vig-dni').value = v.dni || '';
    document.getElementById('edit-vig-legajo').value = v.legajo || '';
    document.getElementById('edit-vig-domicilio').value = v.domicilio || '';
    document.getElementById('edit-vig-telefono').value = v.telefono || '';
    document.getElementById('edit-vig-alta').value = v.fecha_alta || '';
    document.getElementById('edit-vig-vence').value = v.fecha_vencimiento_hab || '';
    openModal('modal-edit-vigilador');
}

document.getElementById('form-edit-empresa').addEventListener('submit', async (e) => {
    e.preventDefault();
    const id = document.getElementById('edit-emp-id').value;
    const data = {
        nombre: document.getElementById('edit-emp-nombre').value,
        cuit: document.getElementById('edit-emp-cuit').value,
        direccion: document.getElementById('edit-emp-direccion').value || null,
        telefono: document.getElementById('edit-emp-telefono').value || null,
        email: document.getElementById('edit-emp-email').value || null,
        fecha_alta: document.getElementById('edit-emp-alta').value || null,
        fecha_vencimiento_hab: document.getElementById('edit-emp-vence').value || null,
        jurisdicciones: Array.from(document.querySelectorAll('input[name="edit-emp-juris"]:checked')).map(i => i.value).join(',')
    };
    await fetch(`${API_URL}/empresas/${id}`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    closeModal('modal-edit-empresa');
    await refreshState();
});

document.getElementById('form-edit-vigilador').addEventListener('submit', async (e) => {
    e.preventDefault();
    const id = document.getElementById('edit-vig-id').value;
    const data = {
        nombre_completo: document.getElementById('edit-vig-nombre').value,
        dni: document.getElementById('edit-vig-dni').value,
        legajo: document.getElementById('edit-vig-legajo').value || null,
        domicilio: document.getElementById('edit-vig-domicilio').value || null,
        telefono: document.getElementById('edit-vig-telefono').value || null,
        fecha_alta: document.getElementById('edit-vig-alta').value || null,
        fecha_vencimiento_hab: document.getElementById('edit-vig-vence').value || null
    };
    await fetch(`${API_URL}/vigiladores/${id}`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    closeModal('modal-edit-vigilador');
    await refreshState();
});

function renderTramites() {
    const grid = document.getElementById('grid-tramites');
    if (!grid) return;
    grid.innerHTML = '';
    const getTramiteOwner = (tramite) => {
        if (tramite.asignacion_rol_id) {
            const asignacion = state.asignaciones.find(a => (a.roles || []).some(ar => ar.id === tramite.asignacion_rol_id));
            const vigilador = asignacion ? state.vigiladores.find(v => v.id === asignacion.vigilador_id) : null;
            const empresa = asignacion ? state.empresas.find(e => e.id === asignacion.empresa_id) : null;
            const asigRol = asignacion ? (asignacion.roles || []).find(ar => ar.id === tramite.asignacion_rol_id) : null;
            const rolNombre = asigRol ? state.roles.find(r => r.id === asigRol.rol_id)?.nombre : null;
            return {
                title: vigilador ? vigilador.nombre_completo : "Personal",
                subtitle: [empresa?.nombre, rolNombre].filter(Boolean).join(" / ")
            };
        }
        if (tramite.empresa_id) {
            const emp = state.empresas.find(e => e.id === tramite.empresa_id);
            return {
                title: emp ? emp.nombre : "Empresa",
                subtitle: "Habilitacion Jurisdiccional"
            };
        }
        return { title: "Tramite", subtitle: "" };
    };

    let filtered = state.tramites.filter(t => {
        const q = (state.tramiteFilter || '').toLowerCase();
        let matchSearch = true;
        if (q) {
            const tipo = state.tipoTramites.find(ti => ti.id === t.tipo_tramite_id)?.nombre || '';
            let entName = "";
            if (t.asignacion_rol_id) {
                // ... búsqueda simplificada para performance
                entName = "Personal"; 
            } else if (t.empresa_id) {
                const emp = state.empresas.find(e => e.id === t.empresa_id);
                entName = emp ? emp.nombre : "Empresa";
            }
            matchSearch = tipo.toLowerCase().includes(q) || entName.toLowerCase().includes(q);
        }

        let matchDate = true;
        if (state.tramiteDateFilter) {
            matchDate = t.fecha_creacion && t.fecha_creacion.startsWith(state.tramiteDateFilter);
        }

        return matchSearch && matchDate;
    });

    // Ordenamiento
    filtered.sort((a, b) => {
        if (state.tramiteSort === 'newest') return new Date(b.fecha_creacion) - new Date(a.fecha_creacion);
        if (state.tramiteSort === 'oldest') return new Date(a.fecha_creacion) - new Date(b.fecha_creacion);
        return 0;
    });

    filtered.forEach(t => {
        const tipo = (state.tipoTramites || []).find(ti => ti.id === t.tipo_tramite_id);
        let entidad = "";
        let subtext = "";
        
        if (t.asignacion_rol_id) {
            entidad = "Trámite de Personal";
            subtext = `ID Rol: ${t.asignacion_rol_id}`;
        } else if (t.empresa_id) {
            const emp = state.empresas.find(e => e.id === t.empresa_id);
            entidad = emp ? emp.nombre : "Empresa";
            subtext = "Habilitación Jurisdiccional";
        }

        const card = document.createElement('div');
        card.className = 'tramite-card glass-panel';
        card.innerHTML = `
            <div class="tramite-header">
                <h3>${tipo ? tipo.nombre : 'Trámite'}</h3>
                <span class="badge ${t.estado === 'Completo' ? 'badge-success' : 'badge-warning'}">${t.estado}</span>
            </div>
            <p><strong>${entidad}</strong></p>
            <p style="font-size:0.85rem; color:var(--text-secondary);">${subtext}</p>
            <div style="margin-top:1rem; display:flex; justify-content:space-between; align-items:center;">
                <small><i class="fa-solid fa-calendar-day"></i> ${t.fecha_creacion || '-'}</small>
                <div>
                    <button class="btn-primary btn-sm" onclick="viewChecklist(${t.id})"><i class="fa-solid fa-list-check"></i> Checklist</button>
                    <button class="btn-icon text-danger write-action" onclick="deleteTramite(${t.id})"><i class="fa-solid fa-trash-can"></i></button>
                </div>
            </div>
        `;
        grid.appendChild(card);
    });
}

renderTramites = function() {
    const grid = document.getElementById('grid-tramites');
    if (!grid) return;
    grid.innerHTML = '';

    const getTramiteOwner = (tramite) => {
        if (tramite.asignacion_rol_id) {
            const asignacion = state.asignaciones.find(a => (a.roles || []).some(ar => ar.id === tramite.asignacion_rol_id));
            const vigilador = asignacion ? state.vigiladores.find(v => v.id === asignacion.vigilador_id) : null;
            const empresa = asignacion ? state.empresas.find(e => e.id === asignacion.empresa_id) : null;
            const asigRol = asignacion ? (asignacion.roles || []).find(ar => ar.id === tramite.asignacion_rol_id) : null;
            const rolNombre = asigRol ? state.roles.find(r => r.id === asigRol.rol_id)?.nombre : null;
            return {
                title: vigilador ? vigilador.nombre_completo : "Personal",
                subtitle: [empresa?.nombre, rolNombre].filter(Boolean).join(" / ")
            };
        }

        if (tramite.empresa_id) {
            const empresa = state.empresas.find(e => e.id === tramite.empresa_id);
            return {
                title: empresa ? empresa.nombre : "Empresa",
                subtitle: "Habilitacion Jurisdiccional"
            };
        }

        return { title: "Tramite", subtitle: "" };
    };

    let filtered = state.tramites.filter(t => {
        const q = (state.tramiteFilter || '').toLowerCase();
        let matchSearch = true;
        if (q) {
            const tipo = state.tipoTramites.find(ti => ti.id === t.tipo_tramite_id)?.nombre || '';
            const owner = getTramiteOwner(t);
            const entName = `${owner.title} ${owner.subtitle}`.trim();
            matchSearch = tipo.toLowerCase().includes(q) || entName.toLowerCase().includes(q);
        }

        let matchDate = true;
        if (state.tramiteDateFilter) {
            matchDate = t.fecha_creacion && t.fecha_creacion.startsWith(state.tramiteDateFilter);
        }

        return matchSearch && matchDate;
    });

    filtered.sort((a, b) => {
        if (state.tramiteSort === 'newest') return new Date(b.fecha_creacion) - new Date(a.fecha_creacion);
        if (state.tramiteSort === 'oldest') return new Date(a.fecha_creacion) - new Date(b.fecha_creacion);
        return 0;
    });

    filtered.forEach(t => {
        const tipo = (state.tipoTramites || []).find(ti => ti.id === t.tipo_tramite_id);
        const owner = getTramiteOwner(t);

        const card = document.createElement('div');
        card.className = 'tramite-card glass-panel';
        card.innerHTML = `
            <div class="tramite-header">
                <h3>${tipo ? tipo.nombre : 'Tramite'}</h3>
                <span class="badge ${t.estado === 'Completo' ? 'badge-success' : 'badge-warning'}">${t.estado}</span>
            </div>
            <p><strong>${owner.title}</strong></p>
            <p style="font-size:0.85rem; color:var(--text-secondary);">${owner.subtitle || '-'}</p>
            <div style="margin-top:1rem; display:flex; justify-content:space-between; align-items:center;">
                <small><i class="fa-solid fa-calendar-day"></i> ${t.fecha_creacion || '-'}</small>
                <div>
                    <button class="btn-primary btn-sm" onclick="viewChecklist(${t.id})"><i class="fa-solid fa-list-check"></i> Checklist</button>
                    <button class="btn-icon text-danger write-action" onclick="deleteTramite(${t.id})"><i class="fa-solid fa-trash-can"></i></button>
                </div>
            </div>
        `;
        grid.appendChild(card);
    });
}

window.filterTramites = function(q) {
    state.tramiteFilter = q;
    renderTramites();
}

window.filterTramitesByDate = function(date) {
    state.tramiteDateFilter = date;
    renderTramites();
}

window.sortTramites = function(order) {
    state.tramiteSort = order;
    renderTramites();
}

window.deleteTramite = async function(id) {
    if (!confirm("¿Desea eliminar/archivar este trámite? Desaparecerá de la pantalla pero se mantendrá en registros.")) return;
    try {
        await fetch(`${API_URL}/tramites/${id}/toggle-activo`, { method: 'PATCH' });
        await refreshState();
    } catch(e) { console.error(e); }
}

function populateSelects() {
    // Asignacion Modal
    document.getElementById('asig-vigilador').innerHTML = state.vigiladores.map(v => `<option value="${v.id}">${v.nombre_completo} (${v.dni})</option>`).join('');
    document.getElementById('asig-empresa').innerHTML = state.empresas.map(e => `<option value="${e.id}">${e.nombre}</option>`).join('');
    
    // Usuario Modal (Empresas para clientes)
    const userEmpresaSelect = document.getElementById('user-empresa-id');
    if (userEmpresaSelect) {
        userEmpresaSelect.innerHTML = state.empresas.map(e => `<option value="${e.id}">${e.nombre}</option>`).join('');
    }

    
    // Rol Modal
    document.getElementById('rol-select').innerHTML = state.roles.map(r => `<option value="${r.id}">${r.nombre}</option>`).join('');
    
    // Tramite Modal (AsignacionRol + Empresas)
    let asigRolesHtml = '<optgroup label="Personal / Vigiladores">';
    state.asignaciones.forEach(a => {
        const vig = state.vigiladores.find(v => v.id === a.vigilador_id);
        (a.roles || []).forEach(ar => {
            const rolName = state.roles.find(r => r.id === ar.rol_id)?.nombre;
            asigRolesHtml += `<option value="${ar.id}">${vig?.nombre_completo} - ${rolName}</option>`;
        });
    });
    asigRolesHtml += '</optgroup><optgroup label="Empresas">';
    state.empresas.forEach(e => {
        asigRolesHtml += `<option value="emp_${e.id}">EMPRESA: ${e.nombre}</option>`;
    });
    asigRolesHtml += '</optgroup>';
    
    document.getElementById('tram-asignacion-rol').innerHTML = asigRolesHtml;
    
    // Tipos Tramite
    document.getElementById('tram-tipo').innerHTML = state.tipoTramites.map(t => `<option value="${t.id}">${t.nombre}</option>`).join('');

    const bibEmpresa = document.getElementById('bib-empresa');
    if (bibEmpresa) {
        bibEmpresa.innerHTML = '<option value="">Sin relacion</option>' + state.empresas.map(e => `<option value="${e.id}">${e.nombre}</option>`).join('');
    }

    const bibVigilador = document.getElementById('bib-vigilador');
    if (bibVigilador) {
        bibVigilador.innerHTML = '<option value="">Sin relacion</option>' + state.vigiladores.map(v => `<option value="${v.id}">${v.nombre_completo}</option>`).join('');
    }
}

function getChecklistOwnerInfo(tramite) {
    if (tramite.empresa_id) {
        const empresa = state.empresas.find(e => e.id === tramite.empresa_id);
        return { tipo: 'Empresa', nombre: empresa ? empresa.nombre : `Empresa #${tramite.empresa_id}`, empresa: null };
    }

    const asignacion = state.asignaciones.find(a => (a.roles || []).some(ar => ar.id === tramite.asignacion_rol_id));
    const vigilador = asignacion ? state.vigiladores.find(v => v.id === asignacion.vigilador_id) : null;
    const empresa = asignacion ? state.empresas.find(e => e.id === asignacion.empresa_id) : null;
    return {
        tipo: 'Persona',
        nombre: vigilador ? vigilador.nombre_completo : `Persona #${tramite.asignacion_rol_id || ''}`,
        empresa: empresa ? empresa.nombre : null
    };
}

function getOpenChecklistTramiteId() {
    const modal = document.getElementById('modal-checklist');
    if (!modal) return null;
    const rawId = modal.dataset.tramiteId;
    const tramiteId = rawId ? parseInt(rawId, 10) : NaN;
    return Number.isNaN(tramiteId) ? null : tramiteId;
}

window.viewChecklist = function(tramiteId) {
    const t = state.tramites.find(x => x.id === tramiteId);
    if (!t) return;

    const owner = getChecklistOwnerInfo(t);
    const checklistModal = document.getElementById('modal-checklist');
    const checklistLabel = document.getElementById('check-tramite-label');
    if (checklistModal) {
        checklistModal.dataset.tramiteId = String(tramiteId);
    }
    if (checklistLabel) {
        checklistLabel.innerText = `"${owner.nombre}"`;
    }
    document.getElementById('check-tramite-owner').innerHTML = `
        <div class="checklist-owner-card">
            <span class="checklist-owner-type">${owner.tipo}</span>
            <strong>${owner.nombre}</strong>
            ${owner.empresa ? `<span class="checklist-owner-company">Empresa: ${owner.empresa}</span>` : ''}
        </div>
    `;
    const reqHtml = t.requisitos.map(r => {
        let stateClass = 'pendiente';
        if(r.estado === 'Subido') stateClass = 'subido';
        if(r.estado === 'Aprobado') stateClass = 'aprobado';
        
        // Uso de descripción inyectada por el backend en main.py:read_tramites
        const nombre = r.descripcion_requisito || `Requisito #${r.id}`;
        const fechaVto = r.fecha_vencimiento || '';
        const url = r.archivo_url || '';
        const hasAdjunto = Boolean(url);
        const resumen = r.estado === 'Aprobado' ? 'OK' : (r.estado === 'Subido' ? 'S' : 'F');
        const resumenColor = r.estado === 'Aprobado' ? 'var(--success)' : (r.estado === 'Subido' ? 'var(--warning)' : 'var(--danger)');

        return `
        <div class="checklist-item ${stateClass}" style="flex-direction: column; align-items: flex-start; gap: 10px; padding: 15px;">
            <div style="width:100%; display:flex; justify-content:space-between; gap:10px; flex-wrap:wrap;">
                <strong>${nombre}</strong>
                <span class="badge ${stateClass}">${r.estado}</span>
            </div>
            <div style="width:100%; display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap;">
                <span class="req-resumen" style="color:${resumenColor}; font-weight:700;">${nombre} = ${resumen}</span>
                <button class="btn-primary btn-sm write-action" onclick="openUploadModal('requisito', ${r.id}, '${nombre.replace(/'/g,"\\'")}')">
                    <i class="fa-solid fa-file-arrow-up"></i> Adjuntar PDF
                </button>
            </div>
            <div class="req-edit-grid" style="width:100%; display:grid; grid-template-columns: 1fr 1fr auto; gap:10px; align-items:end;">
                <div class="input-group write-action" style="margin:0">
                    <label style="font-size:0.7rem">URL Archivo / Referencia</label>
                    <input type="text" id="req-url-${r.id}" value="${url}" placeholder="http://..." style="padding:4px 8px; font-size:0.8rem">
                </div>
                <div class="input-group write-action" style="margin:0">
                    <label style="font-size:0.7rem">Vencimiento</label>
                    <input type="date" id="req-date-${r.id}" value="${fechaVto}" style="padding:4px 8px; font-size:0.8rem">
                </div>
                <button class="btn-primary btn-sm write-action" onclick="guardarRequisito(${r.id})"><i class="fa-solid fa-save"></i></button>
            </div>

            <div id="req-docs-${r.id}" class="req-doc-list" style="width:100%;"></div>
            <div class="req-actions write-action" style="margin-top: 5px; width:100%; text-align:right;">
                ${r.estado !== 'Aprobado'
                    ? `<button class="btn-primary btn-sm" style="background:${hasAdjunto ? 'var(--success)' : 'var(--warning)'}" onclick="marcarReq(${r.id}, 'Aprobado')"><i class="fa-solid ${hasAdjunto ? 'fa-check' : 'fa-file-arrow-up'}"></i> ${hasAdjunto ? 'Aprobar' : 'Adjuntar para aprobar'}</button>`
                    : '<span style="color:var(--success); font-weight:600;"><i class="fa-solid fa-circle-check"></i> Verificado</span>'}
            </div>
        </div>
        `;
    }).join('');
    
    document.getElementById('checklist-items').innerHTML = reqHtml || '<p style="color:var(--text-secondary)">No hay requisitos generados para este trámite.</p>';
    t.requisitos.forEach(r => loadExistingDocuments('requisito', r.id, `req-docs-${r.id}`));
    openModal('modal-checklist');
}

window.openUploadModal = async function(contextType, contextId, label) {
    state.uploadContext = { type: contextType, id: contextId, label };
    document.getElementById('doc-context-type').value = contextType;
    document.getElementById('doc-context-id').value = contextId;
    document.getElementById('doc-context-label').value = label;
    document.getElementById('doc-tipo-documento').value = '';
    document.getElementById('doc-file').value = '';
    document.getElementById('doc-observaciones').value = '';
    document.getElementById('doc-upload-existing').innerHTML = '<p class="chart-empty" style="padding-top:0">Cargando documentos...</p>';
    openModal('modal-upload-documento');
    await loadExistingDocuments(contextType, contextId, 'doc-upload-existing');
}

async function loadExistingDocuments(contextType, contextId, targetId) {
    const target = document.getElementById(targetId);
    if (!target) return;
    const endpoint = `/documentos/${contextType}/${contextId}`;
    try {
        const res = await fetch(`${API_URL}${endpoint}`, {
            headers: getAuthHeaders()
        });
        if (!res.ok) throw new Error('No se pudieron cargar documentos');
        const docs = await res.json();
        if (!docs.length) {
            target.innerHTML = '<p class="chart-empty" style="padding-top:0">No hay documentos cargados.</p>';
            return;
        }
        target.innerHTML = docs.map(doc => `
            <div class="doc-item">
                <div>
                    <strong>${doc.tipo_documento}</strong>
                    <span>${doc.nombre_original}</span>
                    <small style="color:var(--text-secondary);">IA: ${doc.estado_extraccion || 'Pendiente'}${doc.jurisdiccion_referencia ? ` · ${doc.jurisdiccion_referencia}` : ''}</small>
                </div>
                <a class="btn-primary btn-sm" href="${API_URL}/documentos/${doc.id}/view" target="_blank" rel="noopener noreferrer">
                    <i class="fa-solid fa-file-pdf"></i> Abrir
                </a>
            </div>
        `).join('');
    } catch (e) {
        target.innerHTML = '<p class="chart-empty" style="padding-top:0">No fue posible obtener los documentos.</p>';
    }
}

document.getElementById('form-upload-documento').addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!state.uploadContext) return;

    const formData = new FormData();
    formData.append('tipo_documento', document.getElementById('doc-tipo-documento').value.trim());
    formData.append('observaciones', document.getElementById('doc-observaciones').value.trim());
    const file = document.getElementById('doc-file').files[0];
    if (!file) {
        alert('Debe seleccionar un archivo PDF');
        return;
    }
    formData.append('file', file);

    const endpoint = `/documentos/${state.uploadContext.type}/${state.uploadContext.id}/upload`;
    try {
        const res = await fetch(`${API_URL}${endpoint}`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: formData
        });
        const data = await res.json();
        if (!res.ok) {
            alert(`Error: ${data.detail || 'No se pudo subir el documento'}`);
            return;
        }
        await refreshState();
        await loadExistingDocuments(state.uploadContext.type, state.uploadContext.id, 'doc-upload-existing');
        if (state.uploadContext.type === 'requisito') {
            const tId = getOpenChecklistTramiteId();
            if (tId) viewChecklist(tId);
        }
    } catch (err) {
        console.error(err);
        alert('Error al subir documento');
    }
});

window.guardarRequisito = async function(reqId) {
    const url = document.getElementById(`req-url-${reqId}`).value;
    const date = document.getElementById(`req-date-${reqId}`).value;
    
    try {
        await fetch(`${API_URL}/requisitos/${reqId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders()
            },
            body: JSON.stringify({ 
                archivo_url: url,
                fecha_vencimiento: date || null,
                estado: url ? "Subido" : "Faltante"
            })
        });
        await refreshState();
        // Refresh modal content without closing
        const tId = getOpenChecklistTramiteId();
        if (tId) viewChecklist(tId);
    } catch(e) { console.error(e); }
}

window.marcarReq = async function(reqId, action) {
    const tramiteId = getOpenChecklistTramiteId();
    if (!tramiteId) return;
    const tramite = state.tramites.find(t => t.id === tramiteId);
    const requisito = tramite?.requisitos?.find(r => r.id === reqId);

    if (action === 'Aprobado' && !requisito?.archivo_url) {
        const nombre = requisito?.descripcion_requisito || `Requisito #${reqId}`;
        alert('Debe adjuntar documentacion PDF antes de aprobar este requisito.');
        await openUploadModal('requisito', reqId, nombre);
        return;
    }

    try {
        const res = await fetch(`${API_URL}/requisitos/${reqId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders()
            },
            body: JSON.stringify({ estado: action })
        });
        if (!res.ok) {
            const err = await res.json();
            alert(`Error: ${err.detail || 'No se pudo actualizar el requisito'}`);
            return;
        }
        await refreshState();
        viewChecklist(tramiteId);
    } catch(e) { console.error(e); }
}

// ─── INFORME DE ESTADO ─────────────────────────────────────────────────────
let informeSearchTimer = null;

window.searchInforme = function(query) {
    clearTimeout(informeSearchTimer);
    const ul = document.getElementById('informe-suggestions');
    if (query.length < 2) { ul.innerHTML = ''; ul.style.display = 'none'; return; }
    informeSearchTimer = setTimeout(async () => {
        try {
            const res = await fetch(`${API_URL}/empresas/informe/?q=${encodeURIComponent(query)}`, {
                headers: getAuthHeaders()
            });
            const data = await res.json();
            if (!data.length) { ul.innerHTML = '<li style="opacity:0.5;padding:0.75rem 1rem;">Sin resultados</li>'; ul.style.display = 'block'; return; }
            ul.innerHTML = data.map(e => `
                <li onclick="loadInforme(${e.id}, '${e.nombre.replace(/'/g,"\\'")}')">
                    <strong>${e.nombre}</strong> <span style="color:var(--text-secondary); font-size:0.8rem;">${e.cuit}</span>
                </li>
            `).join('');
            ul.style.display = 'block';
        } catch(err) { console.error(err); }
    }, 300);
}

window.loadInforme = async function(id, nombre) {
    // Close dropdown
    document.getElementById('search-informe').value = nombre;
    document.getElementById('informe-suggestions').innerHTML = '';
    document.getElementById('informe-suggestions').style.display = 'none';

    // Fetch full informe
    const res = await fetch(`${API_URL}/empresas/${id}/informe`, {
        headers: getAuthHeaders()
    });
    if (!res.ok) { alert('Error al cargar informe'); return; }
    const data = await res.json();
    renderInformeDashboard(data);
}

function renderInformeDashboard(data) {
    state.currentReport = data; // Guardar referencia para el popup
    const emp = data.empresa;
    const dash = document.getElementById('informe-dashboard');

    // Header
    document.getElementById('inf-nombre').innerText = emp.nombre;
    document.getElementById('inf-cuit').innerText = `CUIT: ${emp.cuit}`;
    document.getElementById('inf-dir').innerText = emp.direccion || '-';
    
    // Links para Teléfono y Email
    const telSpan = document.getElementById('inf-tel');
    const telLink = document.getElementById('inf-tel-link');
    telSpan.innerText = emp.telefono || '-';
    telLink.href = emp.telefono ? `tel:${emp.telefono}` : '#';
    telLink.style.pointerEvents = emp.telefono ? 'auto' : 'none';

    const emailSpan = document.getElementById('inf-email');
    const emailLink = document.getElementById('inf-email-link');
    emailSpan.innerText = emp.email || '-';
    emailLink.href = emp.email ? `mailto:${emp.email}` : '#';
    emailLink.style.pointerEvents = emp.email ? 'auto' : 'none';

    document.getElementById('inf-vto').innerText = emp.fecha_vencimiento_hab
        ? new Date(emp.fecha_vencimiento_hab).toLocaleDateString() : '-';

    const estadoColores = { 'HABILITADO': 'var(--success)', 'POR VENCER': 'var(--warning)', 'VENCIDO': 'var(--danger)', 'Sin fecha': 'var(--text-secondary)' };
    const badge = document.getElementById('inf-estado-badge');
    badge.innerText = emp.estado_habilitacion;
    badge.style.color = estadoColores[emp.estado_habilitacion] || 'white';
    badge.style.border = `2px solid ${estadoColores[emp.estado_habilitacion] || 'white'}`;

    // Jurisdicciones
    const jGrid = document.getElementById('inf-jurisdicciones');
    jGrid.innerHTML = data.jurisdicciones.map(j => {
        const estado = j.estado;
        const color = estado === 'Completo' ? 'var(--success)' : (estado === 'Sin trámite' ? 'var(--text-secondary)' : 'var(--warning)');
        
        let pendingHtml = '';
        if (j.pendientes && j.pendientes.length > 0) {
            pendingHtml = j.pendientes.map(p => `<span class="inf-jurisd-pendiente"><i class="fa-solid fa-clock"></i> ${p}</span>`).join('');
        }
        
        const actionHtml = `<div class="inf-jurisd-card glass-panel" onclick="openInformeAction(${emp.id}, '${j.nombre}', ${j.id || 'null'})">`;

        return `
        ${actionHtml}
            <div class="inf-jurisd-name">${j.nombre}</div>
            <div class="inf-jurisd-estado" style="color:${color};">${estado}</div>
            <div style="text-align:left; margin-top:10px;">
                ${pendingHtml || (j.id ? '' : '<span style="font-size:0.7rem;opacity:0.6;">Haga clic para iniciar trámite de empresa</span>')}
            </div>
        </div>`;
    }).join('');

    // Vigiladores table - Solo mostrar si tienen temas pendientes (requisitos faltantes)
    const tbody = document.getElementById('inf-tbody-vigiladores');
    
    // Filtrar vigiladores que tengan al menos un trámite pendiente o incompleto 
    // (O según el criterio del usuario: omitir 0/0 de requisitos)
    const filteredVig = data.vigiladores.map(v => {
        const filteredRoles = v.roles.map(r => {
            const filteredTrams = r.tramites.filter(t => t.estado !== 'Completo' && t.total_requisitos > 0);
            return { ...r, tramites: filteredTrams };
        }).filter(r => r.tramites.length > 0);
        return { ...v, roles: filteredRoles };
    }).filter(v => v.roles.length > 0);

    if (!filteredVig.length) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; opacity:0.5; padding: 2rem;">No hay personal con requisitos pendientes.</td></tr>';
    } else {
        tbody.innerHTML = filteredVig.map(v => {
            const colores = { 'HABILITADO': 'var(--success)', 'POR VENCER': 'var(--near-vence)', 'VENCIDO': 'var(--danger)', 'Sin fecha': 'var(--text-secondary)' };
            const col = colores[v.estado_habilitacion] || 'white';
            const vto = v.fecha_vencimiento_hab || '-';
            
            const rolesHtml = v.roles.map(r => {
                const trams = r.tramites.map(t =>
                    `<span class="badge clickable pendiente" 
                           onclick="navToTramite(${t.id}); event.stopPropagation();" 
                           style="margin-left:4px;">${t.tipo} ${t.aprobados}/${t.total_requisitos}</span>`
                ).join('');
                return `<div style="margin-bottom:4px;"><i class="fa-solid fa-id-badge"></i> ${r.rol}${trams}</div>`;
            }).join('');

            return `
            <tr>
                <td><a href="#" class="inf-person-link" onclick="openEditVigilador(${v.id}); event.preventDefault();">${v.nombre_completo}</a></td>
                <td>${v.dni}</td>
                <td style="font-size:0.75rem;">${v.nombre_jurisdiccion || '-'}</td>
                <td class="${v.estado_habilitacion === 'VENCIDO' ? 'status-vencido' : (v.estado_habilitacion === 'POR VENCER' ? 'status-por-vencer' : '')}">${vto}</td>
                <td style="color:${col}; font-weight:600;">${v.estado_habilitacion}</td>
                <td style="font-size:0.8rem;">${rolesHtml}</td>
            </tr>`;
        }).join('');
    }

    dash.style.display = 'block';
}

window.openInformeAction = function(empresaId, tipoNombre, tramiteId) {
    const body = document.getElementById('inf-action-body');
    const title = document.getElementById('inf-action-title');
    title.innerText = `Opciones de Trámite: ${tipoNombre}`;
    
    let html = '';
    
    // 1. Ver Existente (si hay uno en el resumen)
    if (tramiteId) {
        html += `
            <div style="background: rgba(255,255,255,0.05); padding: 10px; border-radius: 8px; margin-bottom: 5px;">
                <p style="font-size: 0.8rem; margin: 0 0 10px 0; opacity: 0.7;">Existe un trámite activo en esta jurisdicción:</p>
                <button class="btn-primary w-100" onclick="closeModal('modal-informe-action'); navToTramite(${tramiteId})">
                    <i class="fa-solid fa-list-check"></i> Ver Trámite Existente
                </button>
            </div>
            <p style="font-size: 0.7rem; margin: 10px 0; opacity: 0.5;">O INICIAR UNO NUEVO:</p>
        `;
    } else {
        html += `<p style="font-size: 0.9rem; margin-bottom: 10px;">Seleccione el destinatario del nuevo trámite:</p>`;
    }
    
    // 2. Opciones de Nuevo Trámite
    html += `
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
            <button class="btn-primary" style="background: var(--accent-color); padding: 15px 5px;" onclick="closeModal('modal-informe-action'); startEmpresaTramite(${empresaId}, '${tipoNombre}')">
                <i class="fa-solid fa-building"></i> PARA LA EMPRESA
            </button>
            <button class="btn-primary" style="background: var(--secondary-color); padding: 15px 5px;" onclick="showPersonnelListForTramite('${tipoNombre}')">
                <i class="fa-solid fa-users"></i> PARA PERSONAL
            </button>
        </div>
        <div id="personnel-selection-area" style="margin-top: 15px; display: none; text-align: left;">
             <label style="font-size: 0.8rem; opacity: 0.7;">Seleccione el Vigilador:</label>
             <select id="inf-select-vigilador" style="width:100%; margin-top:5px; padding: 8px; background: rgba(0,0,0,0.3); color:white; border: 1px solid rgba(255,255,255,0.1); border-radius: 5px;">
             </select>
             <button class="btn-primary w-100" style="margin-top: 10px;" onclick="startPersonnelTramiteFromInforme('${tipoNombre}')">Iniciar Trámite de Personal</button>
        </div>
    `;
    
    body.innerHTML = html;
    openModal('modal-informe-action');
}

window.showPersonnelListForTramite = function(tipoNombre) {
    const area = document.getElementById('personnel-selection-area');
    const select = document.getElementById('inf-select-vigilador');
    
    // Poblar con los vigiladores del reporte actual
    const vgs = state.currentReport.vigiladores;
    if (!vgs || vgs.length === 0) {
        alert("No hay vigiladores asignados a esta empresa.");
        return;
    }
    
    // Necesitamos encontrar el asignacion_rol_id. 
    // Como un vigilador puede tener varios roles, mostramos Vigilador - Rol
    let options = '';
    vgs.forEach(v => {
        v.roles.forEach(r => {
            // Buscamos el ID real de la asignación de rol. 
            // state.currentReport no tiene el ID directamente en el formato compacto, 
            // pero podemos buscarlo en state.asignaciones
            const asig = state.asignaciones.find(a => a.vigilador_id === v.id && a.empresa_id === state.currentReport.empresa.id);
            if(asig) {
                const asigRol = asig.roles.find(ar => {
                     const rol = state.roles.find(role => role.id === ar.rol_id);
                     return rol && rol.nombre === r.rol;
                });
                if(asigRol) {
                    options += `<option value="${asigRol.id}">${v.nombre_completo} - ${r.rol}</option>`;
                }
            }
        });
    });
    
    if(!options) {
        alert("No se encontraron roles activos para el personal.");
        return;
    }
    
    select.innerHTML = options;
    area.style.display = 'block';
}

window.startPersonnelTramiteFromInforme = async function(tipoNombre) {
    const asigRolId = document.getElementById('inf-select-vigilador').value;
    const tipo = state.tiposTramites.find(t => t.nombre === tipoNombre);
    if (!tipo || !asigRolId) return;

    // VALIDACION PREVIA: La empresa debe tener tramite iniciado en esta jurisdiccion
    const empId = state.currentReport.empresa.id;
    const companyTramite = state.tramites.find(t => t.empresa_id === empId && t.tipo_tramite_id === tipo.id);
    
    if (!companyTramite) {
        const vigName = document.getElementById('inf-select-vigilador').options[document.getElementById('inf-select-vigilador').selectedIndex].text;
        const empName = state.currentReport.empresa.nombre;
        alert(`Para poder generar el tramite del vigilador ${vigName} la ${empName} debe tener iniciados sus tramites de habilitacion`);
        return;
    }

    try {
        const res = await fetch(`${API_URL}/tramites/`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ 
                asignacion_rol_id: parseInt(asigRolId),
                tipo_tramite_id: tipo.id,
                estado: "Pendiente"
            })
        });
        if (res.ok) {
            alert("Trámite de personal iniciado correctamente.");
            closeModal('modal-informe-action');
            await refreshState();
            loadInforme(state.currentReport.empresa.id, state.currentReport.empresa.nombre);
        } else {
            const err = await res.json();
            alert(`Error: ${err.detail}`);
        }
    } catch(e) { console.error(e); }
}

window.navToTramite = function(id) {
    // Switch section
    const navItem = document.querySelector('li[data-section="tramites"]');
    if (navItem) navItem.click();
    
    // Highlight or open checklist
    setTimeout(() => {
        const card = document.getElementById(`tramite-card-${id}`);
        if(card) {
            card.scrollIntoView({ behavior: 'smooth', block: 'center' });
            card.style.outline = '4px solid var(--accent-color)';
            card.style.outlineOffset = '4px';
            setTimeout(() => card.style.outline = 'none', 3000);
            viewChecklist(id);
        }
    }, 300);
}

window.startEmpresaTramite = async function(empId, tipoName) {
    const tipo = state.tipoTramites.find(t => t.nombre === tipoName);
    if (!tipo) return;
    
    if (!confirm(`¿Iniciar trámite de habilitación de EMPRESA para ${tipoName}?`)) return;
    
    try {
        const res = await fetch(`${API_URL}/empresas/${empId}/tramites/${tipo.id}`, { method: 'POST' });
        if (res.ok) {
            const data = await res.json();
            alert("Trámite de empresa iniciado correctamente.");
            await refreshState();
            // Refresh dashboard
            loadInforme(empId, state.empresas.find(e => e.id === empId).nombre);
        } else {
            const err = await res.json();
            alert(`Error: ${err.detail}`);
        }
    } catch(e) { console.error(e); }
}
// ─── SEGURIDAD / USUARIOS ───────────────────────────────────────────────────
window.renderBiblioteca = function() {
    const tbody = document.getElementById('tbody-biblioteca');
    if (!tbody) return;

    const search = (document.getElementById('search-biblioteca')?.value || '').trim().toLowerCase();
    const categoria = document.getElementById('filter-biblioteca-categoria')?.value || '';
    const jurisdiccion = (document.getElementById('filter-biblioteca-jurisdiccion')?.value || '').trim().toLowerCase();

    const rows = state.biblioteca.filter(item => {
        const hayCategoria = !categoria || item.categoria === categoria;
        const hayJurisdiccion = !jurisdiccion || (item.jurisdiccion || '').toLowerCase().includes(jurisdiccion);
        const searchable = [
            item.titulo,
            item.tema,
            item.organismo,
            item.tags,
            item.categoria,
            item.jurisdiccion,
            item.resumen_referencia,
            item.estado_extraccion
        ].filter(Boolean).join(' ').toLowerCase();
        const hayBusqueda = !search || searchable.includes(search);
        return hayCategoria && hayJurisdiccion && hayBusqueda;
    });

    if (!rows.length) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" style="color:var(--text-secondary);">No hay documentos cargados en la biblioteca para el filtro actual.</td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = rows.map(item => {
        const empresa = item.empresa_id ? state.empresas.find(e => e.id === item.empresa_id) : null;
        const vigilador = item.vigilador_id ? state.vigiladores.find(v => v.id === item.vigilador_id) : null;
        const vinculo = [empresa?.nombre, vigilador?.nombre_completo].filter(Boolean).join(' / ') || '-';
        return `
            <tr>
                <td>
                    <strong>${item.titulo}</strong>
                    <small style="display:block; color:var(--text-secondary); font-size:0.75rem;">${item.fecha_documento || item.fecha_carga || '-'}</small>
                </td>
                <td><span class="badge ${item.categoria === 'Normativa' ? 'badge-success' : 'badge-warning'}">${item.categoria}</span></td>
                <td>${item.jurisdiccion || '-'}</td>
                <td>${item.organismo || '-'}</td>
                <td>${item.tema || '-'}</td>
                <td>${item.vigencia || '-'}</td>
                <td>${vinculo}</td>
                <td>
                    <small style="display:block; color:var(--text-secondary); margin-bottom:0.35rem;">IA: ${item.estado_extraccion || 'Pendiente'}</small>
                    <a class="btn-primary btn-sm" href="${API_URL}/biblioteca/${item.id}/view" target="_blank" rel="noopener noreferrer">
                        <i class="fa-solid fa-file-pdf"></i> Abrir
                    </a>
                </td>
            </tr>
        `;
    }).join('');
}

async function renderUsuarios() {
    const tbody = document.getElementById('tbody-usuarios');
    if (!tbody) return;
    try {
        const res = await fetch(`${API_URL}/users/`, {
            headers: getAuthHeaders()
        });
        if (!res.ok) return;
        const users = await res.json();
        tbody.innerHTML = users.map(u => {
            const emp = u.empresa_id ? state.empresas.find(e => e.id === u.empresa_id) : null;
            const empName = emp ? emp.nombre : '-';
            // Mostrar el nombre de la empresa como nombre de usuario para Clientes
            const displayName = u.role === 'Cliente' && emp ? emp.nombre : u.username;
            
            const roleLabel = { 'Admin': 'Administrador', 'Cliente': 'Empresa', 'Consultor': 'Consultor' }[u.role] || u.role;
            const privClass = { 'Admin': 'badge-admin', 'Editar': 'badge-editar', 'Ver': 'badge-ver' }[u.privilege] || 'badge-ver';
            const privLabel = { 'Admin': 'Admin', 'Editar': 'Editor', 'Ver': 'Consulta' }[u.privilege] || 'Ver';

            return `
            <tr>
                <td>
                    <strong>${displayName}</strong>
                    <small style="display:block; color:var(--text-secondary); font-size:0.75rem;">${u.username}</small>
                </td>
                <td><span class="badge badge-warning">${roleLabel}</span></td>
                <td><span class="badge ${privClass}">${privLabel}</span></td>
                <td>${empName}</td>
                <td style="display:flex; gap:6px;">
                    <button class="btn-icon" title="Editar" onclick="openEditUsuario(${u.id})"><i class="fa-solid fa-pen"></i></button>
                    <button class="btn-icon" title="Resetear contrasena" onclick="promptResetPassword(${u.id}, '${displayName}')"><i class="fa-solid fa-key"></i></button>
                    ${u.username !== 'admin' ? `<button class="btn-icon text-danger" title="Eliminar" onclick="deleteUsuario(${u.id})"><i class="fa-solid fa-user-minus"></i></button>` : ''}
                </td>
            </tr>
            `;
        }).join('');
    } catch(e) { console.error(e); }
}

// Abrir modal para editar un usuario existente
window.openEditUsuario = async function(userId) {
    try {
        const res = await fetch(`${API_URL}/users/`, {
            headers: getAuthHeaders()
        });
        if (!res.ok) return;
        const users = await res.json();
        const u = users.find(x => x.id === userId);
        if (!u) return;

        document.getElementById('modal-usuario-title').innerHTML = '<i class="fa-solid fa-user-pen"></i> Editar Usuario';
        document.getElementById('user-edit-id').value = u.id;
        document.getElementById('user-role').value = u.role;
        document.getElementById('user-privilege').value = u.privilege || 'Ver';
        document.getElementById('user-password-hint').style.display = 'block';
        document.getElementById('user-password').value = '';
        document.getElementById('user-password').required = false;
        toggleUserRole(u.role);
        
        if (u.role === 'Cliente' && u.empresa_id) {
            document.getElementById('user-empresa-id').value = u.empresa_id;
        } else {
            document.getElementById('user-username').value = u.username;
        }

        openModal('modal-usuario');
    } catch(e) { console.error(e); }
}

// Reset de contrasena con prompt
window.promptResetPassword = async function(userId, nombre) {
    const newPass = prompt(`Nueva contrasena para "${nombre}":`);
    if (!newPass || newPass.trim() === '') return;
    try {
        const res = await fetch(`${API_URL}/users/${userId}/reset-password`, {
            method: 'PATCH',
            headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ new_password: newPass })
        });
        if (res.ok) {
            alert('Contrasena actualizada correctamente.');
        } else {
            const err = await res.json();
            alert('Error: ' + err.detail);
        }
    } catch(e) { console.error(e); }
}

window.toggleUserEmpresa = function(role) {
    const group = document.getElementById('user-empresa-group');
    group.style.display = (role === 'Cliente') ? 'block' : 'none';
}

// Controla qué campos mostrar según el tipo de usuario
window.toggleUserRole = function(role) {
    const empGroup = document.getElementById('user-empresa-group');
    const userGroup = document.getElementById('user-username-group');
    const privGroup = document.getElementById('user-privilege-group');
    if (role === 'Cliente') {
        empGroup.style.display = 'block';
        userGroup.style.display = 'none';
        // Auto-seleccionar privilegio Ver para Cliente y ocultarlo
        document.getElementById('user-privilege').value = 'Ver';
    } else if (role === 'Admin') {
        empGroup.style.display = 'none';
        userGroup.style.display = 'block';
        document.getElementById('user-privilege').value = 'Admin';
    } else {
        empGroup.style.display = 'none';
        userGroup.style.display = 'block';
    }
}

document.getElementById('form-biblioteca').addEventListener('submit', async (e) => {
    e.preventDefault();

    const file = document.getElementById('bib-file').files[0];
    if (!file) {
        alert('Debe seleccionar un archivo PDF para la biblioteca.');
        return;
    }

    const formData = new FormData();
    formData.append('titulo', document.getElementById('bib-titulo').value.trim());
    formData.append('categoria', document.getElementById('bib-categoria').value);
    formData.append('jurisdiccion', document.getElementById('bib-jurisdiccion').value.trim());
    formData.append('organismo', document.getElementById('bib-organismo').value.trim());
    formData.append('tema', document.getElementById('bib-tema').value.trim());
    formData.append('fecha_documento', document.getElementById('bib-fecha-documento').value);
    formData.append('vigencia', document.getElementById('bib-vigencia').value);
    formData.append('tags', document.getElementById('bib-tags').value.trim());
    formData.append('observaciones', document.getElementById('bib-observaciones').value.trim());

    const empresaId = document.getElementById('bib-empresa').value;
    const vigiladorId = document.getElementById('bib-vigilador').value;
    if (empresaId) formData.append('empresa_id', empresaId);
    if (vigiladorId) formData.append('vigilador_id', vigiladorId);

    formData.append('file', file);

    try {
        const res = await fetch(`${API_URL}/biblioteca/upload`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: formData
        });
        const data = await res.json();
        if (!res.ok) {
            alert(`Error: ${data.detail || 'No se pudo guardar el documento en biblioteca'}`);
            return;
        }

        document.getElementById('form-biblioteca').reset();
        closeModal('modal-biblioteca');
        await refreshState();
        showSection('biblioteca');
    } catch (err) {
        console.error(err);
        alert('Error al guardar el documento en biblioteca.');
    }
});

document.getElementById('form-usuario').addEventListener('submit', async (e) => {
    e.preventDefault();
    const headers = getAuthHeaders({ 'Content-Type': 'application/json' });
    const role = document.getElementById('user-role').value;
    const editId = document.getElementById('user-edit-id').value;
    const password = document.getElementById('user-password').value;
    
    let username;
    let empresaId = null;
    if (role === 'Cliente') {
        const empId = parseInt(document.getElementById('user-empresa-id').value);
        const emp = state.empresas.find(x => x.id === empId);
        username = emp ? emp.nombre : `empresa_${empId}`;
        empresaId = empId;
    } else {
        username = document.getElementById('user-username').value.trim();
    }

    const privilege = document.getElementById('user-privilege').value;

    if (editId) {
        // EDITAR usuario existente
        const data = { username, role, privilege, empresa_id: empresaId };
        const res = await fetch(`${API_URL}/users/${editId}`, {
            method: 'PUT', headers, body: JSON.stringify(data)
        });
        if (res.ok) {
            // Si se ingreso contrasena, resetearla
            if (password) {
                await fetch(`${API_URL}/users/${editId}/reset-password`, {
                    method: 'PATCH', headers,
                    body: JSON.stringify({ new_password: password })
                });
            }
            closeModal('modal-usuario');
            renderUsuarios();
        } else {
            const err = await res.json();
            alert(err.detail);
        }
    } else {
        // CREAR nuevo usuario
        if (!password) { alert('La contrasena es obligatoria para nuevos usuarios.'); return; }
        const data = { username, password, role, privilege, empresa_id: empresaId };
        const res = await fetch(`${API_URL}/users/`, {
            method: 'POST', headers, body: JSON.stringify(data)
        });
        if (res.ok) {
            closeModal('modal-usuario');
            renderUsuarios();
        } else {
            const err = await res.json();
            alert(err.detail);
        }
    }
});

window.deleteUsuario = async function(id) {
    if(!confirm('Eliminar este usuario?')) return;
    await fetch(`${API_URL}/users/${id}`, {
        method: 'DELETE',
        headers: getAuthHeaders()
    });
    renderUsuarios();
}

// Setup inicial del modal de usuario
document.getElementById('modal-usuario').addEventListener('click', function(e) {
    if (e.target === this) closeModal('modal-usuario');
});

// Resetear modal al abrir para nuevo usuario
const _origOpenModal = window.openModal;
window.openModal = function(id) {
    if (id === 'modal-usuario' && !document.getElementById('user-edit-id').value) {
        document.getElementById('modal-usuario-title').innerHTML = '<i class="fa-solid fa-user-plus"></i> Nuevo Usuario';
        document.getElementById('user-edit-id').value = '';
        document.getElementById('form-usuario').reset();
        document.getElementById('user-password-hint').style.display = 'none';
        document.getElementById('user-password').required = true;
        toggleUserRole('Admin');
    }
    document.getElementById(id).classList.add('active');
}
