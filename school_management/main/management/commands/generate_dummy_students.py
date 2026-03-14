import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from faker import Faker

User = get_user_model()
fake = Faker()


class Command(BaseCommand):
    help = 'Generate dummy student data for testing and development'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Delete all existing dummy students before generating new ones',
        )

    def handle(self, *args, **options):
        if options['delete']:
            # Delete all dummy students marked in database (students with 'test' or 'dummy' in email)
            dummy_students = User.objects.filter(role='student', email__icontains='dummy')
            count = dummy_students.count()
            dummy_students.delete()
            self.stdout.write(
                self.style.SUCCESS(f'Deleted {count} existing dummy students')
            )

        try:
            # Generate students for Prep class (5 students, no section)
            self.stdout.write('Generating Prep class students...')
            self.create_students(class_name='Prep', section=None, count=5)

            # Generate students for classes 1-10 with sections A, B, C
            for class_num in range(1, 11):
                for section in ['A', 'B', 'C']:
                    self.stdout.write(f'Generating Class {class_num}{section} students...')
                    self.create_students(class_name=str(class_num), section=section, count=5)

            self.stdout.write(
                self.style.SUCCESS('✓ Successfully generated all dummy students')
            )
            
            # Print summary
            total_students = User.objects.filter(role='student', email__icontains='dummy').count()
            self.stdout.write(
                self.style.SUCCESS(f'Total dummy students created: {total_students}')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error generating dummy students: {str(e)}')
            )

    def create_students(self, class_name, section, count):
        """Create dummy students for a specific class and section"""
        created_count = 0
        
        for i in range(count):
            # Generate a random name
            first_name = fake.first_name()
            last_name = fake.last_name()
            full_name = f"{first_name} {last_name}"
            
            # Generate email based on class and section
            if section:
                email = f"dummy_{first_name.lower()}{last_name.lower()}{class_name}{section}_{i+1}@school.edu.pk"
            else:
                email = f"dummy_{first_name.lower()}{last_name.lower()}{class_name}_{i+1}@school.edu.pk"
            
            # Check if user already exists
            if User.objects.filter(email=email).exists():
                continue
            
            # Generate unique username
            username = f"dummy_{first_name.lower()}{last_name.lower()}_{class_name}"
            if section:
                username += f"_{section}"
            username += f"_{i+1}"
            
            # Ensure username is unique (max 150 chars)
            username = username[:150]
            if User.objects.filter(username=username).exists():
                username = f"dummy_student_{class_name}_{section}_{random.randint(1000, 9999)}"
                username = username[:150]
            
            # Create the student
            user = User.objects.create_user(
                username=username,
                email=email,
                password='Student@123',  # Default password for dummy accounts
                first_name=first_name,
                last_name=last_name,
                role='student',
                status='active',
                student_class=class_name,
                section=section if section else '',
            )
            
            created_count += 1
        
        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'  ✓ Created {created_count} students')
            )
