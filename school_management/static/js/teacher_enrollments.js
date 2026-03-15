document.addEventListener('DOMContentLoaded', function() {
    const endpointScript = document.querySelector('script[data-student-endpoint]');
    const endpoint = endpointScript ? endpointScript.dataset.studentEndpoint : '';

    const courseSelect = document.querySelector('select[name="course"]');
    const studentsSelect = document.querySelector('select[name="students"]');
    const messageElement = document.getElementById('student-filter-message');

    if (!endpoint || !courseSelect || !studentsSelect || !messageElement) {
        return;
    }

    const selectedStudents = new Set(Array.from(studentsSelect.options)
        .filter(function(option) { return option.selected; })
        .map(function(option) { return option.value; }));

    function setMessage(text, isError) {
        messageElement.textContent = text;
        messageElement.classList.toggle('is-error', !!isError);
    }

    function resetStudents(placeholder) {
        studentsSelect.innerHTML = '';
        const option = document.createElement('option');
        option.disabled = true;
        option.textContent = placeholder;
        studentsSelect.appendChild(option);
    }

    function loadStudents(courseId) {
        if (!courseId) {
            studentsSelect.disabled = true;
            resetStudents('Select a subject first');
            setMessage('Select a subject to load students from the matching class and section.', false);
            return;
        }

        studentsSelect.disabled = true;
        resetStudents('Loading students...');
        setMessage('Loading students for the selected class and section...', false);

        fetch(endpoint + '?course_id=' + encodeURIComponent(courseId))
            .then(function(response) {
                if (!response.ok) {
                    throw new Error('Failed to load students.');
                }
                return response.json();
            })
            .then(function(data) {
                studentsSelect.innerHTML = '';

                if (!data.students || !data.students.length) {
                    studentsSelect.disabled = true;
                    resetStudents('No students available');
                    setMessage(data.message || 'No students found for this class and section.', true);
                    return;
                }

                data.students.forEach(function(student) {
                    const option = document.createElement('option');
                    option.value = student.id;
                    option.textContent = student.roll_number ? (student.name + ' (' + student.roll_number + ')') : student.name;
                    option.selected = selectedStudents.has(String(student.id));
                    studentsSelect.appendChild(option);
                });

                studentsSelect.disabled = false;
                setMessage('Only students from the selected class and section are shown.', false);
            })
            .catch(function() {
                studentsSelect.disabled = true;
                resetStudents('Unable to load students');
                setMessage('Unable to load students right now. Please try again.', true);
            });
    }

    courseSelect.addEventListener('change', function() {
        selectedStudents.clear();
        loadStudents(this.value);
    });

    loadStudents(courseSelect.value);
});
