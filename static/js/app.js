const API_URL = ""; // Assuming relative path since it's hosted on the same server

// Core state
let state = {
    empresas: [],
    vigiladores: [],
    asignaciones: [],
    roles: [],
    tiposTramites: [],
    tramites: [],
    plantillas: [],
    tramiteFilter: '',
    currentReport: null
};

// Start
document.addEventListener("DOMContentLoaded", async () => {
    initNavigation();
    await fetchAllData();
    renderAll();
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
    try {
        const [empRes, vigRes, asigRes, rolRes, tipoRes, tramRes] = await Promise.all([
            fetch(`${API_URL}/empresas/`),
            fetch(`${API_URL}/vigiladores/`),
            fetch(`${API_URL}/asignaciones/`),
            fetch(`${API_URL}/roles/`),
            fetch(`${API_URL}/tipos-tramites/`),
            fetch(`${API_URL}/tramites/`)
        ]);
        
        state.empresas = await empRes.json();
        state.vigiladores = await vigRes.json();
        state.asignaciones = await asigRes.json();
        state.roles = await rolRes.json();
        state.tiposTramites = await tipoRes.json();
        state.tramites = await tramRes.json();
        
    } catch (e) {
        console.error("Error connecting to API", e);
    }
}

function renderAll() {
    updateDashboardStats();
    renderAlertasDashboard();
    renderEmpresas();
    renderVigiladores();
    renderAsignaciones();
    renderTramites();
    populateSelects();
}

function updateDashboardStats() {
    document.getElementById('count-empresas').innerText = state.empresas.length;
    document.getElementById('count-vigiladores').innerText = state.vigiladores.length;
    document.getElementById('count-tramites').innerText = state.tramites.length;
}

function renderAlertasDashboard() {
    const grid = document.getElementById('grid-alertas');
    const hoy = new Date();
    const UN_MES = 30 * 24 * 60 * 60 * 1000;
    
    let alertasHtml = '';

    // Revisar empresas
    state.empresas.forEach(emp => {
        if(emp.fecha_vencimiento_hab) {
            const vto = new Date(emp.fecha_vencimiento_hab);
            const diff = vto - hoy;
             // Si falta menos de un mes o ya vencio
            if (diff < UN_MES) {
                const isVencido = diff < 0;
                alertasHtml += `
                    <div class="tramite-card glass-panel" style="border-top-color: var(--danger)">
                        <div style="display:flex; justify-content:space-between">
                            <h4>Empresa: ${emp.nombre}</h4>
                            <span class="badge" style="background:var(--danger); color:white">${isVencido ? 'VENCIDA' : 'POR VENCER'}</span>
                        </div>
                        <p><i class="fa-solid fa-calendar-xmark"></i> Vto: ${vto.toLocaleDateString()}</p>
                    </div>
                `;
            }
        }
    });

    // Revisar vigiladores
    state.vigiladores.forEach(vig => {
        if(vig.fecha_vencimiento_hab) {
            const vto = new Date(vig.fecha_vencimiento_hab);
            const diff = vto - hoy;
            if (diff < UN_MES) {
                const isVencido = diff < 0;
                alertasHtml += `
                    <div class="tramite-card glass-panel" style="border-top-color: var(--warning)">
                        <div style="display:flex; justify-content:space-between">
                            <h4>Vigilador: ${vig.nombre_completo}</h4>
                            <span class="badge" style="background:var(--warning); color:white">${isVencido ? 'VENCIDO' : 'POR VENCER'}</span>
                        </div>
                        <p><i class="fa-solid fa-calendar-xmark"></i> Vto: ${vto.toLocaleDateString()}</p>
                    </div>
                `;
            }
        }
    });

    if(!alertasHtml) {
        alertasHtml = '<p style="color:var(--text-secondary)">No hay vencimientos próximos.</p>';
    }
    grid.innerHTML = alertasHtml;
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

// Render Functions
function renderEmpresas() {
    const tbody = document.getElementById('tbody-empresas');
    tbody.innerHTML = state.empresas.map(e => {
        const vto = e.fecha_vencimiento_hab ? new Date(e.fecha_vencimiento_hab).toLocaleDateString() : '-';
        const isExpired = e.fecha_vencimiento_hab && (new Date(e.fecha_vencimiento_hab) < new Date());
        return `
        <tr>
            <td>#${e.id}</td>
            <td><strong>${e.nombre}</strong></td>
            <td>${e.cuit}</td>
            <td>${e.telefono || '-'}</td>
            <td style="color: ${isExpired ? 'var(--danger)' : 'inherit'}">${vto}</td>
            <td style="display:flex; gap:6px;">
                <button class="btn-primary btn-sm" onclick="openEditEmpresa(${e.id})"><i class="fa-solid fa-pen"></i></button>
                <button class="btn-primary btn-sm" style="background:var(--danger)" onclick="deleteEmpresa(${e.id}, '${e.nombre}')"><i class="fa-solid fa-trash"></i></button>
            </td>
        </tr>
    `}).join('');
}

function renderVigiladores() {
    const tbody = document.getElementById('tbody-vigiladores');
    tbody.innerHTML = state.vigiladores.map(v => {
        const vto = v.fecha_vencimiento_hab ? new Date(v.fecha_vencimiento_hab).toLocaleDateString() : '-';
        const isExpired = v.fecha_vencimiento_hab && (new Date(v.fecha_vencimiento_hab) < new Date());
        return `
        <tr>
            <td>#${v.id}</td>
            <td><strong>${v.nombre_completo}</strong></td>
            <td>${v.dni}</td>
            <td>${v.legajo || '-'}</td>
            <td style="color: ${isExpired ? 'var(--danger)' : 'inherit'}">${vto}</td>
            <td style="display:flex; gap:6px;">
                <button class="btn-primary btn-sm" onclick="openEditVigilador(${v.id})"><i class="fa-solid fa-pen"></i></button>
                <button class="btn-primary btn-sm" style="background:var(--danger)" onclick="deleteVigilador(${v.id}, '${v.nombre_completo}')"><i class="fa-solid fa-trash"></i></button>
            </td>
        </tr>
    `}).join('');
}

function renderAsignaciones() {
    const tbody = document.getElementById('tbody-asignaciones');
    tbody.innerHTML = state.asignaciones.map(a => {
        const vig = state.vigiladores.find(v => v.id === a.vigilador_id);
        const emp = state.empresas.find(e => e.id === a.empresa_id);
        
        const rolesHtml = (a.roles || []).map(r => {
            const rolData = state.roles.find(ro => ro.id === r.rol_id);
            return `<span class="badge" style="background:var(--accent-color)">${rolData ? rolData.nombre : 'Rol'}</span>`;
        }).join(' ');

        return `
        <tr>
            <td>#${a.id}</td>
            <td>${vig ? vig.nombre_completo : '-'}</td>
            <td>${emp ? emp.nombre : '-'}</td>
            <td>${rolesHtml || 'Sin roles'}</td>
            <td>
                <button class="btn-primary btn-sm" onclick="openRolModal(${a.id})"><i class="fa-solid fa-plus"></i> Añadir Rol</button>
            </td>
        </tr>
    `}).join('');
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
    const filtered = state.tramites.filter(t => {
        if (!state.tramiteFilter) return true;
        const q = state.tramiteFilter.toLowerCase();
        // Buscar por tipo o por etiqueta (persona/empresa)
        const tipo = state.tiposTramites.find(ti => ti.id === t.tipo_tramite_id)?.nombre || '';
        let label = "";
        if (t.asignacion_rol_id) {
            const ar = state.asignaciones.flatMap(a => a.roles).find(r => r.id === t.asignacion_rol_id);
            const asig = ar ? state.asignaciones.find(a => a.roles.includes(ar)) : null;
            const vig = asig ? state.vigiladores.find(v => v.id === asig.vigilador_id) : null;
            label = vig ? vig.nombre_completo : "";
        } else if (t.empresa_id) {
            label = state.empresas.find(e => e.id === t.empresa_id)?.nombre || "";
        }
        return tipo.toLowerCase().includes(q) || label.toLowerCase().includes(q);
    });

    grid.innerHTML = filtered.map(t => {
        const tipo = state.tiposTramites.find(ti => ti.id === t.tipo_tramite_id);
        const isCompleto = t.estado === 'Completo';
        const pendingReqs = (t.requisitos || []).filter(r => r.estado !== 'Aprobado').length;

        let label = "Desconocido";
        if (t.asignacion_rol_id) {
            const ar = state.asignaciones.flatMap(a => a.roles).find(r => r.id === t.asignacion_rol_id);
            const asig = ar ? state.asignaciones.find(a => a.roles.includes(ar)) : null;
            const vig = asig ? state.vigiladores.find(v => v.id === asig.vigilador_id) : null;
            const emp = asig ? state.empresas.find(e => e.id === asig.empresa_id) : null;
            label = vig ? `${vig.nombre_completo} (${emp ? emp.nombre : '?'})` : "Personal";
        } else if (t.empresa_id) {
            const emp = state.empresas.find(e => e.id === t.empresa_id);
            label = `EMPRESA: ${emp ? emp.nombre : '?'}`;
        }

        return `
        <div id="tramite-card-${t.id}" class="tramite-card glass-panel clickable ${isCompleto ? 'completo' : ''}" onclick="viewChecklist(${t.id})">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div>
                    <h3>${tipo ? tipo.nombre : 'Trámite'}</h3>
                    <span class="badge ${isCompleto ? 'completo' : 'pendiente'}">${t.estado}</span>
                </div>
                <button class="btn-icon" style="color:var(--danger); background:none; border:none; cursor:pointer;" onclick="event.stopPropagation(); deleteTramite(${t.id})">
                    <i class="fa-solid fa-trash-can"></i>
                </button>
            </div>
            <p style="margin: 0.5rem 0; font-size:0.9rem; color:var(--accent-color); font-weight:600;">
                <i class="fa-solid fa-building-shield"></i> ${label}
            </p>
            <p><i class="fa-solid fa-list-check"></i> ${(t.requisitos || []).length} Requisitos (${pendingReqs} pendientes)</p>
            <div class="tramite-footer" style="margin-top:1rem; text-align:right;">
                <span style="font-size:0.8rem; opacity:0.7;">Ver Checklist <i class="fa-solid fa-chevron-right"></i></span>
            </div>
        </div>
        `;
    }).join('');
}

window.filterTramites = function(val) {
    state.tramiteFilter = val;
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
    document.getElementById('tram-tipo').innerHTML = state.tiposTramites.map(t => `<option value="${t.id}">${t.nombre}</option>`).join('');
}

window.viewChecklist = function(tramiteId) {
    const t = state.tramites.find(tr => tr.id === tramiteId);
    if(!t) return;
    
    document.getElementById('check-tramite-id').innerText = t.id;
    
    const reqHtml = (t.requisitos || []).map(r => {
        let stateClass = '';
        if(r.estado === 'Subido') stateClass = 'subido';
        if(r.estado === 'Aprobado') stateClass = 'aprobado';
        
        const nombre = r.descripcion_requisito || `Requisito #${r.id}`;
        const fechaVto = r.fecha_vencimiento || '';
        const url = r.archivo_url || '';

        return `
        <div class="checklist-item ${stateClass}" style="flex-direction: column; align-items: flex-start; gap: 10px; padding: 15px;">
            <div style="width:100%; display:flex; justify-content:space-between;">
                <strong>${nombre}</strong>
                <span class="badge ${stateClass}">${r.estado}</span>
            </div>
            
            <div class="req-edit-fields" style="width:100%; display:grid; grid-template-columns: 1fr 1fr auto; gap: 10px; align-items: end;">
                <div class="input-group" style="margin:0">
                    <label style="font-size:0.7rem">URL Archivo / Referencia</label>
                    <input type="text" id="req-url-${r.id}" value="${url}" placeholder="http://..." style="padding:4px 8px; font-size:0.8rem">
                </div>
                <div class="input-group" style="margin:0">
                    <label style="font-size:0.7rem">Vencimiento</label>
                    <input type="date" id="req-date-${r.id}" value="${fechaVto}" style="padding:4px 8px; font-size:0.8rem">
                </div>
                <button class="btn-primary btn-sm" onclick="guardarRequisito(${r.id})"><i class="fa-solid fa-save"></i></button>
            </div>

            <div class="req-actions" style="margin-top: 5px; width:100%; text-align:right;">
                ${r.estado !== 'Aprobado' ? `<button class="btn-primary btn-sm" style="background:var(--success)" onclick="marcarReq(${r.id}, 'Aprobado')"><i class="fa-solid fa-check"></i> Aprobar</button>` : '<span style="color:var(--success); font-weight:600;"><i class="fa-solid fa-circle-check"></i> Verificado</span>'}
            </div>
        </div>
        `;
    }).join('');
    
    document.getElementById('checklist-items').innerHTML = reqHtml || '<p style="color:var(--text-secondary)">No hay requisitos generados para este trámite.</p>';
    openModal('modal-checklist');
}

window.guardarRequisito = async function(reqId) {
    const url = document.getElementById(`req-url-${reqId}`).value;
    const date = document.getElementById(`req-date-${reqId}`).value;
    
    try {
        await fetch(`${API_URL}/requisitos/${reqId}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ 
                archivo_url: url,
                fecha_vencimiento: date || null,
                estado: url ? "Subido" : "Faltante"
            })
        });
        await refreshState();
        // Refresh modal content without closing
        const tId = document.getElementById('check-tramite-id').innerText;
        viewChecklist(parseInt(tId));
    } catch(e) { console.error(e); }
}

window.marcarReq = async function(reqId, action) {
    try {
        await fetch(`${API_URL}/requisitos/${reqId}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ estado: action })
        });
        await refreshState();
        closeModal('modal-checklist'); // Reabrir para refrescar info o dejar cerrado
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
            const res = await fetch(`${API_URL}/empresas/informe/?q=${encodeURIComponent(query)}`);
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
    const res = await fetch(`${API_URL}/empresas/${id}/informe`);
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

    // Vigiladores table
    const tbody = document.getElementById('inf-tbody-vigiladores');
    if (!data.vigiladores.length) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;opacity:0.5;">Sin personal asignado</td></tr>';
    } else {
        tbody.innerHTML = data.vigiladores.map(v => {
            const colores = { 'HABILITADO': 'var(--success)', 'POR VENCER': 'var(--warning)', 'VENCIDO': 'var(--danger)', 'Sin fecha': 'var(--text-secondary)' };
            const col = colores[v.estado_habilitacion] || 'white';
            const vto = v.fecha_vencimiento_hab ? new Date(v.fecha_vencimiento_hab).toLocaleDateString() : '-';
            // Roles and tramites summary
            const rolesHtml = v.roles.map(r => {
                const trams = r.tramites.map(t =>
                    `<span class="badge clickable ${t.estado === 'Completo' ? 'completo' : 'pendiente'}" 
                           onclick="navToTramite(${t.id}); event.stopPropagation();" 
                           style="margin-left:4px;">${t.tipo} ${t.aprobados}/${t.total_requisitos}</span>`
                ).join('');
                return `<div><i class="fa-solid fa-id-badge"></i> ${r.rol}${trams}</div>`;
            }).join('') || '<span style="opacity:0.5">Sin roles</span>';

            return `
            <tr>
                <td><a href="#" class="inf-person-link" onclick="openEditVigilador(${v.id}); event.preventDefault();">${v.nombre_completo}</a></td>
                <td>${v.dni}</td>
                <td>${v.legajo || '-'}</td>
                <td>${vto}</td>
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
    const tipo = state.tiposTramites.find(t => t.nombre === tipoName);
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
