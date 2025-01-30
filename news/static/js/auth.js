// Authentication handling
const loginForm = document.getElementById('login-form');
const signupForm = document.getElementById('signup-form');

loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(loginForm);
    try {
        const response = await fetch('/accounts/login/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        if (response.ok) {
            location.reload();
        } else {
            showToast('Login failed. Please try again.');
        }
    } catch (error) {
        console.error('Login error:', error);
    }
});

signupForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(signupForm);
    try {
        const response = await fetch('/accounts/signup/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        if (response.ok) {
            location.reload();
        } else {
            showToast('Signup failed. Please try again.');
        }
    } catch (error) {
        console.error('Signup error:', error);
    }
}); 