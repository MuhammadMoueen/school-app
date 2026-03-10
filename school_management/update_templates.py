# Update Admin Templates - Remove Inline CSS/JS
# This script replaces inline styles and scripts with external file references

import re
import os

TEMPLATES_DIR = r'c:\Users\muham\OneDrive\Desktop\school-app\school_management\templates\admin'

def update_template(filepath):
    """Update a single template file to use external CSS/JS"""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Replace inline CSS block with external stylesheet reference
    css_pattern = r'{%\s*block\s+extra_css\s*%}.*?</style>\s*{%\s*endblock\s*%}'
    css_replacement = '{% block extra_css %}\n<link rel="stylesheet" href="{% static \'css/admin.css\' %}">\n{% endblock %}'
    content = re.sub(css_pattern, css_replacement, content, flags=re.DOTALL)
    
    # Write back if changed
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Updated: {os.path.basename(filepath)}")
        return True
    else:
        print(f"- Skipped: {os.path.basename(filepath)} (no changes)")
        return False

def main():
    """Process all admin template files"""
    
    print("=" * 60)
    print("UPDATING ADMIN TEMPLATES")
    print("=" * 60)
    print()
    
    templates = [
        'admin_dashboard.html',
        'admin_statistics.html',
        'admin_search_users.html',
        'admin_manage_students.html',
        'admin_create_student.html',
        'admin_create_teacher.html',
        'admin_edit_user.html',
        'admin_bulk_import.html',
        'admin_confirm_delete_teacher.html',
        'admin_edit_course.html',
        'admin_manage_courses.html',
        'admin_view_teachers.html',
        'admin_students_hub.html',
        'admin_teachers_hub.html',
        'admin_courses_hub.html',
    ]
    
    updated_count = 0
    
    for template in templates:
        filepath = os.path.join(TEMPLATES_DIR, template)
        if os.path.exists(filepath):
            if update_template(filepath):
                updated_count += 1
        else:
            print(f"✗ Not found: {template}")
    
    print()
    print("=" * 60)
    print(f"SUMMARY: {updated_count} files updated")
    print("=" * 60)

if __name__ == '__main__':
    main()
