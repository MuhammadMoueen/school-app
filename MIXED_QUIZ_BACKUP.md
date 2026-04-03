# Mixed Quiz Feature - Code Backup

This file contains the complete code for the Mixed Quiz feature (Draft/Publish workflow) that was built and later removed. You can restore this feature at any time by referencing this file.

## 1. Models.py Changes

Add this to `QUIZ_TYPE_CHOICES` in the Quiz model:
```python
('mixed', 'Mixed (MCQ + Subjective)'),
```

Add this to the Quiz model (after TOTAL_MARKS_MODE_CHOICES):
```python
STATUS_CHOICES = (
    ('draft', 'Draft'),
    ('published', 'Published'),
)
```

Add this field to Quiz model (after quiz_type field):
```python
status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', help_text='Quiz can be saved as draft and published later')
```

## 2. Forms.py Changes

In QuizForm Meta fields, add:
```python
'status',
```

In QuizForm Meta widgets, add:
```python
'status': forms.Select(attrs={'class': 'form-control'}),
```

In clean() method, add this validation after the manual and auto validations:
```python
if quiz_type == 'mixed':
    # Mixed quizzes can have both MCQ and Subjective questions
    cleaned_data['question_source'] = 'manual'  # Manual MCQ entry only for mixed
```

## 3. create_quiz.html Changes

Add this HTML after Quiz Type field:
```html
<div class="mb-3">
    <label class="form-label">Status</label>
    {{ form.status }}
    {% if form.status.errors %}
    <div class="text-danger small mt-2">
        {% for error in form.status.errors %}
        <i class="fas fa-exclamation-triangle"></i> {{ error }}<br>
        {% endfor %}
    </div>
    {% endif %}
    <small class="form-text text-muted">Save as Draft or Publish to make it available for students</small>
</div>
```

Add this HTML after manualQuizSection div:
```html
<div id="mixedQuizSection" class="quiz-section quiz-hidden">
    <div class="quiz-section-title">Mixed Quiz Setup</div>
    <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 10px 12px; margin-bottom: 15px; border-radius: 4px;">
        <p style="margin: 0; color: #664d03; font-size: 0.95rem;">
            <i class="fas fa-lightbulb"></i> <strong>Mixed quizzes combine MCQ (auto-graded) and Subjective (manual) questions.</strong> You can add both types on the next page.
        </p>
    </div>
</div>
```

## 4. quiz-create.js Changes

In toggleCreateQuizSections() function:

Add after existing variables:
```javascript
var isMixed = quizTypeEl.value === 'mixed';
var mixedSection = byId('mixedQuizSection');
```

Add after existing section toggles:
```javascript
if (mixedSection) {
    mixedSection.classList.toggle('quiz-hidden', !isMixed);
}
```

## 5. add_questions.html Changes

Update section visibility conditions:

Section 1 header:
```html
{% if quiz.quiz_type == 'manual' or quiz.quiz_type == 'mixed' %}
```

Section 2 header:
```html
{% if quiz.quiz_type == 'auto' or quiz.quiz_type == 'mixed' %}
```

Section 3 header:
```html
{% if quiz.quiz_type == 'manual' or quiz.quiz_type == 'mixed' %}
```

Add after Back to Quizzes button:
```html
<div class="mb-3">
    <label class="form-label">Status</label>
    {{ form.status }}
    {% if form.status.errors %}
    <div class="text-danger small mt-2">
        {% for error in form.status.errors %}
        <i class="fas fa-exclamation-triangle"></i> {{ error }}<br>
        {% endfor %}
    </div>
    {% endif %}
    <small class="form-text text-muted">Save as Draft or Publish to make it available for students</small>
</div>
```

Add these buttons before Back to Quizzes button:
```html
<div style="display: flex; gap: 10px;">
    {% if quiz.status == 'draft' %}
    <form method="post" style="display: inline;">
        {% csrf_token %}
        <input type="hidden" name="form_type" value="save_draft">
        <button type="submit" class="btn btn-outline-secondary">
            <i class="fas fa-save"></i> Save as Draft
        </button>
    </form>
    <form method="post" style="display: inline;">
        {% csrf_token %}
        <input type="hidden" name="form_type" value="publish">
        <button type="submit" class="btn btn-success">
            <i class="fas fa-rocket"></i> Publish Quiz
        </button>
    </form>
    {% else %}
    <span class="badge bg-success" style="padding: 8px 12px; font-size: 0.95rem;">
        <i class="fas fa-check-circle"></i> Published
    </span>
    {% endif %}
</div>
```

## 6. Views.py Changes

In add_questions() function, add these handlers at the start of the POST section:

```python
# Handle draft save
if form_type == 'save_draft':
    quiz.status = 'draft'
    quiz.is_published = False
    quiz.save()
    messages.success(request, 'Quiz saved as draft successfully!')
    return redirect('main:add_questions', quiz_id=quiz.id)

# Handle quiz publish
elif form_type == 'publish':
    if quiz.questions.count() == 0:
        messages.error(request, 'Please add at least one question before publishing.')
        return redirect('main:add_questions', quiz_id=quiz.id)
    quiz.status = 'published'
    quiz.is_published = True
    quiz.save()
    messages.success(request, 'Quiz published successfully! Students can now take the quiz.')
    return redirect('main:manage_quizzes')
```

Update docstring from:
```python
"""Add questions to a quiz - supports auto and manual types"""
```
To:
```python
"""Add questions to a quiz - supports auto, manual, and mixed types"""
```

## 7. Database Migration

The migration file `0028_quiz_status_alter_quiz_quiz_type.py` handles:
- Adding `status` field with default='draft'
- Updating `quiz_type` choices to include 'mixed'

## How to Restore

1. Copy the code snippets from above
2. Apply them to the respective files in the order listed
3. Run: `python manage.py makemigrations main`
4. Run: `python manage.py migrate main`
5. Test the feature at http://localhost:8000/teacher/quizzes/create/

## Features Included

✅ Mixed quiz type (MCQ + Subjective in one quiz)
✅ Draft/Publish workflow
✅ Status field for tracking quiz state
✅ Tab-based sections for different question types
✅ Form validation allowing both question types in mixed quizzes
✅ Helper text and UI indicators
✅ Error messages under each form field
