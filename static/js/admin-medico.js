$(document).ready(function() {
            // 1. Cargar datos del usuario
            const loadUserData = () => {
                fetch('/api/user-data')
                    .then(response => {
                        if (!response.ok) throw new Error('Error al cargar datos de usuario');
                        return response.json();
                    })
                    .then(data => {
                        $('#username').text(data.nombre || 'Administrador');
                        $('#userrole').text(data.rol || 'Admin');
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        showAlert('Error al cargar datos de usuario', 'danger');
                    });
            };

            // 2. Inicializar DataTable con configuración mejorada
            const initializeDataTable = () => {
                const table = $('#medicosTable').DataTable({
                    ajax: {
                        url: '/api/medicos',
                        dataSrc: '',
                        error: (xhr, error, thrown) => {
                            console.error('Error al cargar datos:', error);
                            showAlert('Error al cargar la lista de médicos', 'danger');
                        }
                    },
                    columns: [
                        { data: 'id_medico', className: 'fw-bold' },
                        { 
                            data: 'nombre_completo',
                            render: function(data, type, row) {
                                return `<span class="fw-semibold">${data}</span>`;
                            }
                        },
                        { data: 'especialidad' },
                        { 
                            data: 'telefono',
                            render: data => data ? `<a href="tel:${data}">${data}</a>` : '<span class="text-muted">No registrado</span>'
                        },
                        { 
                            data: 'correo',
                            render: data => data ? `<a href="mailto:${data}">${data}</a>` : '<span class="text-muted">No registrado</span>'
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
                            data: 'id_medico',
                            render: function(data, type, row) {
                                return `
                                    <div class="btn-group" role="group">
                                        <button class="btn btn-sm btn-outline-primary action-btn edit-btn" data-id="${data}" title="Editar">
                                            <i class="fas fa-edit"></i>
                                        </button>
                                        <button class="btn btn-sm btn-outline-success action-btn schedule-btn" data-id="${data}" title="horarios.html">
                                            <i class="fas fa-calendar-alt"></i>
                                            <span class="tooltip-text">Gestionar horario</span>
                                        </button>
                                        <button class="btn btn-sm btn-outline-danger action-btn delete-btn" data-id="${data}" title="${row.estado === 'A' ? 'Desactivar' : 'Activar'}">
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
                        url: '//cdn.datatables.net/plug-ins/1.11.5/i18n/es-ES.json'
                    },
                    responsive: true,
                    order: [[1, 'asc']],
                    dom: '<"top"<"row"<"col-md-6"l><"col-md-6"f>>>rt<"bottom"<"row"<"col-md-6"i><"col-md-6"p>>>',
                    initComplete: function() {
                        $('.dataTables_filter input').addClass('form-control');
                        $('.dataTables_length select').addClass('form-select');
                    },
                    drawCallback: function() {
                        const api = this.api();
                        $('#totalMedicos').text(`${api.rows().count()} médicos`);
                    }
                });

                return table;
            };

            // 3. Configurar filtros para DataTable
            const setupFilters = (table) => {
                $('#filterEspecialidad').change(function() {
                    table.column(2).search(this.value).draw();
                });

                $('#filterEstado').change(function() {
                    table.column(5).search(this.value).draw();
                });

                $('#filterSearch').keyup(function() {
                    table.search(this.value).draw();
                });

                $('#btnClearFilters').click(function() {
                    $('#filterEspecialidad, #filterEstado').val('');
                    $('#filterSearch').val('');
                    table.search('').columns().search('').draw();
                });
            };

            // 4. Manejo del modal y formulario de médico
            const setupMedicoModal = (table) => {
                const medicoModal = new bootstrap.Modal('#medicoModal');
                const medicoForm = $('#medicoForm');
                
                // Inicializar Select2 para especialidades dentro del modal
                $('.js-specialties-select').select2({
                    placeholder: "Seleccionar especialidad...",
                    allowClear: true,
                    width: '100%',
                    dropdownParent: $('#medicoModal')
                });

                // Validación del formulario
                medicoForm.on('submit', function(e) {
                    e.preventDefault();
                    
                    if (!this.checkValidity()) {
                        e.stopPropagation();
                        $(this).addClass('was-validated');
                        return;
                    }
                    
                    const id = $('#id_medico').val();
                    const formData = {
                        nombre_completo: $('#nombre_completo').val().trim(),
                        especialidad: $('#especialidad').val(),
                        telefono: $('#telefono').val().trim(),
                        correo: $('#correo').val().trim(),
                        estado: $('#estado').val()
                    };

                    const method = id ? 'PUT' : 'POST';
                    const url = id ? `/api/medicos/${id}` : '/api/medicos';
                    
                    // Mostrar spinner de carga
                    $('#saveSpinner').removeClass('d-none');
                    $('#saveText').text('Guardando...');
                    
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
                        medicoModal.hide();
                        showAlert(`Médico ${id ? 'actualizado' : 'creado'} exitosamente`, 'success');
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        showAlert(error.error || 'Error al guardar el médico', 'danger');
                    })
                    .finally(() => {
                        $('#saveSpinner').addClass('d-none');
                        $('#saveText').text('Guardar');
                    });
                });

                // Nuevo médico
                $('#nuevoMedicoBtn').click(function() {
                    medicoForm.removeClass('was-validated')[0].reset();
                    $('#modalTitle').text('Nuevo Médico');
                    $('#id_medico').val('');
                    $('#especialidad').val('').trigger('change');
                    medicoModal.show();
                });

                // Editar médico
                $('#medicosTable').on('click', '.edit-btn', function() {
                    const id = $(this).data('id');
                    fetch(`/api/medicos/${id}`)
                        .then(response => {
                            if (!response.ok) throw new Error('Médico no encontrado');
                            return response.json();
                        })
                        .then(medico => {
                            medicoForm.removeClass('was-validated')[0].reset();
                            $('#modalTitle').text('Editar Médico');
                            $('#id_medico').val(medico.id_medico);
                            $('#nombre_completo').val(medico.nombre_completo);
                            $('#especialidad').val(medico.especialidad).trigger('change');
                            $('#telefono').val(medico.telefono);
                            $('#correo').val(medico.correo);
                            $('#estado').val(medico.estado);
                            medicoModal.show();
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            showAlert(error.message || 'Error al cargar datos del médico', 'danger');
                        });
                });

                // Cerrar modal al hacer clic en Cancelar
                $('.btn-secondary').click(function() {
                    medicoModal.hide();
                });
            };

            // 5. Manejo de acciones (eliminar, horario)
            const setupActions = (table) => {
                // Eliminar/Activar médico
                $('#medicosTable').on('click', '.delete-btn', function(e) {
                    e.stopPropagation();
                    const id = $(this).data('id');
                    const row = table.row($(this).closest('tr'));
                    const medico = row.data();
                    const action = medico.estado === 'A' ? 'desactivar' : 'activar';
                    
                    if (confirm(`¿Está seguro que desea ${action} este médico?`)) {
                        fetch(`/api/medicos/${id}`, {
                            method: 'DELETE'
                        })
                        .then(response => {
                            if (!response.ok) throw new Error('Error al cambiar estado');
                            return response.json();
                        })
                        .then(data => {
                            table.ajax.reload(null, false);
                            showAlert(data.message || `Médico ${action}do correctamente`, 'success');
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            showAlert(error.message || 'Error al cambiar estado del médico', 'danger');
                        });
                    }
                });

                // Redirigir a horarios
                 $(document).on('click', '.schedule-btn', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const id = $(this).data('id');
        if (!id) {
            console.error('No se encontró ID en el botón de horarios');
            showAlert('Error al identificar el médico', 'danger');
            return;
        }
        
        console.log('Redirigiendo a horarios.html con ID:', id);
        window.location.href = `horarios.html?id=${encodeURIComponent(id)}`;
    });

                // Seleccionar fila
                $('#medicosTable').on('click', 'tbody tr', function(e) {
                    if (!$(e.target).is('button, a, input, select, textarea')) {
                        const id = table.row(this).data().id_medico;
                        $('.edit-btn[data-id="'+id+'"]').click();
                    }
                });
            };

            // 6. Mostrar notificaciones
            const showAlert = (message, type) => {
                const alertId = 'alert-' + Date.now();
                const alert = $(`
                    <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3" role="alert" style="z-index: 9999;">
                        <div class="d-flex align-items-center">
                            <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'danger' ? 'fa-exclamation-circle' : 'fa-info-circle'} me-2"></i>
                            <div>${message}</div>
                        </div>
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                `);
                
                $('body').append(alert);
                setTimeout(() => $(`#${alertId}`).alert('close'), 5000);
            };

            // 7. Configurar exportación
            const setupExport = (table) => {
                $('#exportExcel').click(function(e) {
                    e.preventDefault();
                    table.button('.buttons-excel').trigger();
                });

                $('#exportPDF').click(function(e) {
                    e.preventDefault();
                    // Aquí iría la lógica para exportar a PDF
                    showAlert('Exportación a PDF no implementada aún', 'info');
                });
            };

            // Inicialización
            loadUserData();
            const table = initializeDataTable();
            setupFilters(table);
            setupMedicoModal(table);
            setupActions(table);
            setupExport(table);
        });