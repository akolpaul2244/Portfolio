"""
Core models for AkolPaul.dev portfolio.
"""
from django.db import models
from django.utils.text import slugify


class Skill(models.Model):
    CATEGORY_CHOICES = [
        ('language', 'Programming Language'),
        ('framework', 'Framework'),
        ('database', 'Database'),
        ('devops', 'DevOps & Cloud'),
        ('security', 'Security'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    proficiency = models.PositiveSmallIntegerField(default=80)  # 0–100
    icon = models.CharField(max_length=60, blank=True)  # e.g. "fab fa-python"
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Experience(models.Model):
    company = models.CharField(max_length=200)
    role = models.CharField(max_length=150)
    location = models.CharField(max_length=100, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    description = models.TextField()
    tech_stack = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.role} at {self.company}"


class Project(models.Model):
    CATEGORY_CHOICES = [
        ('web', 'Web App'),
        ('mobile', 'Mobile'),
        ('ai', 'AI / ML'),
        ('fintech', 'Fintech'),
        ('humanitarian', 'Humanitarian'),
        ('security', 'Security'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True, max_length=220)
    short_description = models.TextField()
    long_description = models.TextField(blank=True)
    stack = models.CharField(max_length=300)
    highlight = models.TextField(blank=True)
    image = models.ImageField(upload_to='projects/', blank=True, null=True)
    github_link = models.URLField(blank=True)
    live_link = models.URLField(blank=True)
    date = models.DateField()
    featured = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='web')

    
    tags = models.CharField(
        max_length=200,
        blank=True,
        help_text="Comma-separated filter tags, e.g. ai,fintech,realtime",
    )

    class Meta:
        ordering = ['order', '-date']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def tag_list(self):
        """
        Normalized list of tags: lowercase, trimmed, de-duplicated, empty
        entries dropped. Safe to use directly in templates and avoids every
        consumer having to re-clean the raw `tags` string.
        """
        seen = []
        for raw in self.tags.split(','):
            tag = raw.strip().lower()
            if tag and tag not in seen:
                seen.append(tag)
        return seen

    @property
    def tags_attr(self):
        """Comma-joined normalized tags, ready to drop into a data-* attribute."""
        return ','.join(self.tag_list)


class Testimonial(models.Model):
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=150)
    company = models.CharField(max_length=100, blank=True)
    quote = models.TextField()
    image = models.ImageField(upload_to='testimonials/', blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class ContactMessage(models.Model):
    """Stores contact form submissions."""
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.name} – {self.subject} ({self.submitted_at:%Y-%m-%d})"


class ChatMessage(models.Model):
    session_id = models.CharField(max_length=100)
    user_message = models.TextField()
    assistant_response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Chat {self.session_id} @ {self.timestamp:%Y-%m-%d %H:%M}"