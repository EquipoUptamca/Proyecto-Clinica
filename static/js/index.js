document.addEventListener('DOMContentLoaded', function() {
  // Verificar autenticación existente
  const checkAuth = () => {
    const token = localStorage.getItem('authToken');
    const userRole = localStorage.getItem('userRole');
    
    if (token) {
      const redirectPaths = {
        '1': '/admin_dashboard',
        '2': '/doctor_dashboard',
        '3': '/patient_dashboard'
      };
      
      const path = redirectPaths[userRole] || '/dashboard';
      window.location.href = path;
    }
  };
  
  // Manejar clic en botones con feedback visual
  const handleButtonClick = (button, path) => {
    checkAuth();
    
    // Efecto visual al hacer clic
    button.style.transform = 'scale(0.95)';
    button.style.opacity = '0.8';
    
    setTimeout(() => {
      button.style.transform = '';
      button.style.opacity = '';
      window.location.href = path;
    }, 150);
  };
  
  document.getElementById('loginBtn').addEventListener('click', function() {
    handleButtonClick(this, '/login');
  });
  
  document.getElementById('registerBtn').addEventListener('click', function() {
    handleButtonClick(this, '/register');
  });
  
  // Efecto hover mejorado para tarjetas
  const cards = document.querySelectorAll('.feature-card');
  cards.forEach(card => {
    card.addEventListener('mouseenter', () => {
      card.style.transform = 'translateY(-8px)';
      card.style.boxShadow = '0 15px 30px rgba(0,0,0,0.15)';
    });
    card.addEventListener('mouseleave', () => {
      card.style.transform = 'translateY(0)';
      card.style.boxShadow = 'var(--shadow-md)';
    });
  });
  
  // Cargar testimonios dinámicamente
  const loadTestimonials = () => {
    const testimonials = [
      {
        name: "Dr. Juan Pérez",
        role: "Cardiólogo",
        text: "MedAsistencia ha transformado nuestra forma de trabajar, optimizando tiempos y mejorando la atención al paciente.",
        avatar: "/static/img/avatars/doctor1.jpg"
      },
      {
        name: "Dra. María González",
        role: "Pediatra",
        text: "La plataforma es intuitiva y completa. Ahora puedo acceder a los historiales de mis pacientes desde cualquier lugar.",
        avatar: "/static/img/avatars/doctor2.jpg"
      },
      {
        name: "Lic. Carlos Rodríguez",
        role: "Administrador",
        text: "Los reportes automatizados nos han ahorrado horas de trabajo manual. La gestión del centro es ahora más eficiente.",
        avatar: "/static/img/avatars/admin1.jpg"
      }
    ];
    
    const slider = document.querySelector('.testimonial-slider');
    
    if (slider) {
      testimonials.forEach(testimonial => {
        const testimonialElement = document.createElement('div');
        testimonialElement.className = 'testimonial';
        testimonialElement.innerHTML = `
          <div class="testimonial-content">
            <p>"${testimonial.text}"</p>
            <div class="testimonial-author">
              <img src="${testimonial.avatar}" alt="${testimonial.name}" class="testimonial-avatar">
              <div>
                <h5>${testimonial.name}</h5>
                <small>${testimonial.role}</small>
              </div>
            </div>
          </div>
        `;
        slider.appendChild(testimonialElement);
      });
    }
  };
  
  // Verificar preferencias de animación del usuario
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  
  if (!prefersReducedMotion) {
    // Cargar animaciones solo si el usuario no ha solicitado reducción de movimiento
    loadTestimonials();
    
    // Observador de intersección para animaciones al hacer scroll
    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate');
          observer.unobserve(entry.target);
        }
      });
    }, observerOptions);
    
    document.querySelectorAll('.feature-card, .content-container').forEach(el => {
      observer.observe(el);
    });
  } else {
    // Cargar contenido sin animaciones
    loadTestimonials();
  }
  
  // Mejorar accesibilidad del teclado
  document.querySelectorAll('button, [tabindex="0"]').forEach(el => {
    el.addEventListener('focus', () => {
      el.style.outline = '2px solid var(--accent-color)';
      el.style.outlineOffset = '2px';
    });
    
    el.addEventListener('blur', () => {
      el.style.outline = 'none';
    });
  });
});