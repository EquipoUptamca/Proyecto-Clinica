document.addEventListener('DOMContentLoaded', function() {
            // Cargar datos del usuario
            fetch('/api/user-data')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('username').textContent = data.nombre;
                    document.getElementById('userrole').textContent = data.rol;
                });
            
            // Cargar estadísticas
            fetch('/api/admin/stats')
                .then(response => response.json())
                .then(stats => {
                    const statsContainer = document.getElementById('stats-container');
                    const statsData = [
                        { 
                            icon: 'user-md', 
                            count: stats.doctors, 
                            label: 'Médicos',
                            link: '/medicos',
                            color: 'primary'
                        },
                        { 
                            icon: 'procedures', 
                            count: stats.patients, 
                            label: 'Pacientes',
                            link: '/pacientes',
                            color: 'success'
                        },
                        { 
                            icon: 'calendar-check', 
                            count: stats.appointments, 
                            label: 'Citas Hoy',
                            link: '/citas',
                            color: 'info'
                        },
                        { 
                            icon: 'users', 
                            count: stats.users, 
                            label: 'Usuarios',
                            link: '/users',
                            color: 'warning'
                        }
                    ];
                    
                    statsContainer.innerHTML = '';
                    statsData.forEach(stat => {
                        statsContainer.innerHTML += `
                            <div class="col-md-3">
                                <a href="${stat.link}" class="text-decoration-none">
                                    <div class="card stat-card">
                                        <i class="fas fa-${stat.icon} fa-2x mb-2 text-${stat.color}"></i>
                                        <h3 class="count">${stat.count}</h3>
                                        <p class="label">${stat.label}</p>
                                    </div>
                                </a>
                            </div>
                        `;
                    });
                });
            
            // Cargar actividad reciente
            fetch('/api/admin/recent-activity')
                .then(response => response.json())
                .then(activity => {
                    const tableBody = document.querySelector('#recent-records tbody');
                    tableBody.innerHTML = '';
                    
                    activity.forEach(item => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${item.id}</td>
                            <td>${item.type}</td>
                            <td>${item.name}</td>
                            <td>${item.date}</td>
                            <td><span class="badge bg-${item.status === 'completed' ? 'success' : 'warning'}">${item.status === 'completed' ? 'Completado' : 'Pendiente'}</span></td>
                        `;
                        tableBody.appendChild(row);
                    });
                });
            
            // Manejo de botones de acción rápida
            
            document.getElementById('nuevoPacienteBtn').addEventListener('click', function() {
                window.location.href = '/pacientes';
            });
            
            document.getElementById('nuevaCitaBtn').addEventListener('click', function() {
                window.location.href = '/nueva_cita';
            });
            
            document.getElementById('nuevoUsuarioBtn').addEventListener('click', function() {
                window.location.href = '/nuevo_usuario';
            });
            
            // Toggle sidebar en móviles
            document.querySelector('.navbar-toggler').addEventListener('click', function() {
                document.querySelector('.sidebar').classList.toggle('active');
            });
        });