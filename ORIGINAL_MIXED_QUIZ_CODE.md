# Original Mixed Quiz Code - Complete Restore Guide

This file contains the **ORIGINAL** UI and code from the very beginning (Commit: 1ab909f) before any changes.

## Original Implementation Features:
- 3-section UI for adding different question types
- MCQ questions with options (A, B, C, D)
- Subjective/Essay questions for manual grading
- File upload support for question papers
- Clean conditional rendering based on quiz type

## 1. ORIGINAL models.py (Quiz Model Changes)

In `QUIZ_TYPE_CHOICES`, keep:
```python
QUIZ_TYPE_CHOICES = (
    ('auto', 'MCQ Only (Auto-Graded)'),
    ('manual', 'Subjective Only (Manual)'),
    ('mixed', 'Mixed Mode (MCQ + Subjective + File Upload)'),
)
```

## 2. ORIGINAL forms.py (QuizForm)

Changes needed in QuizForm clean() method:
```python
# For mixed quizzes, validate that they can have both types
if quiz_type == 'mixed':
    # Mixed mode allows both MCQ and subjective questions
    # No special validation needed - all question types allowed
    pass
```

## 3. ORIGINAL create_quiz.html - Full Template

Key sections:

### Quiz Type Dropdown (ORIGINAL):
```html
<div class="mb-3">
    <label class="form-label">Quiz Type <span class="text-danger">*</span></label>
    {{ form.quiz_type }}
    {% if form.quiz_type.errors %}
    <div class="text-danger small mt-2">
        {% for error in form.quiz_type.errors %}
        <i class="fas fa-exclamation-triangle"></i> {{ error }}<br>
        {% endfor %}
    </div>
    {% endif %}
</div>
```

### Auto Quiz Section (ORIGINAL):
```html
<div id="autoQuizSection" class="quiz-section">
    <div class="quiz-section-title">Auto-Graded Setup</div>
    <div class="mb-3">
        <label class="form-label">MCQ Source</label>
        {{ form.question_source }}
        {% if form.question_source.errors %}
        <div class="text-danger small mt-2">
            {% for error in form.question_source.errors %}
            <i class="fas fa-exclamation-triangle"></i> {{ error }}<br>
            {% endfor %}
        </div>
        {% endif %}
    </div>
    <div id="omrUploadSection" class="quiz-hidden">
        <div class="mb-3">
            <label class="form-label">Upload MCQ File (PDF, JPG, PNG, DOCX)</label>
            {{ form.omr_source_file }}
            {% if form.omr_source_file.errors %}
            <div class="text-danger small mt-2">
                {% for error in form.omr_source_file.errors %}
                <i class="fas fa-exclamation-triangle"></i> {{ error }}<br>
                {% endfor %}
            </div>
            {% endif %}
        </div>
        <div class="mb-3">
            <label class="form-label">Answer Key (Text)</label>
            {{ form.answer_key_text }}
            {% if form.answer_key_text.errors %}
            <div class="text-danger small mt-2">
                {% for error in form.answer_key_text.errors %}
                <i class="fas fa-exclamation-triangle"></i> {{ error }}<br>
                {% endfor %}
            </div>
            {% endif %}
            <div class="quiz-helper-text">Use format like: Q1: A, Q2: C, Q3: B</div>
        </div>
        <div class="mb-3">
            <label class="form-label">Answer Key File (TXT, CSV, DOCX)</label>
            {{ form.answer_key_file }}
            {% if form.answer_key_file.errors %}
            <div class="text-danger small mt-2">
                {% for error in form.answer_key_file.errors %}
                <i class="fas fa-exclamation-triangle"></i> {{ error }}<br>
                {% endfor %}
            </div>
            {% endif %}
        </div>
        <div class="quiz-helper-text">Basic parsing is applied for text-based keys. For scanned OMR files, this is stored as a reference file.</div>
    </div>
</div>
```

### Manual Quiz Section (ORIGINAL):
```html
<div id="manualQuizSection" class="quiz-section quiz-hidden">
    <div class="quiz-section-title">Manual Quiz Setup</div>
    <div class="quiz-helper-text">Manual quizzes support descriptive questions and teacher checking with feedback.</div>
</div>
```

### Mixed Quiz Section (ORIGINAL):
```html
<div id="mixedQuizSection" class="quiz-section quiz-hidden">
    <div class="quiz-section-title">Mixed Mode Setup</div>
    <div style="background-color: #e8f4f8; border-left: 4px solid #0284c7; padding: 12px 16px; margin-bottom: 15px; border-radius: 4px;">
        <p style="margin: 0; color: #0c4a6e; font-size: 0.95rem;">
            <i class="fas fa-info-circle"></i> <strong>Mixed Mode:</strong> Combine MCQ questions (auto-graded) and Subjective questions (manually graded) in a single quiz. Students answer both types in one attempt.
        </p>
    </div>
</div>
```

## 4. ORIGINAL quiz-create.js - JavaScript Toggle

