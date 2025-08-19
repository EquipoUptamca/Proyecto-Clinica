document.addEventListener('DOMContentLoaded', function() {
    const registerForm = document.getElementById('registerForm');
    const messageDiv = document.getElementById('message');
    const passwordInput = document.getElementById('contraseña');
    const confirmInput = document.getElementById('confirm_password');
    const togglePassword = document.getElementById('togglePassword');
    const toggleConfirmPassword = document.getElementById('toggleConfirmPassword');
    const passwordStrength = document.getElementById('passwordStrength');
    const roleSelect = document.getElementById('id_rol');
    const roleDescription = document.getElementById('roleDescription');
    const cedulaInput = document.getElementById('cedula');
    const telefonoInput = document.getElementById('telefono');
    const gmailInput = document.getElementById('gmail');
    const btnText = document.getElementById('btn-text');
    
    // Descripciones de roles
    const roleDescriptions = {
        '1': 'Acceso completo al sistema con capacidades de administración y configuración del sistema.',
        '2': 'Acceso completo a historiales médicos, programación de citas y registros clínicos de pacientes.',
        '3': 'Acceso especializado según área médica con capacidades extendidas para especialistas.',
        '4': 'Acceso a registros de pacientes, administración de medicamentos y funciones de enfermería.',
        '5': 'Acceso a programación de citas, registro de pacientes y funciones administrativas básicas.'
    };
    
    // Mostrar/ocultar contraseña
    [togglePassword, toggleConfirmPassword].forEach(toggle => {
        toggle.addEventListener('click', function() {
            const input = this.id === 'togglePassword' ? passwordInput : confirmInput;
            const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
            input.setAttribute('type', type);
            this.innerHTML = type === 'password' ? '<i class="fas fa-eye"></i> Mostrar' : '<i class="fas fa-eye-slash"></i> Ocultar';
        });
    });
    
    // Validar fortaleza de contraseña
    passwordInput.addEventListener('input', function() {
        const password = this.value;
        let strength = 0;
        
        // Longitud mínima
        if (password.length >= 8) strength += 1;
        
        // Contiene mayúsculas
        if (/[A-Z]/.test(password)) strength += 1;
        
        // Contiene números
        if (/[0-9]/.test(password)) strength += 1;
        
        // Contiene caracteres especiales
        if (/[^A-Za-z0-9]/.test(password)) strength += 1;
        
        // Actualizar indicador visual
        passwordStrength.className = 'strength-meter';
        if (password.length === 0) {
            passwordStrength.style.width = '0';
        } else if (strength <= 1) {
            passwordStrength.classList.add('weak');
        } else if (strength <= 3) {
            passwordStrength.classList.add('medium');
        } else {
            passwordStrength.classList.add('strong');
        }
    });
    
    // Mostrar descripción del rol
    roleSelect.addEventListener('change', function() {
        const selectedRole = this.value;
        if (selectedRole && roleDescriptions[selectedRole]) {
            roleDescription.textContent = roleDescriptions[selectedRole];
            roleDescription.style.display = 'block';
        } else {
            roleDescription.style.display = 'none';
        }
    });

    // Validar formato de cédula en tiempo real
    cedulaInput.addEventListener('input', function() {
        this.value = this.value.replace(/\D/g, '').slice(0, 8);
        clearError('cedula_error');
    });

    // Validar formato de teléfono en tiempo real
    telefonoInput.addEventListener('input', function() {
        this.value = this.value.replace(/\D/g, '').slice(0, 12);
        clearError('telefono_error');
    });
    
    // Validación en tiempo real
    registerForm.addEventListener('input', function(e) {
        const target = e.target;
        clearError(target.id + '_error');
        
        if (target.id === 'confirm_password') {
            validatePasswordMatch();
        }
    });
    
    // Manejar el envío del formulario
    registerForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Validación del cliente
        if (validateForm()) {
            await submitForm();
        }
    });
    
    function validateForm() {
        let isValid = true;
        
        // Validar nombre
        const nombre = document.getElementById('nombre_completo');
        if (!nombre.value || nombre.value.length < 5) {
            showError('nombre_error', 'El nombre completo debe tener al menos 5 caracteres');
            isValid = false;
        }
        
        // Validar usuario
        const usuario = document.getElementById('usuario_login');
        if (!usuario.value || usuario.value.length < 4) {
            showError('usuario_error', 'El nombre de usuario debe tener al menos 4 caracteres');
            isValid = false;
        }

        // Validar cédula
        const cedula = document.getElementById('cedula');
        if (!cedula.value || cedula.value.length !== 8 || !/^\d{8}$/.test(cedula.value)) {
            showError('cedula_error', 'La cédula debe tener exactamente 8 dígitos numéricos');
            isValid = false;
        }

        // Validar teléfono si se proporciona
        const telefono = document.getElementById('telefono');
        if (telefono.value && !/^\d{7,12}$/.test(telefono.value)) {
            showError('telefono_error', 'El teléfono debe tener entre 7 y 12 dígitos');
            isValid = false;
        }

        // Validar email si se proporciona
        const gmail = document.getElementById('gmail');
        if (gmail.value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(gmail.value)) {
            showError('gmail_error', 'Por favor ingrese un correo electrónico válido');
            isValid = false;
        }
        
        // Validar contraseña
        const password = document.getElementById('contraseña');
        if (!password.value || password.value.length < 8) {
            showError('password_error', 'La contraseña debe tener al menos 8 caracteres');
            isValid = false;
        }
        
        // Validar confirmación de contraseña
        if (!validatePasswordMatch()) {
            isValid = false;
        }
        
        // Validar rol
        const rol = document.getElementById('id_rol');
        if (!rol.value) {
            showError('rol_error', 'Por favor seleccione un rol del sistema');
            isValid = false;
        }
        
        return isValid;
    }
    
    function validatePasswordMatch() {
        const password = document.getElementById('contraseña');
        const confirmPassword = document.getElementById('confirm_password');
        
        if (password.value && confirmPassword.value && password.value !== confirmPassword.value) {
            showError('confirm_error', 'Las contraseñas no coinciden. Por favor verifique.');
            return false;
        }
        
        clearError('confirm_error');
        return true;
    }
    
    function showError(elementId, message) {
        const errorElement = document.getElementById(elementId);
        errorElement.textContent = message;
        errorElement.style.display = 'block';
        
        // Agregar animación
        errorElement.style.animation = 'shake 0.3s ease-in-out';
        setTimeout(() => {
            errorElement.style.animation = '';
        }, 300);
    }
    
    function clearError(elementId) {
        const errorElement = document.getElementById(elementId);
        errorElement.textContent = '';
        errorElement.style.display = 'none';
    }
    
    async function submitForm() {
        const formData = {
            nombre_completo: document.getElementById('nombre_completo').value.trim(),
            usuario_login: document.getElementById('usuario_login').value.trim(),
            cedula: document.getElementById('cedula').value.trim(),
            telefono: document.getElementById('telefono').value.trim(),
            gmail: document.getElementById('gmail').value.trim(),
            contraseña: document.getElementById('contraseña').value,
            id_rol: document.getElementById('id_rol').value
        };
        
        try {
            // Mostrar estado de carga
            const submitBtn = registerForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            btnText.innerHTML = '<i class="fas fa-spinner fa-spin" style="margin-right: 8px;"></i> Registrando...';
            
            const response = await fetch('/api/users', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();
            
            if (response.ok) {
                showMessage(data.message || '¡Registro exitoso! Redirigiendo al sistema...', 'success');
                
                // Redirigir después de 2 segundos
                setTimeout(() => {
                    window.location.href = data.redirect || '/login';
                }, 2000);
            } else {
                showMessage(data.error || 'Error en el registro. Por favor verifique los datos e intente nuevamente.', 'error');
                
                // Resaltar campos con error si vienen del servidor
                if (data.errors) {
                    Object.keys(data.errors).forEach(field => {
                        showError(field + '_error', data.errors[field]);
                    });
                }
            }
        } catch (error) {
            console.error('Error:', error);
            showMessage('Error de conexión con el servidor. Por favor intente más tarde.', 'error');
        } finally {
            // Restaurar botón
            const submitBtn = registerForm.querySelector('button[type="submit"]');
            submitBtn.disabled = false;
            btnText.textContent = 'Registrarse';
        }
    }
    
    function showMessage(message, type) {
        messageDiv.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center;">
                <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}" 
                   style="margin-right: 10px; font-size: 1.2rem;"></i>
                ${message}
            </div>
        `;
        messageDiv.className = `message ${type}`;
        messageDiv.style.display = 'block';
        
        // Desplazarse al mensaje
        messageDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        // Ocultar mensaje después de 5 segundos (excepto para éxito)
        if (type !== 'success') {
            setTimeout(() => {
                messageDiv.style.display = 'none';
            }, 5000);
        }
    }
    
    // Agregar animación de shake para errores
    document.head.insertAdjacentHTML('beforeend', `
        <style>
            @keyframes shake {
                0%, 100% { transform: translateX(0); }
                20%, 60% { transform: translateX(-5px); }
                40%, 80% { transform: translateX(5px); }
            }
        </style>
    `);
});