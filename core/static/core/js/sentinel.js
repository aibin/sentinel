function togglePassword(elementId) {
    const passwordField = document.getElementById(elementId);
    const toggleIcon = document.getElementById("toggle-icon");
    // Toggle the type of the password field
    if (passwordField.type === "password") {
        passwordField.type = "text";
        toggleIcon.classList.remove("bi-eye-fill");
        toggleIcon.classList.add("bi-eye-slash-fill");
    } else {
        passwordField.type = "password";
        toggleIcon.classList.remove("bi-eye-slash-fill");
        toggleIcon.classList.add("bi-eye-fill");
    }
}