```javascript
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
    var mixedSection = byId('mixedQuizSection');
    var omrSection = byId('omrUploadSection');

    var isAuto = quizTypeEl.value === 'auto';
    var isManual = quizTypeEl.value === 'manual';
    var isMixed = quizTypeEl.value === 'mixed';
    var isOmr = sourceEl && sourceEl.value === 'omr_upload';

    if (autoSection) {
        autoSection.classList.toggle('quiz-hidden', !isAuto);
    }
    if (manualSection) {
        manualSection.classList.toggle('quiz-hidden', !isManual);
    }
    if (mixedSection) {
        mixedSection.classList.toggle('quiz-hidden', !isMixed);
    }
    if (omrSection) {
        omrSection.classList.toggle('quiz-hidden', !(isAuto && isOmr));
    }
    if (sourceEl) {
        sourceEl.disabled = !isAuto && !isMixed;
        if (!isAuto && !isMixed) {
            sourceEl.value = 'manual';
        }
    }
    if (totalMarksWrap && totalMarksModeEl) {
        totalMarksWrap.classList.toggle('quiz-hidden', totalMarksModeEl.value === 'auto');
    }
}
```

## 5. ORIGINAL add_questions.html - 3 Section UI

### Section 1: Upload Paper (For Manual & Mixed):
```html
<!-- SECTION 1: UPLOAD FULL QUESTION PAPER (Manual & Mixed) -->
{% if quiz.quiz_type == 'manual' or quiz.quiz_type == 'mixed' %}
<div class="premium-card">
    <div class="section-header">
        <div class="section-header-icon">
            <i class="fas fa-file-upload"></i>
        </div>
        <div style="flex: 1;">
            <h3>Upload Full Question Paper</h3>
            <p>Upload a complete question paper (Optional)</p>
        </div>
    </div>
    <!-- File upload form here -->
</div>
{% endif %}
```

### Section 2: MCQ Questions (For Auto & Mixed):
```html
<!-- SECTION 2: MCQ QUESTIONS (Auto & Mixed) -->
{% if quiz.quiz_type == 'auto' or quiz.quiz_type == 'mixed' %}
<div class="premium-card">
    <div class="section-header">
        <div class="section-header-icon">
            <i class="fas fa-tasks"></i>
        </div>
        <div style="flex: 1;">
            <h3>Add MCQ Questions</h3>
            <p>Add multiple choice questions with options</p>
        </div>
    </div>
    <!-- MCQ form here -->
</div>
{% endif %}
```

### Section 3: Subjective Questions (For Manual & Mixed):
```html
<!-- SECTION 3: SUBJECTIVE QUESTIONS (Manual & Mixed) -->
{% if quiz.quiz_type == 'manual' or quiz.quiz_type == 'mixed' %}
<div class="premium-card">
    <div class="section-header">
        <div class="section-header-icon">
            <i class="fas fa-pen-fancy"></i>
        </div>
        <div style="flex: 1;">
            <h3>Add Subjective Questions</h3>
            <p>Add open-ended questions for manual grading</p>
        </div>
    </div>
    <!-- Subjective form here -->
</div>
{% endif %}
```

## 6. ORIGINAL views.py - Question Validation

In `add_questions()` function:

```python
# Validate question type against quiz type
if quiz.quiz_type == 'auto' and question_type == 'subjective':
    messages.error(request, 'MCQ-only quizzes support objective questions only.')
    return redirect('main:add_questions', quiz_id=quiz.id)

if quiz.quiz_type == 'manual' and question_type != 'subjective':
    messages.error(request, 'Subjective-only quizzes require subjective questions only.')
    return redirect('main:add_questions', quiz_id=quiz.id)

# Mixed quizzes allow BOTH types - no validation needed!
# Users can add MCQ and Subjective questions freely
```

## 7. How to Restore to Original Mixed Quiz

Step 1: In models.py, ensure QUIZ_TYPE_CHOICES includes:
```python
('mixed', 'Mixed Mode (MCQ + Subjective + File Upload)'),
```

Step 2: Add this condition in forms.py clean() method after auto/manual validation:
```python
if quiz_type == 'mixed':
    # Allow both question types
    cleaned_data['question_source'] = 'manual'
```

Step 3: In quiz-create.js, update toggleCreateQuizSections() to:
- Check for `isMixed` value
- Show/hide `mixedSection` div
- Keep sourceEl enabled for mixed type

Step 4: Update create_quiz.html:
- Add `mixedQuizSection` div with info box
- Ensure it shows when 'mixed' is selected

Step 5: Update add_questions.html conditions:
- Section 1: `if quiz.quiz_type == 'manual' or quiz.quiz_type == 'mixed'`
- Section 2: `if quiz.quiz_type == 'auto' or quiz.quiz_type == 'mixed'`
- Section 3: `if quiz.quiz_type == 'manual' or quiz.quiz_type == 'mixed'`

Step 6: Create/apply database migrations:
```bash
python manage.py makemigrations main
python manage.py migrate main
```

Step 7: Test by creating a "Mixed Mode" quiz and adding both MCQ and Subjective questions!

---

## Original UI Flow Summary:

1. **Quiz Creation Page**: 3 options - Auto, Manual, **Mixed Mode**
2. **Mixed Mode Selection**: Shows info box explaining mixed mode capability
3. **Add Questions Page**: Shows all 3 sections:
   - Paper upload (for manual grading)
   - MCQ section (auto-graded)
   - Subjective section (manual grading)
4. **Teacher Can**: Upload MCQs AND add subjective questions in one quiz
5. **Grading**: MCQs auto-graded, subjectives manually graded afterward

This is the ORIGINAL implementation before Draft/Publish was added!
