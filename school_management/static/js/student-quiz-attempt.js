(function () {
    function safeParse(value, fallback) {
        try {
            return JSON.parse(value);
        } catch (err) {
            return fallback;
        }
    }

    function buildPayload(formEl) {
        var payload = {};
        var cards = formEl.querySelectorAll('.quiz-question-card');
        cards.forEach(function (card) {
            var qid = card.getAttribute('data-question-id');
            if (!qid) {
                return;
            }

            var checked = card.querySelector('input[type="radio"]:checked');
            var textArea = card.querySelector('textarea');
            payload[qid] = {
                selected_answer: checked ? checked.value : '',
                answer_text: textArea ? textArea.value.trim() : ''
            };
        });
        return payload;
    }

    function fillExistingAnswers(formEl, existing) {
        Object.keys(existing || {}).forEach(function (qid) {
            var card = formEl.querySelector('.quiz-question-card[data-question-id="' + qid + '"]');
            if (!card) {
                return;
            }

            var answer = existing[qid] || {};
            var selected = answer.selected_answer || '';
            var text = answer.answer_text || '';

            if (selected) {
                var radio = card.querySelector('input[type="radio"][value="' + selected + '"]');
                if (radio) {
                    radio.checked = true;
                }
            }
            if (text) {
                var textArea = card.querySelector('textarea');
                if (textArea) {
                    textArea.value = text;
                }
            }
        });
    }

    function updateProgress(formEl) {
        var cards = formEl.querySelectorAll('.quiz-question-card');
        var answered = 0;
        cards.forEach(function (card) {
            var hasChecked = !!card.querySelector('input[type="radio"]:checked');
            var textArea = card.querySelector('textarea');
            var hasText = textArea && textArea.value.trim().length > 0;
            if (hasChecked || hasText) {
                answered += 1;
            }
        });

        var total = cards.length;
        var percent = total > 0 ? Math.round((answered / total) * 100) : 0;

        var progressLabel = document.getElementById('quizProgressLabel');
        var progressBar = document.getElementById('quizProgressBar');
        if (progressLabel) {
            progressLabel.textContent = answered + ' / ' + total + ' answered';
        }
        if (progressBar) {
            progressBar.style.width = percent + '%';
        }
    }

    function setupOneByOneMode(formEl, mode) {
        if (mode !== 'one_by_one') {
            return;
        }

        var cards = Array.prototype.slice.call(formEl.querySelectorAll('.quiz-question-card'));
        var activeIndex = 0;

        function render() {
            cards.forEach(function (card, idx) {
                card.classList.toggle('quiz-hidden', idx !== activeIndex);
            });

            var indexEl = document.getElementById('quizStepIndex');
            if (indexEl) {
                indexEl.textContent = 'Question ' + (activeIndex + 1) + ' of ' + cards.length;
            }

            var prevBtn = document.getElementById('quizPrevBtn');
            var nextBtn = document.getElementById('quizNextBtn');
            if (prevBtn) {
                prevBtn.disabled = activeIndex === 0;
            }
            if (nextBtn) {
                nextBtn.disabled = activeIndex >= cards.length - 1;
            }
        }

        var prevBtn = document.getElementById('quizPrevBtn');
        var nextBtn = document.getElementById('quizNextBtn');
        if (prevBtn) {
            prevBtn.addEventListener('click', function () {
                if (activeIndex > 0) {
                    activeIndex -= 1;
                    render();
                }
            });
        }
        if (nextBtn) {
            nextBtn.addEventListener('click', function () {
                if (activeIndex < cards.length - 1) {
                    activeIndex += 1;
                    render();
                }
            });
        }

        render();
    }

    document.addEventListener('DOMContentLoaded', function () {
        var configEl = document.getElementById('quizRuntimeConfig');
        var formEl = document.getElementById('quizForm');
        if (!configEl || !formEl) {
            return;
        }

        var config = safeParse(configEl.textContent, {});
        var remainingSeconds = Number(config.remaining_seconds || 0);
        var autosaveUrl = config.autosave_url || '';
        var displayMode = config.display_mode || 'full';
        var csrfToken = config.csrf_token || '';
        var existingAnswers = config.existing_answers || {};

        var saveIndicator = document.getElementById('quizSaveIndicator');
        var submitBtn = document.getElementById('submitQuizBtn');
        var timerEl = document.getElementById('quizTimer');

        fillExistingAnswers(formEl, existingAnswers);
        updateProgress(formEl);
        setupOneByOneMode(formEl, displayMode);

        var saveTimeout = null;
        function autosave() {
            if (!autosaveUrl) {
                return;
            }

            var payload = { answers: buildPayload(formEl) };
            fetch(autosaveUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify(payload)
            })
                .then(function (response) { return response.json(); })
                .then(function (result) {
                    if (result && result.success && saveIndicator) {
                        saveIndicator.textContent = 'Saved ' + new Date().toLocaleTimeString();
                    }
                })
                .catch(function () {
                    if (saveIndicator) {
                        saveIndicator.textContent = 'Save failed';
                    }
                });
        }

        function scheduleAutosave() {
            if (saveTimeout) {
                clearTimeout(saveTimeout);
            }
            saveTimeout = setTimeout(autosave, 500);
        }

        formEl.addEventListener('change', function () {
            updateProgress(formEl);
            scheduleAutosave();
        });
        formEl.addEventListener('input', function () {
            updateProgress(formEl);
            scheduleAutosave();
        });

        setInterval(autosave, 20000);

        function renderTimer() {
            var mins = Math.floor(remainingSeconds / 60);
            var secs = remainingSeconds % 60;
            if (timerEl) {
                timerEl.textContent = String(mins).padStart(2, '0') + ':' + String(secs).padStart(2, '0');
            }
        }

        function tick() {
            renderTimer();
            if (remainingSeconds <= 0) {
                if (submitBtn) {
                    submitBtn.disabled = true;
                }
                autosave();
                formEl.submit();
                return;
            }
            remainingSeconds -= 1;
            setTimeout(tick, 1000);
        }

        window.addEventListener('beforeunload', function () {
            autosave();
        });

        tick();
    });
})();
