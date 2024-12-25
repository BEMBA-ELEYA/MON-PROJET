document.addEventListener("DOMContentLoaded", () => {
    const passwordInput = document.getElementById('password');
    const passwordConfirmInput = document.getElementById('password_confirm');

    passwordConfirmInput.addEventListener('input', () => {
        if (passwordInput.value !== passwordConfirmInput.value) {
            passwordConfirmInput.setCustomValidity('Les mots de passe ne correspondent pas.');
        } else {
            passwordConfirmInput.setCustomValidity('');
        }
    });
});