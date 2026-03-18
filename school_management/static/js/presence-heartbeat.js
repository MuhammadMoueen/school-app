(function () {
    const pingUrl = document.body ? document.body.getAttribute('data-presence-ping-url') : null;
    if (!pingUrl) {
        return;
    }

    const sendPresencePing = () => {
        fetch(pingUrl, {
            method: 'GET',
            credentials: 'same-origin',
            cache: 'no-store',
        }).catch(() => {
            // Ignore heartbeat failures; UI must remain responsive.
        });
    };

    sendPresencePing();
    window.setInterval(sendPresencePing, 30000);
})();
