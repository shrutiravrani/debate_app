/* static/js/script.js */
document.addEventListener('DOMContentLoaded', function() {
    const loginButton = document.getElementById('loginButton');
    const signupButton = document.getElementById('signupButton');
    const logoutButton = document.getElementById('logoutButton');
    const authModal = document.getElementById('authModal');
    const authForms = document.getElementById('authForms');
    const closeModal = document.querySelector('.close');

    // Check if user is authenticated
    let current_user = null; // Set this dynamically based on user state

    // Event listeners
    loginButton.addEventListener('click', () => showForm('login'));
    signupButton.addEventListener('click', () => showForm('signup'));
    logoutButton.addEventListener('click', handleLogout);
    closeModal.addEventListener('click', () => authModal.style.display = 'none');
    window.addEventListener('click', (event) => {
        if (event.target == authModal) {
            authModal.style.display = 'none';
        }
    });

    // Function to show login/signup forms
    function showForm(type) {
        if (type === 'login') {
            fetch('/login')
                .then(response => response.text())
                .then(html => {
                    authForms.innerHTML = html;
                    document.getElementById('loginForm').addEventListener('submit', handleLogin);
                });
        } else {
            fetch('/signup')
                .then(response => response.text())
                .then(html => {
                    authForms.innerHTML = html;
                    document.getElementById('signupForm').addEventListener('submit', handleSignup);
                });
        }
        authModal.style.display = 'block';
    }

    // Function to handle login
    function handleLogin(event) {
        event.preventDefault();
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;
        
        fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                userName: username,
                passwordHash: password, // Hash password in a real application
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log('User logged in:', data);
            authModal.style.display = 'none';
            setCurrentUser(data); // Set current user state
            updateAuthButtons();
        })
        .catch(error => console.error('Error:', error));
    }

    // Function to handle signup
    function handleSignup(event) {
        event.preventDefault();
        const username = document.getElementById('signupUsername').value;
        const password = document.getElementById('signupPassword').value;
        const isAdmin = document.getElementById('isAdmin').checked;
        
        fetch('/users', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                userName: username,
                passwordHash: password, // Hash password in a real application
                isAdmin: isAdmin
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log('User signed up:', data);
            authModal.style.display = 'none';
            setCurrentUser(data); // Set current user state
            updateAuthButtons();
        })
        .catch(error => console.error('Error:', error));
    }

    // Function to handle logout
    function handleLogout() {
        fetch('/logout', {
            method: 'POST'
        })
        .then(() => {
            console.log('User logged out');
            setCurrentUser(null); // Clear current user state
            updateAuthButtons();
        })
        .catch(error => console.error('Error:', error));
    }

    // Function to set current user state
    function setCurrentUser(user) {
        current_user = user;
    }

    // Function to update authentication buttons
    function updateAuthButtons() {
        if (current_user) {
            loginButton.style.display = 'none';
            signupButton.style.display = 'none';
            logoutButton.style.display = 'block';
        } else {
            loginButton.style.display = 'block';
            signupButton.style.display = 'block';
            logoutButton.style.display = 'none';
        }
    }

    // Initial update of authentication buttons
    updateAuthButtons();
});

// Function to display login form
function showLoginForm() {
    // Assuming you have a modal or popup container in your HTML
    var loginFormContainer = document.querySelector('.login-form-container');

    // Display the login form container (toggle its visibility)
    loginFormContainer.style.display = 'block';

    // Optionally, you can prevent scrolling of the main content behind the popup
    document.body.style.overflow = 'hidden';
}

// Function to display signup form
function showSignupForm() {
    // Assuming you have a modal or popup container in your HTML
    var signupFormContainer = document.querySelector('.signup-form-container');

    // Display the signup form container (toggle its visibility)
    signupFormContainer.style.display = 'block';

    // Optionally, you can prevent scrolling of the main content behind the popup
    document.body.style.overflow = 'hidden';
}
