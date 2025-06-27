from django.db import models
from django.contrib.auth.models import User
import uuid
import string
import random


class Person(models.Model):
    """Predefined names that can be voted for"""
    name = models.CharField(max_length=100, unique=True)
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Auto-populate first_name and last_name from name if not set
        if not self.first_name and not self.last_name and self.name:
            name_parts = self.name.strip().split()
            if len(name_parts) >= 2:
                self.first_name = name_parts[0]
                self.last_name = ' '.join(name_parts[1:])
            else:
                self.first_name = self.name
                self.last_name = ''
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['first_name', 'last_name']


class Category(models.Model):
    """Voting categories with text and image"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['title']


class VotingCode(models.Model):
    """Admin-generated codes for voting access"""
    code = models.CharField(max_length=20, unique=True)
    max_uses = models.IntegerField(default=2)
    current_uses = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    # NEU: Feld für die E-Mail-Adresse hinzugefügt
    email = models.EmailField(max_length=254, blank=True, null=True, help_text="Email this code was sent to, if any.")

    def __str__(self):
        return f"{self.code} ({self.current_uses}/{self.max_uses})"

    def can_vote(self):
        return self.is_active and self.current_uses < self.max_uses

    def use_code(self):
        if self.can_vote():
            self.current_uses += 1
            self.save()
            return True
        return False

    @classmethod
    def generate_code(cls, user, length=8, max_uses=2, email=None):
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
            if not cls.objects.filter(code=code).exists():
                return cls.objects.create(
                    code=code,
                    created_by=user,
                    max_uses=max_uses,
                    email=email
                )


class VotingSession(models.Model):

    voting_code = models.ForeignKey(VotingCode, on_delete=models.CASCADE)

    pending_votes = models.JSONField(default=dict, blank=True)

    current_category_index = models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # A voting code should only have one active session.
        unique_together = ['voting_code']

    def __str__(self):
        status = "Completed" if self.is_completed else f"Step {self.current_category_index + 1}"
        return f"Session for {self.voting_code.code} ({status})"

    def get_categories(self):
        return list(Category.objects.filter(is_active=True).order_by('title'))

    def get_current_category(self):
        categories = self.get_categories()
        if 0 <= self.current_category_index < len(categories):
            return categories[self.current_category_index]
        return None

    def add_vote(self, category_id, person_id):
        self.pending_votes[str(category_id)] = person_id
        self.save(update_fields=['pending_votes', 'updated_at'])

    def advance_category(self):
        self.current_category_index += 1
        self.save(update_fields=['current_category_index', 'updated_at'])

    def regress_category(self):
        if self.current_category_index > 0:
            self.current_category_index -= 1
            self.save(update_fields=['current_category_index', 'updated_at'])

    def is_final_category(self):
        return self.current_category_index >= len(self.get_categories()) - 1

    def complete_voting(self):

        from django.db import transaction

        all_categories = self.get_categories()
        if self.is_completed or len(self.pending_votes) != len(all_categories):
            return False

        try:
            with transaction.atomic():
                for category_id, person_id in self.pending_votes.items():
                    Vote.objects.create(
                        voting_code=self.voting_code,
                        category_id=category_id,
                        person_id=person_id,
                        ip_address=self.ip_address,
                        user_agent=self.user_agent
                    )

                self.voting_code.use_code()

                self.is_completed = True
                self.save(update_fields=['is_completed', 'updated_at'])

            for category in all_categories:
                update_vote_statistics(category)

            return True
        except Exception:
            # In case of any error during the transaction, it will be rolled back.
            # You might want to log the exception here.
            return False


class Vote(models.Model):
    """Individual votes cast"""
    voting_code = models.ForeignKey(VotingCode, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.person.name} in {self.category.title} (Code: {self.voting_code.code})"

    class Meta:
        unique_together = ['voting_code', 'category']
        ordering = ['-created_at']


def update_vote_statistics(category):
    from django.db.models import Count
    votes = Vote.objects.filter(category=category).values('person').annotate(count=Count('person'))
    total_votes = Vote.objects.filter(category=category).count()
    VoteStatistics.objects.filter(category=category).delete()
    for vote_data in votes:
        person_id = vote_data['person']
        vote_count = vote_data['count']
        percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0

        VoteStatistics.objects.create(
            category=category,
            person_id=person_id,
            vote_count=vote_count,
            percentage=round(percentage, 2)
        )


class VoteStatistics(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    vote_count = models.IntegerField(default=0)
    percentage = models.FloatField(default=0.0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.person.name} in {self.category.title}: {self.vote_count} votes ({self.percentage}%)"

    class Meta:
        unique_together = ['category', 'person']
        ordering = ['-vote_count']