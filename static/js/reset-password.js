document.addEventListener('DOMContentLoaded', function() {
    // Elementos del DOM
    const resetForm = document.getElementById('resetForm');
    const messageDiv = document.getElementById('message');
    const passwordInput = document.getElementById('contraseña');
    const confirmInput = document.getElementById('confirm_password');
    const togglePassword = document.getElementById('togglePassword');
    const toggleConfirm = document.getElementById('toggleConfirmPassword');
    const btnText = document.getElementById('btn-text');
    const tokenInput = document.getElementById('token');

    // Verificar si hay un token válido en la URL
    const urlParams = new URLSearchParams(window.location.search);
    const urlToken = urlParams.get('token');
    if (urlToken && tokenInput) {
        tokenInput.value = urlToken;
    }

    // Mostrar/ocultar contraseña
    const togglePasswordVisibility = (inputElement, toggleElement) => {
        const type = inputElement.getAttribute('type') === 'password' ? 'text' : 'password';
        inputElement.setAttribute('type', type);
        const icon = toggleElement.querySelector('i');
        icon.classList.toggle('fa-eye');
        icon.classList.toggle('fa-eye-slash');
        toggleElement.innerHTML = type === 'password' 
            ? '<i class="fas fa-eye"></i> Mostrar' 
            : '<i class="fas fa-eye-slash"></i> Ocultar';
    };

    // Event listeners
    togglePassword?.addEventListener('click', () => togglePasswordVisibility(passwordInput, togglePassword));
    toggleConfirm?.addEventListener('click', () => togglePasswordVisibility(confirmInput, toggleConfirm));

    // Validar fortaleza de contraseña en tiempo real
    passwordInput?.addEventListener('input', function() {
        const errorElement = document.getElementById('password_error');
        if (this.value.length > 0 && this.value.length < 8) {
            errorElement.textContent = 'La contraseña debe tener al menos 8 caracteres';
            errorElement.style.display = 'block';
        } else {
            errorElement.style.display = 'none';
        }
    });

    // Validar coincidencia de contraseñas en tiempo real
    confirmInput?.addEventListener('input', function() {
        const errorElement = document.getElementById('confirm_error');
        if (this.value !== passwordInput.value) {
            errorElement.textContent = 'Las contraseñas no coinciden';
            errorElement.style.display = 'block';
        } else {
            errorElement.style.display = 'none';
        }
    });

    // Manejar el envío del formulario
    resetForm?.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Limpiar mensajes de error previos
        document.querySelectorAll('.error-message').forEach(el => {
            el.textContent = '';
            el.style.display = 'none';
        });

        // Obtener valores del formulario
        const password = passwordInput.value;
        const confirmPassword = confirmInput.value;
        const token = tokenInput.value;

        // Validaciones del cliente
        let isValid = true;

        if (!token) {
            showMessage('Token de recuperación no válido', 'error');
            isValid = false;
        }

        if (!password) {
            showError('password_error', 'Ingrese una contraseña');
            isValid = false;
        } else if (password.length < 8) {
            showError('password_error', 'La contraseña debe tener al menos 8 caracteres');
            isValid = false;
        }

        if (!confirmPassword) {
            showError('confirm_error', 'Confirme su contraseña');
            isValid = false;
        } else if (password !== confirmPassword) {
            showError('confirm_error', 'Las contraseñas no coinciden');
            isValid = false;
        }

        if (!isValid) return;

        try {
            // Mostrar estado de carga
            const submitBtn = resetForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            btnText.innerHTML = '<i class="fas fa-spinner fa-spin" style="margin-right: 8px;"></i> Procesando...';
            
            // Enviar solicitud al servidor
            const response = await fetch('/api/reset-password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    token: token,
                    nueva_contraseña: password
                })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                // Manejar diferentes tipos de errores
                let errorMsg = data.error || 'Error al actualizar la contraseña';
                
                if (data.code === 'invalid_token') {
                    errorMsg = 'El enlace de recuperación ha expirado o es inválido. Por favor solicite uno nuevo.';
                } else if (response.status === 400) {
                    errorMsg = 'Datos inválidos enviados al servidor';
                }
                
                throw new Error(errorMsg);
            }
            
            // Éxito - mostrar mensaje y redirigir
            showMessage('¡Contraseña actualizada correctamente! Redirigiendo al login...', 'success');
            resetForm.reset();
            
            setTimeout(() => {
                window.location.href = '/login';
            }, 2000);
            
        } catch (error) {
            console.error('Error:', error);
            showMessage(error.message || 'Error al procesar la solicitud', 'error');
        } finally {
            // Restaurar botón
            const submitBtn = resetForm.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = false;
                btnText.innerHTML = '<i class="fas fa-save" style="margin-right: 8px;"></i>Guardar Contraseña';
            }
        }
    });
    
    // Mostrar mensaje de error en un elemento específico
    function showError(elementId, message) {
        const errorElement = document.getElementById(elementId);
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.style.display = 'block';
            errorElement.style.animation = 'shake 0.3s ease-in-out';
            setTimeout(() => {
                errorElement.style.animation = '';
            }, 300);
        }
    }
    
    // Mostrar mensaje general en el contenedor
    function showMessage(message, type) {
        if (!messageDiv) return;
        
        messageDiv.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center;">
                <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}" 
                   style="margin-right: 10px; font-size: 1.2rem;"></i>
                ${message}
            </div>
        `;
        messageDiv.className = `message ${type}`;
        messageDiv.style.display = 'block';
        
        if (type !== 'success') {
            setTimeout(() => {
                messageDiv.style.display = 'none';
            }, 5000);
        }
    }
});

// Añadir animación de shake si no existe
if (!document.getElementById('shake-animation-style')) {
    const style = document.createElement('style');
    style.id = 'shake-animation-style';
    style.textContent = `
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            20%, 60% { transform: translateX(-5px); }
            40%, 80% { transform: translateX(5px); }
        }
    `;
    document.head.appendChild(style);
}