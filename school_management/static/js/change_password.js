function togglePassword(fieldId, button) {
    const field = document.getElementById(fieldId);
    const icon = button.querySelector('i');

    if (!field || !icon) {
        return;
    }

    const isHidden = field.type === 'password';
    field.type = isHidden ? 'text' : 'password';
    button.setAttribute('aria-pressed', isHidden ? 'true' : 'false');
    icon.classList.toggle('fa-eye', !isHidden);
    icon.classList.toggle('fa-eye-slash', isHidden);
}

document.querySelectorAll('.password-toggle').forEach((button) => {
    button.addEventListener('click', () => {
        const fieldId = button.dataset.target;
        if (fieldId) {
            togglePassword(fieldId, button);
        }
    });
});
