(function () {
    var AUTO_DISMISS_MS = 1000;
    var EXIT_ANIMATION_MS = 240;

    function hideMessage(messageEl) {
        if (!messageEl || messageEl.classList.contains('is-hiding')) {
            return;
        }

        messageEl.classList.add('is-hiding');

        window.setTimeout(function () {
            if (messageEl.parentNode) {
                messageEl.parentNode.removeChild(messageEl);
            }

            var stack = document.getElementById('flashStack');
            if (stack && stack.children.length === 0) {
                stack.parentNode.removeChild(stack);
            }
        }, EXIT_ANIMATION_MS);
    }

    function initFlashMessages() {
        var stack = document.getElementById('flashStack');
        if (!stack) {
            return;
        }

        var messages = stack.querySelectorAll('.flash-message');

        messages.forEach(function (messageEl) {
            var closeBtn = messageEl.querySelector('.flash-close');
            if (closeBtn) {
                closeBtn.addEventListener('click', function () {
                    hideMessage(messageEl);
                });
            }

            window.setTimeout(function () {
                hideMessage(messageEl);
            }, AUTO_DISMISS_MS);
        });
    }

    document.addEventListener('DOMContentLoaded', initFlashMessages);
})();
