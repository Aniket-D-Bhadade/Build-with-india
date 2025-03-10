document.addEventListener('DOMContentLoaded', () => {
    // Get the Get Started button
    const getStartedBtn = document.querySelector('.cta-btn');
    
    if (getStartedBtn) {
        getStartedBtn.addEventListener('click', () => {
            // Redirect to the chatbot page
            window.location.href = '/chatbot';
        });
    }

    // Get the login button
    const loginBtn = document.querySelector('.contact-btn');
    
    if (loginBtn) {
        loginBtn.addEventListener('click', () => {
            // For now, also redirect to chatbot (you can change this to a login page later)
            window.location.href = '/chatbot';
        });
    }
}); 