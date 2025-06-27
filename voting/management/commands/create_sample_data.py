from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import models
from voting.models import Person, Category, VotingCode


class Command(BaseCommand):
    help = 'Create sample data for testing the voting system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--codes',
            type=int,
            default=5,
            help='Number of voting codes to generate (default: 5)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating sample data...'))

        # Create sample persons
        sample_names = [
            'Anna Schmidt', 'Max Müller', 'Lisa Weber', 'Tom Fischer', 
            'Sarah Klein', 'Jan Becker', 'Emma Wagner', 'Lukas Schulz', 
            'Mia Hoffmann', 'Felix Richter', 'Julia Braun', 'David König',
            'Laura Zimmermann', 'Niklas Wolf', 'Sophia Krüger'
        ]

        persons_created = 0
        for name in sample_names:
            person, created = Person.objects.get_or_create(name=name)
            if created:
                persons_created += 1

        self.stdout.write(
            self.style.SUCCESS(f'✓ Created {persons_created} new persons (Total: {Person.objects.count()})')
        )

        # Create sample categories
        sample_categories = [
            ('Klassensprecher/in', 'Wer soll unser/e nächste/r Klassensprecher/in werden?'),
            ('Lustigste Person', 'Wer bringt die Klasse am meisten zum Lachen?'),
            ('Hilfsbereiteste Person', 'Wer hilft anderen am meisten?'),
            ('Sportlichste Person', 'Wer ist am sportlichsten in der Klasse?'),
            ('Kreativste Person', 'Wer hat die besten kreativen Ideen?'),
            ('Zuverlässigste Person', 'Auf wen kann man sich am besten verlassen?'),
            ('Beste/r Freund/in', 'Wer ist der/die beste Freund/in?'),
        ]

        categories_created = 0
        for title, description in sample_categories:
            category, created = Category.objects.get_or_create(
                title=title,
                defaults={'description': description}
            )
            if created:
                categories_created += 1

        self.stdout.write(
            self.style.SUCCESS(f'✓ Created {categories_created} new categories (Total: {Category.objects.count()})')
        )

        # Create voting codes
        try:
            admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                self.stdout.write(
                    self.style.WARNING('No admin user found. Creating default admin user...')
                )
                admin_user = User.objects.create_superuser(
                    username='admin',
                    email='admin@example.com',
                    password='admin123'
                )
                self.stdout.write(
                    self.style.SUCCESS('✓ Created admin user (username: admin, password: admin123)')
                )

            codes_to_create = options['codes']
            existing_codes = VotingCode.objects.filter(is_active=True).count()
            
            if existing_codes >= codes_to_create:
                self.stdout.write(
                    self.style.WARNING(f'Already have {existing_codes} active codes. Skipping code generation.')
                )
            else:
                codes_created = 0
                generated_codes = []
                
                for _ in range(codes_to_create):
                    code = VotingCode.generate_code(admin_user)
                    generated_codes.append(code.code)
                    codes_created += 1

                self.stdout.write(
                    self.style.SUCCESS(f'✓ Generated {codes_created} new voting codes')
                )
                
                self.stdout.write('\nGenerated codes:')
                for code in generated_codes:
                    self.stdout.write(f'  • {code}')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating voting codes: {e}')
            )

        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('SAMPLE DATA CREATION COMPLETE'))
        self.stdout.write('='*50)
        self.stdout.write(f'Persons: {Person.objects.count()}')
        self.stdout.write(f'Categories: {Category.objects.count()}')
        self.stdout.write(f'Active Voting Codes: {VotingCode.objects.filter(is_active=True).count()}')
        self.stdout.write(f'Total Votes: {VotingCode.objects.aggregate(total=models.Sum("current_uses"))["total"] or 0}')
        
        self.stdout.write('\nNext steps:')
        self.stdout.write('1. Start the server: python manage.py runserver')
        self.stdout.write('2. Visit: http://localhost:8000/')
        self.stdout.write('3. Admin panel: http://localhost:8000/admin/')
        self.stdout.write('4. Results: http://localhost:8000/results/')
        
        if admin_user.username == 'admin':
            self.stdout.write('\nAdmin credentials:')
            self.stdout.write('  Username: admin')
            self.stdout.write('  Password: admin123')

