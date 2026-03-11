/**
 * Teacher Dashboard JavaScript
 * Handles sidebar navigation and mobile menu interactions
 */

// Global click handler to close dropdowns - runs immediately
document.addEventListener('click', function(e) {
    const profileDropdown = document.getElementById('profileDropdown');
    const notificationDropdown = document.getElementById('notificationDropdown');
    
    // Close all dropdowns when clicking anywhere (unless click is inside them)
    if (profileDropdown && !e.target.closest('.profile-section')) {
        profileDropdown.classList.remove('show');
    }
    if (notificationDropdown && !e.target.closest('.notification-section')) {
        notificationDropdown.classList.remove('show');
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('teacherSidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebarToggleBtn = document.getElementById('sidebarToggleBtn');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    
    // Check if we're on mobile
    function isMobile() {
        return window.innerWidth <= 1024;
    }
    
    // Mobile/Desktop sidebar toggle (hamburger in topbar)
    if (sidebarToggleBtn) {
        sidebarToggleBtn.addEventListener('click', function() {
            if (isMobile()) {
                sidebar.classList.toggle('mobile-open');
                sidebarOverlay.classList.toggle('active');
            }
        });
    }
    
    // Sidebar internal toggle (for mobile)
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            if (isMobile()) {
                sidebar.classList.remove('mobile-open');
                sidebarOverlay.classList.remove('active');
            }
        });
    }
    
    // Close sidebar when clicking overlay (mobile only)
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', function() {
            sidebar.classList.remove('mobile-open');
            sidebarOverlay.classList.remove('active');
        });
    }
    
    // Handle window resize
    window.addEventListener('resize', function() {
        if (!isMobile()) {
            // On desktop, remove mobile classes
            sidebar.classList.remove('mobile-open');
            sidebarOverlay.classList.remove('active');
        }
    });
    
    // Profile and Notification Dropdowns - Simplified and Fixed
    const profileIcon = document.getElementById('profileIcon');
    const profileDropdown = document.getElementById('profileDropdown');
    const notificationIcon = document.getElementById('notificationIcon');
    const notificationDropdown = document.getElementById('notificationDropdown');
    
    console.log('=== DROPDOWN INITIALIZATION ===');
    console.log('Profile Icon found:', !!profileIcon);
    console.log('Profile Dropdown found:', !!profileDropdown);
    console.log('Notification Icon found:', !!notificationIcon);
    console.log('Notification Dropdown found:', !!notificationDropdown);
    
    // Test if clicks work anywhere on page
    document.body.addEventListener('click', function(e) {
        console.log('BODY CLICK detected at:', e.target);
    }, true);
    
    // Profile Icon Click Handler
    if (profileIcon && profileDropdown) {
        profileIcon.style.cursor = 'pointer';
        
        profileIcon.addEventListener('click', function(event) {
            event.stopPropagation();
            event.preventDefault();
            console.log('✅ PROFILE ICON CLICKED!');
            
            const isVisible = profileDropdown.classList.contains('show');
            console.log('Dropdown visible before toggle:', isVisible);
            
            profileDropdown.classList.toggle('show');
            
            console.log('Dropdown visible after toggle:', profileDropdown.classList.contains('show'));
            
            // Close notification if open
            if (notificationDropdown) {
                notificationDropdown.classList.remove('show');
            }
        }, false);
        
        console.log('✓ Profile click handler attached');
    } else {
        console.error('❌ Profile elements missing!', {profileIcon, profileDropdown});
    }
    
    // Notification Icon Click Handler
    if (notificationIcon && notificationDropdown) {
        notificationIcon.style.cursor = 'pointer';
        
        notificationIcon.addEventListener('click', function(event) {
            event.stopPropagation();
            event.preventDefault();
            console.log('✅ NOTIFICATION ICON CLICKED!');
            
            const isVisible = notificationDropdown.classList.contains('show');
            console.log('Dropdown visible before toggle:', isVisible);
            
            notificationDropdown.classList.toggle('show');
            
            console.log('Dropdown visible after toggle:', notificationDropdown.classList.contains('show'));
            
            // Close profile if open
            if (profileDropdown) {
                profileDropdown.classList.remove('show');
            }
            
            // Load notifications
            if (notificationDropdown.classList.contains('show')) {
                loadNotifications();
            }
        }, false);
        
        console.log('✓ Notification click handler attached');
    } else {
        console.error('❌ Notification elements missing!', {notificationIcon, notificationDropdown});
    }
    
    // Close dropdowns when clicking outside
    document.addEventListener('click', function(event) {
        const profileDropdown = document.getElementById('profileDropdown');
        const notificationDropdown = document.getElementById('notificationDropdown');
        const profileIcon = document.getElementById('profileIcon');
        const notificationIcon = document.getElementById('notificationIcon');
        
        // Close profile dropdown if clicking outside
        if (profileDropdown && profileIcon) {
            if (!profileIcon.contains(event.target) && !profileDropdown.contains(event.target)) {
                profileDropdown.classList.remove('show');
            }
        }
        
        // Close notification dropdown if clicking outside
        if (notificationDropdown && notificationIcon) {
            if (!notificationIcon.contains(event.target) && !notificationDropdown.contains(event.target)) {
                notificationDropdown.classList.remove('show');
            }
        }
    });
    
    // Load notifications via AJAX
    function loadNotifications() {
        const notificationList = document.getElementById('notificationList');
        if (!notificationList) return;
        
        // Show loading state
        notificationList.innerHTML = `
            <div class="notification-empty">
                <i class="fas fa-spinner fa-spin"></i>
                <p>Loading notifications...</p>
            </div>
        `;
        
        // Fetch notifications
        fetch('/get-notifications/')
            .then(response => response.json())
            .then(data => {
                if (data.notifications && data.notifications.length > 0) {
                    notificationList.innerHTML = data.notifications.map(notif => `
                        <a href="${notif.link}" class="notification-item ${notif.is_read ? '' : 'unread'}">
                            <div class="notification-sender">
                                <i class="fas fa-user-circle"></i>
                                ${notif.sender}
                            </div>
                            <div class="notification-message">${notif.message}</div>
                            <div class="notification-time">
                                <i class="far fa-clock"></i> ${notif.time_ago}
                            </div>
                        </a>
                    `).join('');
                } else {
                    notificationList.innerHTML = `
                        <div class="notification-empty">
                            <i class="fas fa-inbox"></i>
                            <p>No notifications yet</p>
                        </div>
                    `;
                }
            })
            .catch(error => {
                console.error('Error loading notifications:', error);
                notificationList.innerHTML = `
                    <div class="notification-empty">
                        <i class="fas fa-exclamation-triangle"></i>
                        <p>Failed to load notifications</p>
                    </div>
                `;
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
