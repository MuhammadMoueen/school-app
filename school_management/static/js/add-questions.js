/**
 * Add Questions Page JavaScripts
 */

// Auto-click file input on wrapper click
document.addEventListener('click', function(e) {
    if (e.target.closest('[onclick*="FileInput"]')) {
        e.preventDefault();
    }
});
