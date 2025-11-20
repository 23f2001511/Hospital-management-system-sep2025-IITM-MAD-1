// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', () => {

    // Get references to DOM elements
    const loginTab = document.getElementById('login-tab');
    const registerTab = document.getElementById('register-tab');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');

    const loginFormSubmit = document.getElementById('loginFormSubmit');
    const registerFormSubmit = document.getElementById('registerFormSubmit');

    // Function to show the login form and hide the register form
    window.showLogin = function() {
        loginForm.classList.remove('d-none');
        registerForm.classList.add('d-none');
        
        loginTab.classList.add('active');
        registerTab.classList.remove('active');

        // Add animation class for a smooth entry
        loginForm.classList.add('animate-in');
    }

    // Function to show the register form and hide the login form
    window.showRegister = function() {
        loginForm.classList.add('d-none');
        registerForm.classList.remove('d-none');

        loginTab.classList.remove('active');
        registerTab.classList.add('active');

        // Add animation class for a smooth entry
        registerForm.classList.add('animate-in');
    }

    // --- FORM SUBMISSION HANDLING (Front-End Only) ---
    // This is where you would make an API call to your backend.

    loginFormSubmit.addEventListener('submit', (event) => {
        event.preventDefault(); // Prevent the default form submission

        // Get data from the login form
        const email = document.getElementById('loginEmail').value;
        const password = document.getElementById('loginPassword').value;
        const role = document.getElementById('loginRole').value;

        // Basic validation
        if (!email || !password || !role) {
            alert('Please fill in all fields.');
            return;
        }

        console.log('--- Login Attempt ---');
        console.log('Role:', role);
        console.log('Email:', email);
        console.log('Password:', password); // In a real app, NEVER log passwords.

        // Placeholder for backend API call
        alert(`Simulating login for ${role}: ${email}. Check the console for details.`);
        
        // Example: You would use fetch() here to send data to your server
        // fetch('/api/login', { method: 'POST', body: JSON.stringify({ email, password, role }) })
        //   .then(response => response.json())
        //   .then(data => { console.log(data); /* Handle success/error */ });
    });

    registerFormSubmit.addEventListener('submit', (event) => {
        event.preventDefault(); // Prevent the default form submission

        // Get data from the register form
        const fullName = document.getElementById('registerName').value;
        const email = document.getElementById('registerEmail').value;
        const password = document.getElementById('registerPassword').value;
        const role = document.getElementById('registerRole').value;
        const terms = document.getElementById('termsCheck').checked;

        // Basic validation
        if (!fullName || !email || !password || !role) {
            alert('Please fill in all required fields.');
            return;
        }
        if (!terms) {
            alert('You must agree to the Terms & Conditions.');
            return;
        }

        console.log('--- Registration Attempt ---');
        console.log('Full Name:', fullName);
        console.log('Email:', email);
        console.log('Password:', password);
        console.log('Registering as:', role);

        // Placeholder for backend API call
        alert(`Simulating registration for ${fullName}. Check the console for details.`);

        // Example: You would use fetch() here
        // fetch('/api/register', { method: 'POST', body: JSON.stringify({ fullName, email, password, role }) })
        //   .then(response => response.json())
        //   .then(data => { console.log(data); /* Handle success/error */ });
    });

});