// Aeronexa Authentication JS

document.addEventListener('DOMContentLoaded', () => {
  const loginForm = document.getElementById('login-form');
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = loginForm.email.value.trim();
      const password = loginForm.password.value;

      if (!window.AeronexaValidation.validateEmail(email)) {
        window.Aeronexa.showToast('Please enter a valid email address.', 'warning');
        return;
      }

      try {
        const res = await fetch('/api/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });
        const data = await res.json();
        if (res.ok) {
          window.Aeronexa.showToast(data.message, 'success');
          setTimeout(() => {
            if (data.user.role === 'admin') {
              window.location.href = '/admin';
            } else {
              window.location.href = '/dashboard';
            }
          }, 1000);
        } else {
          window.Aeronexa.showToast(data.error || 'Login failed.', 'error');
        }
      } catch (err) {
        window.Aeronexa.showToast('Network error during login.', 'error');
      }
    });
  }

  const registerForm = document.getElementById('register-form');
  if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const name = registerForm.name.value.trim();
      const email = registerForm.email.value.trim();
      const mobile = registerForm.mobile.value.trim();
      const password = registerForm.password.value;
      const confirm_password = registerForm.confirm_password.value;

      if (!name || !email || !password) {
        window.Aeronexa.showToast('Please fill in all required fields.', 'warning');
        return;
      }

      if (!window.AeronexaValidation.validateEmail(email)) {
        window.Aeronexa.showToast('Please enter a valid email address.', 'warning');
        return;
      }

      if (mobile && !window.AeronexaValidation.validateIndianPhone(mobile)) {
        window.Aeronexa.showToast('Please enter a valid 10-digit or +91 mobile number.', 'warning');
        return;
      }

      if (password !== confirm_password) {
        window.Aeronexa.showToast('Passwords do not match.', 'error');
        return;
      }

      if (password.length < 6) {
        window.Aeronexa.showToast('Password must be at least 6 characters long.', 'warning');
        return;
      }

      try {
        const res = await fetch('/api/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, email, mobile, password })
        });
        const data = await res.json();
        if (res.ok) {
          window.Aeronexa.showToast(data.message, 'success');
          setTimeout(() => {
            window.location.href = '/dashboard';
          }, 1000);
        } else {
          window.Aeronexa.showToast(data.error || 'Registration failed.', 'error');
        }
      } catch (err) {
        window.Aeronexa.showToast('Network error during registration.', 'error');
      }
    });
  }

  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      try {
        const res = await fetch('/api/logout', { method: 'POST' });
        if (res.ok) {
          window.Aeronexa.showToast('Logged out successfully.', 'info');
          setTimeout(() => {
            window.location.href = '/';
          }, 800);
        }
      } catch (err) {
        window.location.href = '/';
      }
    });
  }
});
