import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_management.settings')
django.setup()

from main.models import User

# Check status of students
active_students = User.objects.filter(role='student', status='active').count()
dummy_students = User.objects.filter(role='student', email__icontains='dummy').count()
total_students = User.objects.filter(role='student').count()

print(f'Total students: {total_students}')
print(f'Active students: {active_students}')
print(f'Dummy students: {dummy_students}')

# Check a sample dummy student
sample = User.objects.filter(role='student', email__icontains='dummy').first()
if sample:
    print(f'\nSample dummy student:')
    print(f'  Name: {sample.get_full_name()}')
    print(f'  Email: {sample.email}')
    print(f'  Username: {sample.username}')
    print(f'  Class: {sample.student_class}')
    print(f'  Section: {sample.section}')
    print(f'  Status: {sample.status}')
    print(f'  Status Display: {sample.get_status_display()}')
