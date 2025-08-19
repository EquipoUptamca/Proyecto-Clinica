$(document).ready(function() {
            let table;
            let currentFilters = {};

            // Toggle sidebar
            $('#sidebarToggle').click(function() {
                $('#sidebar').toggleClass('sidebar-collapsed');
                $('#mainContent').toggleClass('sidebar-collapsed');
                $(this).find('i').toggleClass('fa-chevron-left fa-chevron-right');
            });

            // Función para mostrar/ocultar loading
            function showLoading() {
                $('#loadingOverlay').removeClass('d-none');
            }

            function hideLoading() {
                $('#loadingOverlay').addClass('d-none');
            }

            // Cargar datos del usuario
            fetch('/api/user-data')
                .then(response => response.json())
                .then(data => {
                    $('#username').text(data.nombre || 'Administrador');
                    $('#userrole').text(data.rol || 'Admin');
                })
                .catch(error => console.error('Error:', error));
            
            // Inicializar DataTable con la estructura correcta de tu API
            table = $('#pacientesTable').DataTable({
                ajax: {
                    url: '/api/pacientes/detallados',
                    data: function(d) {
                        // Agregar filtros personalizados
                        d.estado = currentFilters.estado || '';
                        d.search = currentFilters.search || '';
                        d.fecha_desde = currentFilters.fecha_desde || '';
                        d.fecha_hasta = currentFilters.fecha_hasta || '';
                    },
                    dataSrc: '',
                    error: function(xhr, error, thrown) {
                        hideLoading();
                        showAlert('Error al cargar los datos de pacientes', 'danger');
                    }
                },
                columns: [
                    { 
                        data: 'id_paciente',
                        visible: false
                    },
                    { 
                        data: null,
                        render: function(data, type, row) {
                            const initials = row.nombre_completo ? 
                                row.nombre_completo.split(' ').map(n => n[0]).join('') : '';
                            return `
                                <div class="d-flex justify-content-center">
                                    <div class="patient-avatar d-flex align-items-center justify-content-center bg-primary text-white fw-bold">
                                        ${initials.substring(0, 2)}
                                    </div>
                                </div>
                            `;
                        },
                        orderable: false,
                        width: '60px'
                    },
                    { 
                        data: 'nombre_completo',
                        render: function(data, type, row) {
                            return `<span class="fw-semibold">${data || ''}</span>`;
                        }
                    },
                    { 
                        data: 'cedula',
                        render: function(data) {
                            return data || '<span class="text-muted">No registrada</span>';
                        }
                    },
                    { 
                        data: 'telefono',
                        render: function(data) {
                            return data ? `<a href="tel:${data}" class="text-decoration-none">${data}</a>` : '<span class="text-muted">No registrado</span>';
                        }
                    },
                    { 
                        data: 'correo',
                        render: function(data) {
                            return data ? `<a href="mailto:${data}" class="text-decoration-none">${data}</a>` : '<span class="text-muted">No registrado</span>';
                        }
                    },
                    { 
                        data: 'fecha_nacimiento',
                        render: function(data) {
                            if (!data) return '<span class="text-muted">No registrada</span>';
                            const fecha = new Date(data);
                            return fecha.toLocaleDateString('es-ES');
                        }
                    },
                    { 
                        data: 'estado',
                        render: function(data) {
                            const badgeClass = data === 'A' ? 'badge-active' : 'badge-inactive';
                            const estadoText = data === 'A' ? 'Activo' : 'Inactivo';
                            return `<span class="badge ${badgeClass}">${estadoText}</span>`;
                        }
                    },
                    { 
                        data: 'fecha_creacion',
                        render: function(data) {
                            if (!data) return '<span class="text-muted">No registrada</span>';
                            const fecha = new Date(data);
                            return fecha.toLocaleDateString('es-ES');
                        }
                    },
                    {
                        data: null,
                        render: function(data, type, row) {
                            return `
                                <div class="d-flex justify-content-center">
                                    <button class="btn btn-sm btn-outline-primary action-btn edit-btn" data-id="${row.id_paciente}" title="Editar">
                                        <i class="fas fa-edit"></i>
                                    </button>
                                    <button class="btn btn-sm btn-outline-info action-btn view-btn" data-id="${row.id_paciente}" title="Ver detalles">
                                        <i class="fas fa-eye"></i>
                                    </button>
                                    <button class="btn btn-sm btn-outline-${row.estado === 'A' ? 'danger' : 'success'} action-btn status-btn" data-id="${row.id_paciente}" data-estado="${row.estado}" title="${row.estado === 'A' ? 'Inactivar' : 'Activar'}">
                                        <i class="fas ${row.estado === 'A' ? 'fa-user-slash' : 'fa-user-check'}"></i>
                                    </button>
                                </div>
                            `;
                        },
                        orderable: false,
                        width: '150px'
                    }
                ],
                language: {
                    url: '//cdn.datatables.net/plug-ins/1.13.6/i18n/es-ES.json'
                },
                order: [[2, 'asc']],
                dom: '<"top"Bf>rt<"bottom"lip><"clear">',
                buttons: [
                    {
                        extend: 'excel',
                        text: '<i class="fas fa-file-excel me-1"></i> Excel',
                        className: 'btn btn-success btn-sm',
                        title: 'Listado_de_Pacientes',
                        exportOptions: {
                            columns: [2, 3, 4, 5, 6, 7, 8]
                        }
                    },
                    {
                        extend: 'pdf',
                        text: '<i class="fas fa-file-pdf me-1"></i> PDF',
                        className: 'btn btn-danger btn-sm',
                        title: 'Listado_de_Pacientes',
                        exportOptions: {
                            columns: [2, 3, 4, 5, 6, 7, 8]
                        }
                    },
                    {
                        extend: 'print',
                        text: '<i class="fas fa-print me-1"></i> Imprimir',
                        className: 'btn btn-secondary btn-sm',
                        title: 'Listado_de_Pacientes',
                        exportOptions: {
                            columns: [2, 3, 4, 5, 6, 7, 8]
                        }
                    }
                ],
                initComplete: function() {
                    hideLoading();
                    updateCounters();
                }
            });
            
            // Función para actualizar los contadores
            function updateCounters() {
                fetch('/api/pacientes/stats')
                    .then(response => response.json())
                    .then(data => {
                        $('#countActive').text(data.active || 0);
                        $('#countTotal').text(data.total || 0);
                        $('#countNew').text(data.new_this_month || 0);
                    })
                    .catch(error => {
                        console.error('Error al obtener estadísticas:', error);
                    });
            }
            
            // Función para mostrar alertas
            function showAlert(message, type) {
                const alertId = 'alert-' + Date.now();
                const alert = `
                    <div class="alert alert-${type} alert-dismissible fade show" role="alert" id="${alertId}">
                        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'danger' ? 'exclamation-circle' : 'info-circle'} me-2"></i>
                        ${message}
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                `;
                $('#alertContainer').append(alert);
                
                // Eliminar la alerta después de 5 segundos
                setTimeout(() => {
                    $(`#${alertId}`).alert('close');
                }, 5000);
            }
            
            // Aplicar filtros
            function applyFilters() {
                currentFilters = {
                    estado: $('#filterEstado').val(),
                    search: $('#filterSearch').val(),
                    fecha_desde: $('#filterFechaDesde').val(),
                    fecha_hasta: $('#filterFechaHasta').val()
                };
                
                showLoading();
                table.ajax.reload(function() {
                    hideLoading();
                    updateCounters();
                });
            }

            $('#filterEstado').change(applyFilters);
            $('#filterFechaDesde, #filterFechaHasta').change(applyFilters);
            
            // Búsqueda con debounce
            let searchTimeout;
            $('#filterSearch').keyup(function() {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(applyFilters, 500);
            });
            
            // Limpiar filtros
            $('#btnClearFilters').click(function() {
                $('#filterEstado').val('');
                $('#filterFechaDesde').val('');
                $('#filterFechaHasta').val('');
                $('#filterSearch').val('');
                applyFilters();
            });
            
            // Recargar tabla
            $('#refreshTableBtn').click(function() {
                showLoading();
                table.ajax.reload(function() {
                    hideLoading();
                    updateCounters();
                    showAlert('Datos actualizados correctamente', 'success');
                });
            });
            
            // Mostrar/ocultar inactivos
            $('#showInactive').click(function() {
                const currentFilter = $('#filterEstado').val();
                if (currentFilter === '') {
                    $('#filterEstado').val('A').trigger('change');
                    $(this).html('<i class="fas fa-eye-slash me-2"></i>Mostrar inactivos');
                } else {
                    $('#filterEstado').val('').trigger('change');
                    $(this).html('<i class="fas fa-eye me-2"></i>Ocultar inactivos');
                }
            });
            
            // Modal para nuevo paciente
            const pacienteModal = new bootstrap.Modal('#pacienteModal');
            const pacienteForm = document.getElementById('pacienteForm');
            
            $('#nuevoPacienteBtn').click(function() {
                $('#modalTitle').html('<i class="fas fa-user-plus me-2"></i>Nuevo Paciente');
                pacienteForm.reset();
                pacienteForm.classList.remove('was-validated');
                $('#id_paciente').val('');
                pacienteModal.show();
            });
            
            // Validación del formulario
            pacienteForm.addEventListener('submit', function(event) {
                event.preventDefault();
                event.stopPropagation();
                
                if (pacienteForm.checkValidity()) {
                    submitPacienteForm();
                }
                
                pacienteForm.classList.add('was-validated');
            }, false);
            
            // Enviar formulario de paciente
            function submitPacienteForm() {
                const formData = {
                    nombre_completo: $('#nombre_completo').val(),
                    cedula: $('#cedula').val(),
                    fecha_nacimiento: $('#fecha_nacimiento').val() || null,
                    genero: $('#genero').val() || null,
                    telefono: $('#telefono').val() || null,
                    correo: $('#correo').val() || null,
                    direccion: $('#direccion').val() || null,
                    estado: $('#estado').val(),
                    tipo_sangre: $('#tipo_sangre').val() || null,
                    observaciones: $('#observaciones').val() || null
                };
                
                const id = $('#id_paciente').val();
                const method = id ? 'PUT' : 'POST';
                const url = id ? `/api/pacientes/${id}` : '/api/pacientes';
                
                // Deshabilitar botón para evitar múltiples envíos
                $('#submitBtn').prop('disabled', true).html('<i class="fas fa-spinner fa-spin me-1"></i> Guardando...');
                
                fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formData)
                })
                .then(response => {
                    if (!response.ok) {
                        return response.json().then(err => { throw err; });
                    }
                    return response.json();
                })
                .then(data => {
                    table.ajax.reload(null, false);
                    pacienteModal.hide();
                    showAlert(id ? 'Paciente actualizado exitosamente' : 'Paciente creado exitosamente', 'success');
                    updateCounters();
                })
                .catch(error => {
                    console.error('Error:', error);
                    showAlert(error.error || 'Error al guardar el paciente', 'danger');
                })
                .finally(() => {
                    $('#submitBtn').prop('disabled', false).html('<i class="fas fa-save me-1"></i> Guardar');
                });
            }
            
            // Editar paciente
            $('#pacientesTable').on('click', '.edit-btn', function() {
                const id = $(this).data('id');
                
                showLoading();
                fetch(`/api/pacientes/${id}`)
                    .then(response => {
                        if (!response.ok) throw new Error('Error al obtener paciente');
                        return response.json();
                    })
                    .then(paciente => {
                        hideLoading();
                        $('#modalTitle').html('<i class="fas fa-user-edit me-2"></i>Editar Paciente');
                        $('#id_paciente').val(paciente.id_paciente);
                        $('#nombre_completo').val(paciente.nombre_completo || '');
                        $('#cedula').val(paciente.cedula || '');
                        $('#fecha_nacimiento').val(paciente.fecha_nacimiento || '');
                        $('#genero').val(paciente.genero || '');
                        $('#telefono').val(paciente.telefono || '');
                        $('#correo').val(paciente.correo || '');
                        $('#direccion').val(paciente.direccion || '');
                        $('#estado').val(paciente.estado);
                        $('#tipo_sangre').val(paciente.tipo_sangre || '');
                        $('#observaciones').val(paciente.observaciones || '');
                        
                        pacienteForm.classList.remove('was-validated');
                        pacienteModal.show();
                    })
                    .catch(error => {
                        hideLoading();
                        console.error('Error:', error);
                        showAlert('Error al cargar los datos del paciente', 'danger');
                    });
            });

            // Ver detalles del paciente
            $('#pacientesTable').on('click', '.view-btn', function() {
                const id = $(this).data('id');
                // Aquí puedes implementar un modal de vista detallada o redirigir a otra página
                showAlert('Funcionalidad de vista detallada en desarrollo', 'info');
            });
            
            // Modal de confirmación
            const confirmModal = new bootstrap.Modal('#confirmModal');
            let currentAction = null;
            let currentId = null;
            
            // Cambiar estado del paciente
            $('#pacientesTable').on('click', '.status-btn', function() {
                const id = $(this).data('id');
                const currentEstado = $(this).data('estado');
                const isActive = currentEstado === 'A';
                
                currentId = id;
                currentAction = isActive ? 'inactivate' : 'activate';
                
                $('#confirmModalTitle').html(`<i class="fas fa-exclamation-triangle me-2"></i>${isActive ? 'Inactivar Paciente' : 'Activar Paciente'}`);
                $('#confirmModalBody').html(`
                    <p>¿Está seguro que desea ${isActive ? 'inactivar' : 'activar'} este paciente?</p>
                    ${isActive ? '<p class="text-warning"><i class="fas fa-exclamation-triangle me-2"></i>El paciente no podrá agendar nuevas citas mientras esté inactivo.</p>' : ''}
                `);
                $('#confirmActionBtn').removeClass('btn-warning btn-success').addClass(isActive ? 'btn-warning' : 'btn-success').text(isActive ? 'Inactivar' : 'Activar');
                
                confirmModal.show();
            });
            
            // Confirmar acción
            $('#confirmActionBtn').click(function() {
                const url = `/api/pacientes/${currentId}/status`;
                const newStatus = currentAction === 'inactivate' ? 'I' : 'A';
                
                showLoading();
                fetch(url, {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ estado: newStatus })
                })
                .then(response => {
                    if (!response.ok) {
                        return response.json().then(err => { throw err; });
                    }
                    return response.json();
                })
                .then(data => {
                    hideLoading();
                    table.ajax.reload(null, false);
                    confirmModal.hide();
                    showAlert(data.message || 'Estado del paciente actualizado', 'success');
                    updateCounters();
                })
                .catch(error => {
                    hideLoading();
                    console.error('Error:', error);
                    showAlert(error.error || 'Error al actualizar estado', 'danger');
                });
            });
            
            // Validar cédula única al cambiar
            $('#cedula').on('blur', function() {
                const cedula = $(this).val();
                const id = $('#id_paciente').val();
                
                if (!cedula) return;
                
                const params = new URLSearchParams({ cedula });
                if (id) params.append('exclude', id);
                
                fetch(`/api/pacientes/check-cedula?${params}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.exists) {
                            $(this).addClass('is-invalid');
                            $(this).next('.invalid-feedback').text('Esta cédula ya está registrada');
                        } else {
                            $(this).removeClass('is-invalid');
                        }
                    })
                    .catch(error => {
                        console.error('Error al verificar cédula:', error);
                    });
            });
            
            // Validación de email
            $('#correo').on('blur', function() {
                const email = $(this).val();
                if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
                    $(this).addClass('is-invalid');
                } else {
                    $(this).removeClass('is-invalid');
                }
            });

            // Validación de teléfono
            $('#telefono').on('blur', function() {
                const telefono = $(this).val();
                if (telefono && !/^\+?[\d\s\-\(\)]{7,15}$/.test(telefono)) {
                    $(this).addClass('is-invalid');
                } else {
                    $(this).removeClass('is-invalid');
                }
            });

            // Inicializar Select2 para los selects
            $('.form-select').select2({
                dropdownParent: $('#pacienteModal'),
                width: '100%',
                theme: 'bootstrap-5'
            });

            // Cargar datos iniciales
            showLoading();
        });