(function () {
    function byId(id) {
        return document.getElementById(id);
    }

    function toggleCreateQuizSections() {
        var quizTypeEl = byId('id_quiz_type');
        if (!quizTypeEl) {
            return;
        }

        var sourceEl = byId('id_question_source');
        var totalMarksModeEl = byId('id_total_marks_mode');
        var totalMarksWrap = byId('quizTotalMarksWrap');

        var autoSection = byId('autoQuizSection');
        var manualSection = byId('manualQuizSection');
        var omrSection = byId('omrUploadSection');

        var isAuto = quizTypeEl.value === 'auto';
        var isOmr = sourceEl && sourceEl.value === 'omr_upload';

        if (autoSection) {
            autoSection.classList.toggle('quiz-hidden', !isAuto);
        }
        if (manualSection) {
            manualSection.classList.toggle('quiz-hidden', isAuto);
        }
        if (omrSection) {
            omrSection.classList.toggle('quiz-hidden', !(isAuto && isOmr));
        }
        if (sourceEl) {
            sourceEl.disabled = !isAuto;
        }
        if (totalMarksWrap && totalMarksModeEl) {
            totalMarksWrap.classList.toggle('quiz-hidden', totalMarksModeEl.value === 'auto');
        }
    }

    function toggleQuestionFields() {
        var questionTypeEl = byId('id_question_type');
        if (!questionTypeEl) {
            return;
        }

        var optionsSection = byId('questionOptionsSection');
        var correctAnswerWrap = byId('questionCorrectAnswerWrap');
        var isSubjective = questionTypeEl.value === 'subjective';

        if (optionsSection) {
            optionsSection.classList.toggle('quiz-hidden', isSubjective);
        }
        if (correctAnswerWrap) {
            correctAnswerWrap.classList.toggle('quiz-hidden', isSubjective);
        }
    }

    document.addEventListener('DOMContentLoaded', function () {
        var quizTypeEl = byId('id_quiz_type');
        var sourceEl = byId('id_question_source');
        var totalMarksModeEl = byId('id_total_marks_mode');
        var questionTypeEl = byId('id_question_type');

        if (quizTypeEl) {
            quizTypeEl.addEventListener('change', toggleCreateQuizSections);
        }
        if (sourceEl) {
            sourceEl.addEventListener('change', toggleCreateQuizSections);
        }
        if (totalMarksModeEl) {
            totalMarksModeEl.addEventListener('change', toggleCreateQuizSections);
        }
        if (questionTypeEl) {
            questionTypeEl.addEventListener('change', toggleQuestionFields);
        }

        toggleCreateQuizSections();
        toggleQuestionFields();
    });
})();
