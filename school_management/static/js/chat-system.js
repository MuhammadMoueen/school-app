(function () {
    const app = document.querySelector('[data-chat-app]');
    if (!app) {
        return;
    }

    const endpoint = app.getAttribute('data-chat-endpoint');
    const targetId = app.getAttribute('data-chat-target-id');
    const presencePingUrl = document.body ? document.body.getAttribute('data-presence-ping-url') : null;
    const emptyText = app.getAttribute('data-empty-text') || 'Start conversation.';
    const thread = app.querySelector('[data-chat-thread]');
    const form = app.querySelector('[data-chat-form]');
    const input = app.querySelector('[data-chat-input]');
    const sendButton = app.querySelector('[data-chat-send]');
    const statusDot = app.querySelector('[data-chat-status-dot]');
    const statusText = app.querySelector('[data-chat-status-text]');

    if (!endpoint || !thread || !form || !input || !sendButton) {
        return;
    }

    const toSafeText = (value) => {
        if (value === null || value === undefined) {
            return '';
        }
        return String(value);
    };

    const buildMessageNode = (item) => {
        const row = document.createElement('div');
        const isOutgoing = Boolean(item.is_outgoing);
        row.className = 'chat-row ' + (isOutgoing ? 'mine' : 'theirs');

        const bubble = document.createElement('div');
        bubble.className = 'chat-bubble ' + (isOutgoing ? 'mine' : 'theirs');

        const meta = document.createElement('div');
        meta.className = 'chat-meta';
        const name = document.createElement('span');
        name.className = 'chat-name';
        name.textContent = toSafeText(item.name);
        meta.appendChild(name);

        const message = document.createElement('p');
        message.className = 'chat-message-text';
        message.textContent = toSafeText(item.message);

        const time = document.createElement('div');
        time.className = 'chat-time';

        const timeLabel = document.createElement('span');
        timeLabel.textContent = toSafeText(item.time_label);
        time.appendChild(timeLabel);

        if (isOutgoing && item.tick_state && item.tick_icon) {
            const tickWrap = document.createElement('span');
            tickWrap.className = 'chat-tick ' + toSafeText(item.tick_state);
            tickWrap.title = toSafeText(item.tick_label);
            const icon = document.createElement('i');
            icon.className = toSafeText(item.tick_icon);
            tickWrap.appendChild(icon);
            time.appendChild(tickWrap);
        }

        bubble.appendChild(meta);
        bubble.appendChild(message);
        bubble.appendChild(time);
        row.appendChild(bubble);
        return row;
    };

    const showEmptyState = () => {
        thread.innerHTML = '';
        const empty = document.createElement('div');
        empty.className = 'chat-empty-state';
        empty.innerHTML = '<div><i class="fas fa-comments"></i><p>' + emptyText + '</p></div>';
        thread.appendChild(empty);
    };

    const scrollToBottom = (smooth) => {
        thread.scrollTo({
            top: thread.scrollHeight,
            behavior: smooth ? 'smooth' : 'auto',
        });
    };

    const renderMessages = (messages, smooth) => {
        if (!Array.isArray(messages) || messages.length === 0) {
            showEmptyState();
            return;
        }

        thread.innerHTML = '';
        messages.forEach((item) => {
            thread.appendChild(buildMessageNode(item));
        });
        scrollToBottom(smooth);
    };

    const updatePresence = (presence) => {
        if (!presence || !statusDot || !statusText) {
            return;
        }

        statusDot.classList.remove('online', 'offline');
        statusDot.classList.add(presence.online ? 'online' : 'offline');
        statusText.textContent = toSafeText(presence.status_text || (presence.online ? 'Online' : 'Offline'));
    };

    const fetchUpdates = (smooth) => {
        const url = new URL(endpoint, window.location.origin);
        url.searchParams.set('chat_ajax', '1');

        return fetch(url.toString(), {
            method: 'GET',
            credentials: 'same-origin',
            cache: 'no-store',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
        })
            .then((response) => response.json())
            .then((data) => {
                if (!data.success) {
                    return;
                }
                renderMessages(data.messages || [], smooth);
                updatePresence(data.presence);
            })
            .catch(() => {
                // Do not block UI for transient polling errors.
            });
    };

    const sendMessage = () => {
        const textValue = input.value.trim();
        if (!textValue) {
            return;
        }

        const formData = new FormData(form);
        sendButton.disabled = true;

        fetch(endpoint, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: formData,
        })
            .then((response) => response.json())
            .then((data) => {
                if (!data.success) {
                    throw new Error(data.error || 'Unable to send message.');
                }

                input.value = '';
                input.style.height = '';
                return fetchUpdates(true);
            })
            .catch(() => {
                // Silent fail keeps page usable; normal submit still available if JS disabled.
            })
            .finally(() => {
                sendButton.disabled = false;
            });
    };

    form.addEventListener('submit', function (event) {
        event.preventDefault();
        sendMessage();
    });

    input.addEventListener('keydown', function (event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    });

    input.addEventListener('input', function () {
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 160) + 'px';
    });

    fetchUpdates(false);

    window.setInterval(function () {
        fetchUpdates(false);

        if (targetId && presencePingUrl) {
            const pingUrl = new URL(presencePingUrl, window.location.origin);
            pingUrl.searchParams.set('target_user_id', targetId);
            fetch(pingUrl.toString(), {
                method: 'GET',
                credentials: 'same-origin',
                cache: 'no-store',
            })
                .then((response) => response.json())
                .then((data) => {
                    if (data.success) {
                        updatePresence(data.presence);
                    }
                })
                .catch(() => {
                    // Ignore heartbeat errors.
                });
        }
    }, 10000);
})();
