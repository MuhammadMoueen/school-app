/**
 * Teacher Dashboard JavaScript
 * Handles sidebar navigation and mobile menu interactions
 */

document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('teacherSidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebarToggleBtn = document.getElementById('sidebarToggleBtn');
    const mobileMenuToggle = document.getElementById('mobileMenuToggle');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    
    // Desktop sidebar toggle (in topbar)
    if (sidebarToggleBtn) {
        sidebarToggleBtn.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
        });
    }
    
    // Desktop sidebar toggle (in sidebar)
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
        });
    }
    
    // Mobile sidebar toggle
    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', function() {
            sidebar.classList.add('mobile-open');
            sidebarOverlay.classList.add('active');
        });
    }
    
    // Close sidebar when clicking overlay
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', function() {
            sidebar.classList.remove('mobile-open');
            sidebarOverlay.classList.remove('active');
        });
    }
});

/**
 * Lecture File Upload - File Preview Functionality
 * Shows file preview with icon based on file type
 */
function initLectureFilePreview() {
    const fileInput = document.querySelector('input[type="file"][name="file"]');
    const filePreview = document.getElementById('filePreview');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const fileIcon = document.getElementById('fileIcon');
    
    if (!fileInput || !filePreview) return;
    
    fileInput.addEventListener('change', function(e) {
        if (this.files && this.files[0]) {
            const file = this.files[0];
            const size = (file.size / 1024 / 1024).toFixed(2); // Size in MB
            
            fileName.textContent = file.name;
            fileSize.textContent = `Size: ${size} MB`;
            filePreview.classList.add('show');
            
            // Update icon based on file type
            const ext = file.name.split('.').pop().toLowerCase();
            if (['mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'webm'].includes(ext)) {
                fileIcon.className = 'fas fa-file-video';
            } else if (['pdf'].includes(ext)) {
                fileIcon.className = 'fas fa-file-pdf';
            } else if (['doc', 'docx', 'txt', 'rtf'].includes(ext)) {
                fileIcon.className = 'fas fa-file-word';
            } else if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp'].includes(ext)) {
                fileIcon.className = 'fas fa-file-image';
            } else if (['mp3', 'wav', 'ogg', 'm4a', 'flac'].includes(ext)) {
                fileIcon.className = 'fas fa-file-audio';
            } else {
                fileIcon.className = 'fas fa-file';
            }
        }
    });
}

/**
 * Transcript Grade Calculator
 * Auto-calculates grade based on marks obtained and total marks
 * Grade Scale: A(85-100), B(70-84), C(55-69), D(40-54), F(<40)
 */
function calculateGrade() {
    const marksObtainedField = document.getElementById('id_marks_obtained');
    const totalMarksField = document.getElementById('id_total_marks');
    const gradeField = document.getElementById('id_grade');
    
    if (!marksObtainedField || !totalMarksField || !gradeField) return;
    
    const marksObtained = parseFloat(marksObtainedField.value) || 0;
    const totalMarks = parseFloat(totalMarksField.value) || 100;
    
    if (totalMarks <= 0) {
        gradeField.value = 'F';
        return;
    }
    
    const percentage = (marksObtained / totalMarks) * 100;
    
    // Grade calculation: 85-100=A, 70-84=B, 55-69=C, 40-54=D, <40=F
    let grade;
    if (percentage >= 85) {
        grade = 'A';
    } else if (percentage >= 70) {
        grade = 'B';
    } else if (percentage >= 55) {
        grade = 'C';
    } else if (percentage >= 40) {
        grade = 'D';
    } else {
        grade = 'F';
    }
    
    gradeField.value = grade;
}

/**
 * Initialize Transcript Form Grade Calculator
 * Adds event listeners to marks fields for auto-calculation
 */
function initTranscriptGradeCalculator() {
    const marksObtainedField = document.getElementById('id_marks_obtained');
    const totalMarksField = document.getElementById('id_total_marks');
    
    if (marksObtainedField) {
        marksObtainedField.addEventListener('input', calculateGrade);
        marksObtainedField.addEventListener('change', calculateGrade);
    }
    
    if (totalMarksField) {
        totalMarksField.addEventListener('input', calculateGrade);
        totalMarksField.addEventListener('change', calculateGrade);
    }
    
    // Calculate grade on page load if values exist
    calculateGrade();
}

/**
 * Lecture Delete Confirmation
 * Shows confirmation dialog before deleting a lecture
 */
function confirmDeleteLecture(lectureTitle) {
    return confirm(`Are you sure you want to delete the lecture "${lectureTitle}"?\n\nThis action cannot be undone.`);
}

/**
 * Initialize all teacher panel functionality
 * Call this on DOMContentLoaded
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize lecture file preview if on lecture upload/edit page
    initLectureFilePreview();
    
    // Initialize transcript grade calculator if on transcript form page
    initTranscriptGradeCalculator();
});
