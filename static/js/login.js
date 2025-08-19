document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const messageDiv = document.getElementById('message');
    const passwordInput = document.getElementById('contraseña');
    const togglePassword = document.getElementById('togglePassword');
    const btnText = document.getElementById('btn-text');

    // Mostrar/ocultar contraseña
    togglePassword.addEventListener('click', function() {
        const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordInput.setAttribute('type', type);
        const icon = this.querySelector('i');
        icon.classList.toggle('fa-eye');
        icon.classList.toggle('fa-eye-slash');
        this.innerHTML = type === 'password' 
            ? '<i class="fas fa-eye"></i> Mostrar' 
            : '<i class="fas fa-eye-slash"></i> Ocultar';
    });

    // Manejar el envío del formulario
    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Validación básica del cliente
        const identificador = document.getElementById('identificador').value.trim();
        const contraseña = document.getElementById('contraseña').value;
        
        if (!identificador) {
            showError('identificador_error', 'Ingrese su usuario o cédula');
            return;
        }
        
        if (!contraseña) {
            showError('password_error', 'Ingrese su contraseña');
            return;
        }
        
        try {
            // Mostrar estado de carga
            const submitBtn = loginForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            btnText.innerHTML = '<i class="fas fa-spinner fa-spin" style="margin-right: 8px;"></i> Ingresando...';
            
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    identificador: identificador,
                    contraseña: contraseña
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                showMessage('Inicio de sesión exitoso. Redirigiendo...', 'success');
                setTimeout(() => {
                    window.location.href = data.redirect || '/dashboard';
                }, 1500);
            } else {
                showMessage(data.error || 'Credenciales incorrectas. Por favor intente nuevamente.', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            showMessage('Error de conexión con el servidor', 'error');
        } finally {
            // Restaurar botón
            const submitBtn = loginForm.querySelector('button[type="submit"]');
            submitBtn.disabled = false;
            btnText.innerHTML = '<i class="fas fa-sign-in-alt" style="margin-right: 8px;"></i>Ingresar';
        }
    });
    
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