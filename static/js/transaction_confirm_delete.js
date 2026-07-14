// static/js/delete_confirmation.js

// ============================================
// DELETE CONFIRMATION - AUTO SUBMIT FORM
// ============================================

/**
 * Automatically submits the delete confirmation form
 * when the page loads
 */
document.addEventListener("DOMContentLoaded", function() {
    const deleteForm = document.getElementById("auto-delete-form");
    if (deleteForm) {
        deleteForm.submit();
    }
});