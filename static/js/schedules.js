        document.addEventListener('DOMContentLoaded', function() {
            // Variables globales
            let currentDoctorId = null;
            const apiBaseUrl = '/api';
            
            // Elementos del DOM
            const doctorSelect = document.getElementById('doctorSelect');
            const weeklySchedule = document.getElementById('weeklySchedule');
            const scheduleList = document.getElementById('scheduleList');
            const availableSlots = document.getElementById('availableSlots');
            const addScheduleForm = document.getElementById('addScheduleForm');
            const checkSlotsBtn = document.getElementById('checkSlots');
            
            // Inicializar toasts
            const successToast = new bootstrap.Toast(document.getElementById('successToast'));
            const errorToast = new bootstrap.Toast(document.getElementById('errorToast'));
            
            // Función para obtener nombre del día
            function getDayName(dayNumber) {
                const days = {
                    1: 'Lunes',
                    2: 'Martes',
                    3: 'Miércoles',
                    4: 'Jueves',
                    5: 'Viernes',
                    6: 'Sábado',
                    7: 'Domingo'
                };
                return days[dayNumber] || 'Desconocido';
            }
            
            // Mostrar notificación
            function showNotification(message, isSuccess = true) {
                if (isSuccess) {
                    document.getElementById('successMessage').textContent = message;
                    successToast.show();
                } else {
                    document.getElementById('errorMessage').textContent = message;
                    errorToast.show();
                }
            }
            
            // Cargar lista de médicos
            function loadDoctors() {
                fetch(`${apiBaseUrl}/medicos`)
                    .then(response => response.json())
                    .then(data => {
                        doctorSelect.innerHTML = '<option value="">-- Seleccione un médico --</option>';
                        data.forEach(doctor => {
                            const option = document.createElement('option');
                            option.value = doctor.id_medico;
                            option.textContent = `${doctor.nombre_completo} - ${doctor.especialidad}`;
                            doctorSelect.appendChild(option);
                        });
                    })
                    .catch(error => {
                        console.error('Error al cargar médicos:', error);
                        showNotification('Error al cargar la lista de médicos', false);
                    });
            }
            
            // Cargar horarios del médico seleccionado
            doctorSelect.addEventListener('change', function() {
                currentDoctorId = this.value;
                if (currentDoctorId) {
                    loadWeeklySchedule(currentDoctorId);
                    loadScheduleList(currentDoctorId);
                } else {
                    weeklySchedule.innerHTML = '<div class="col-12 no-schedules">Seleccione un médico para ver sus horarios</div>';
                    scheduleList.innerHTML = '';
                    availableSlots.innerHTML = '';
                    document.getElementById('noSlotsMessage').style.display = 'block';
                }
            });
            
            // Cargar vista semanal
            function loadWeeklySchedule(doctorId) {
                const weeklyContainer = document.getElementById('weeklySchedule');
                const loadingElement = document.getElementById('weeklyLoading');
                
                weeklyContainer.innerHTML = '';
                loadingElement.style.display = 'block';
                
                fetch(`${apiBaseUrl}/horarios/${doctorId}/semanal`)
                    .then(response => response.json())
                    .then(data => {
                        loadingElement.style.display = 'none';
                        
                        if (Object.keys(data).length === 0) {
                            weeklyContainer.innerHTML = '<div class="col-12 no-schedules">No hay horarios registrados para este médico</div>';
                            return;
                        }
                        
                        for (let day = 1; day <= 7; day++) {
                            const dayName = getDayName(day);
                            const daySchedules = data[day] || [];
                            
                            const dayCol = document.createElement('div');
                            dayCol.className = 'col-md-6 col-lg-4 col-xl-3 mb-4';
                            
                            const dayCard = document.createElement('div');
                            dayCard.className = 'card day-card h-100';
                            
                            const cardHeader = document.createElement('div');
                            cardHeader.className = 'card-header day-header';
                            cardHeader.innerHTML = `<i class="bi bi-calendar-day me-2"></i>${dayName}`;
                            
                            const cardBody = document.createElement('div');
                            cardBody.className = 'card-body';
                            
                            if (daySchedules.length === 0) {
                                const noSchedule = document.createElement('div');
                                noSchedule.className = 'no-schedules';
                                noSchedule.textContent = 'Sin horarios este día';
                                cardBody.appendChild(noSchedule);
                            } else {
                                daySchedules.forEach(schedule => {
                                    const timeSlot = document.createElement('div');
                                    timeSlot.className = 'time-slot';
                                    
                                    const timeText = document.createElement('span');
                                    timeText.className = 'time';
                                    timeText.innerHTML = `<i class="bi bi-clock me-1"></i>${schedule.hora_inicio} - ${schedule.hora_fin}`;
                                    
                                    const actions = document.createElement('div');
                                    actions.className = 'btn-group';
                                    
                                    const editBtn = document.createElement('button');
                                    editBtn.className = 'btn btn-sm btn-outline-primary';
                                    editBtn.innerHTML = '<i class="bi bi-pencil"></i>';
                                    editBtn.title = 'Editar';
                                    editBtn.onclick = () => openEditModal(schedule.id_horario, schedule);
                                    
                                    const deleteBtn = document.createElement('button');
                                    deleteBtn.className = 'btn btn-sm btn-outline-danger';
                                    deleteBtn.innerHTML = '<i class="bi bi-trash"></i>';
                                    deleteBtn.title = 'Eliminar';
                                    deleteBtn.onclick = () => deleteSchedule(schedule.id_horario);
                                    
                                    actions.appendChild(editBtn);
                                    actions.appendChild(deleteBtn);
                                    
                                    timeSlot.appendChild(timeText);
                                    timeSlot.appendChild(actions);
                                    
                                    cardBody.appendChild(timeSlot);
                                });
                            }
                            
                            dayCard.appendChild(cardHeader);
                            dayCard.appendChild(cardBody);
                            dayCol.appendChild(dayCard);
                            weeklyContainer.appendChild(dayCol);
                        }
                    })
                    .catch(error => {
                        loadingElement.style.display = 'none';
                        console.error('Error al cargar horario semanal:', error);
                        showNotification('Error al cargar horario semanal', false);
                    });
            }
            
            // Cargar lista completa de horarios
            function loadScheduleList(doctorId) {
                const listContainer = document.getElementById('scheduleList');
                const loadingElement = document.getElementById('listLoading');
                
                listContainer.innerHTML = '';
                loadingElement.style.display = 'block';
                
                fetch(`${apiBaseUrl}/horarios/${doctorId}`)
                    .then(response => response.json())
                    .then(data => {
                        loadingElement.style.display = 'none';
                        
                        if (data.length === 0) {
                            listContainer.innerHTML = '<tr><td colspan="5" class="text-center no-schedules">No hay horarios registrados</td></tr>';
                            return;
                        }
                        
                        data.forEach(schedule => {
                            const row = document.createElement('tr');
                            
                            const idCell = document.createElement('td');
                            idCell.textContent = schedule.id_horario;
                            idCell.className = 'fw-bold';
                            
                            const dayCell = document.createElement('td');
                            dayCell.textContent = getDayName(schedule.dia_semana);
                            
                            const startCell = document.createElement('td');
                            startCell.innerHTML = `<i class="bi bi-clock me-1"></i>${schedule.hora_inicio}`;
                            
                            const endCell = document.createElement('td');
                            endCell.innerHTML = `<i class="bi bi-clock me-1"></i>${schedule.hora_fin}`;
                            
                            const actionsCell = document.createElement('td');
                            actionsCell.className = 'text-end';
                            
                            const btnGroup = document.createElement('div');
                            btnGroup.className = 'btn-group';
                            
                            const editBtn = document.createElement('button');
                            editBtn.className = 'btn btn-sm btn-outline-primary me-1';
                            editBtn.innerHTML = '<i class="bi bi-pencil"></i> Editar';
                            editBtn.onclick = () => openEditModal(schedule.id_horario, schedule);
                            
                            const deleteBtn = document.createElement('button');
                            deleteBtn.className = 'btn btn-sm btn-outline-danger';
                            deleteBtn.innerHTML = '<i class="bi bi-trash"></i>';
                            deleteBtn.onclick = () => deleteSchedule(schedule.id_horario);
                            
                            btnGroup.appendChild(editBtn);
                            btnGroup.appendChild(deleteBtn);
                            actionsCell.appendChild(btnGroup);
                            
                            row.appendChild(idCell);
                            row.appendChild(dayCell);
                            row.appendChild(startCell);
                            row.appendChild(endCell);
                            row.appendChild(actionsCell);
                            
                            listContainer.appendChild(row);
                        });
                    })
                    .catch(error => {
                        loadingElement.style.display = 'none';
                        console.error('Error al cargar lista de horarios:', error);
                        showNotification('Error al cargar lista de horarios', false);
                    });
            }
            
            // Ver disponibilidad
            checkSlotsBtn.addEventListener('click', function() {
                if (!currentDoctorId) {
                    showNotification('Por favor seleccione un médico primero', false);
                    return;
                }
                
                const day = document.getElementById('slotDay').value;
                const duration = document.getElementById('slotDuration').value;
                const slotsContainer = document.getElementById('availableSlots');
                const noSlotsMessage = document.getElementById('noSlotsMessage');
                const loadingElement = document.getElementById('slotsLoading');
                
                slotsContainer.innerHTML = '';
                noSlotsMessage.style.display = 'none';
                loadingElement.style.display = 'block';
                
                fetch(`${apiBaseUrl}/horarios/${currentDoctorId}/slots?dia_semana=${day}&duracion=${duration}`)
                    .then(response => response.json())
                    .then(data => {
                        loadingElement.style.display = 'none';
                        
                        if (data.error) {
                            noSlotsMessage.textContent = data.error;
                            noSlotsMessage.style.display = 'block';
                            return;
                        }
                        
                        if (data.slots_disponibles && data.slots_disponibles.length === 0) {
                            noSlotsMessage.textContent = 'No hay horarios disponibles para este día';
                            noSlotsMessage.style.display = 'block';
                            return;
                        }
                        
                        const slots = data.slots_disponibles || data;
                        slots.forEach(slot => {
                            const slotBadge = document.createElement('span');
                            slotBadge.className = 'slot-badge';
                            const slotTime = slot.hora || slot;
                            slotBadge.innerHTML = `<i class="bi bi-clock me-1"></i>${slotTime}`;
                            slotsContainer.appendChild(slotBadge);
                        });
                    })
                    .catch(error => {
                        loadingElement.style.display = 'none';
                        console.error('Error al cargar slots disponibles:', error);
                        showNotification('Error al cargar slots disponibles', false);
                    });
            });
            
            // Agregar nuevo horario
            addScheduleForm.addEventListener('submit', function(e) {
                e.preventDefault();
                
                if (!currentDoctorId) {
                    showNotification('Por favor seleccione un médico primero', false);
                    return;
                }
                
                const day = document.getElementById('addDay').value;
                const startTime = document.getElementById('startTime').value;
                const endTime = document.getElementById('endTime').value;
                
                if (!day || !startTime || !endTime) {
                    showNotification('Por favor complete todos los campos', false);
                    return;
                }
                
                if (startTime >= endTime) {
                    showNotification('La hora de inicio debe ser anterior a la hora de fin', false);
                    return;
                }
                
                const scheduleData = {
                    id_medico: parseInt(currentDoctorId),
                    dia_semana: parseInt(day),
                    hora_inicio: startTime,
                    hora_fin: endTime
                };
                
                fetch(`${apiBaseUrl}/horarios`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(scheduleData)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        showNotification(data.error, false);
                        return;
                    }
                    
                    showNotification('Horario agregado exitosamente');
                    addScheduleForm.reset();
                    
                    // Recargar las vistas
                    loadWeeklySchedule(currentDoctorId);
                    loadScheduleList(currentDoctorId);
                    
                    // Cambiar a la pestaña de lista
                    const listTab = new bootstrap.Tab(document.getElementById('list-tab'));
                    listTab.show();
                })
                .catch(error => {
                    console.error('Error al agregar horario:', error);
                    showNotification('Error al agregar horario', false);
                });
            });
            
            // Abrir modal de edición
            function openEditModal(scheduleId, scheduleData) {
                const editModalElement = document.getElementById('editModal');
                const modal = new bootstrap.Modal(editModalElement);
                
                document.getElementById('editId').value = scheduleId;
                document.getElementById('editDay').value = scheduleData.dia_semana || scheduleData.dia_semana_num;
                document.getElementById('editStartTime').value = scheduleData.hora_inicio;
                document.getElementById('editEndTime').value = scheduleData.hora_fin;
                
                modal.show();
            }
            
            // Guardar cambios del modal
            document.getElementById('saveChanges').addEventListener('click', function() {
                const scheduleId = document.getElementById('editId').value;
                const day = document.getElementById('editDay').value;
                const startTime = document.getElementById('editStartTime').value;
                const endTime = document.getElementById('editEndTime').value;
                
                if (!day || !startTime || !endTime) {
                    showNotification('Por favor complete todos los campos', false);
                    return;
                }
                
                if (startTime >= endTime) {
                    showNotification('La hora de inicio debe ser anterior a la hora de fin', false);
                    return;
                }
                
                const scheduleData = {
                    dia_semana: parseInt(day),
                    hora_inicio: startTime,
                    hora_fin: endTime
                };
                
                fetch(`${apiBaseUrl}/horarios/${scheduleId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(scheduleData)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        showNotification(data.error, false);
                        return;
                    }
                    
                    showNotification('Horario actualizado exitosamente');
                    
                    // Cerrar modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('editModal'));
                    modal.hide();
                    
                    // Recargar las vistas
                    loadWeeklySchedule(currentDoctorId);
                    loadScheduleList(currentDoctorId);
                })
                .catch(error => {
                    console.error('Error al actualizar horario:', error);
                    showNotification('Error al actualizar horario', false);
                });
            });
            
            // Eliminar horario
            function deleteSchedule(scheduleId) {
                if (!confirm('¿Está seguro de que desea eliminar este horario?')) {
                    return;
                }
                
                fetch(`${apiBaseUrl}/horarios/${scheduleId}`, {
                    method: 'DELETE'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        showNotification(data.error, false);
                        return;
                    }
                    
                    showNotification('Horario eliminado exitosamente');
                    
                    // Recargar las vistas
                    loadWeeklySchedule(currentDoctorId);
                    loadScheduleList(currentDoctorId);
                })
                .catch(error => {
                    console.error('Error al eliminar horario:', error);
                    showNotification('Error al eliminar horario', false);
                });
            }
            
            // Inicializar la aplicación
            loadDoctors();
        });