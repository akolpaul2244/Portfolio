"""
Core models for AkolPaul.dev portfolio.
"""
import json

from django.db import models
from django.utils.text import slugify


class Skill(models.Model):
    CATEGORY_CHOICES = [
        ('language',  'Programming Language'),
        ('framework', 'Framework'),
        ('database',  'Database'),
        ('devops',    'DevOps & Cloud'),
        ('security',  'Security'),
        ('other',     'Other'),
    ]

    name        = models.CharField(max_length=100)
    category    = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    proficiency = models.PositiveSmallIntegerField(default=80)  # 0–100
    icon        = models.CharField(max_length=60, blank=True)   # e.g. "fab fa-python"
    order       = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Experience(models.Model):
    TYPE_INTERNSHIP = 'internship'
    TYPE_CLASS      = 'class'
    TYPE_CHOICES = [
        (TYPE_INTERNSHIP, 'Internship'),
        (TYPE_CLASS,      'Class / Academic'),
    ]

    type        = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_INTERNSHIP)
    company     = models.CharField(max_length=200)
    role        = models.CharField(max_length=150)
    location    = models.CharField(max_length=100, blank=True)
    start_date  = models.DateField()
    end_date    = models.DateField(null=True, blank=True)
    is_current  = models.BooleanField(default=False)
    description = models.TextField()
    tech_stack  = models.CharField(max_length=300, blank=True,
                                   help_text="Comma-separated tech tags, e.g. Django,React,PostgreSQL")

    # Bullet-point achievements stored as one per line.
    # Kept as plain text so the admin stays simple — no JSON editor needed.
    achievements_text = models.TextField(
        blank=True,
        help_text="One achievement per line. Leave blank if none.",
    )

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.role} at {self.company}"

    @property
    def achievements(self) -> list[str]:
        """Return achievements as a clean list, stripping blank lines."""
        return [line.strip() for line in self.achievements_text.splitlines() if line.strip()]

    @property
    def technologies(self) -> list[str]:
        """Return tech_stack as a clean list of tag strings."""
        return [t.strip() for t in self.tech_stack.split(',') if t.strip()]


class Project(models.Model):
    CATEGORY_CHOICES = [
        ('web',          'Web App'),
        ('mobile',       'Mobile'),
        ('ai',           'AI / ML'),
        ('fintech',      'Fintech'),
        ('humanitarian', 'Humanitarian'),
        ('security',     'Security'),
        ('other',        'Other'),
    ]

    title             = models.CharField(max_length=200)
    slug              = models.SlugField(unique=True, blank=True, max_length=220)
    short_description = models.TextField()
    long_description  = models.TextField(blank=True)
    stack             = models.CharField(max_length=300)
    highlight         = models.TextField(blank=True)
    image             = models.ImageField(upload_to='projects/', blank=True, null=True)
    github_link       = models.URLField(blank=True)
    live_link         = models.URLField(blank=True)
    date              = models.DateField()
    featured          = models.BooleanField(default=False)
    order             = models.IntegerField(default=0)
    category          = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='web')
    tags              = models.CharField(
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
    def tag_list(self) -> list[str]:
        """Normalised, de-duplicated list of tags safe for templates and data-* attributes."""
        seen = []
        for raw in self.tags.split(','):
            tag = raw.strip().lower()
            if tag and tag not in seen:
                seen.append(tag)
        return seen

    @property
    def tags_attr(self) -> str:
        """Comma-joined normalised tags ready for a data-* attribute."""
        return ','.join(self.tag_list)


class Testimonial(models.Model):
    name    = models.CharField(max_length=100)
    title   = models.CharField(max_length=150)
    company = models.CharField(max_length=100, blank=True)
    quote   = models.TextField()
    image   = models.ImageField(upload_to='testimonials/', blank=True)
    order   = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class ContactMessage(models.Model):
    """Stores contact form submissions."""
    name         = models.CharField(max_length=100)
    email        = models.EmailField()
    subject      = models.CharField(max_length=200)
    message      = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_read      = models.BooleanField(default=False)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.name} – {self.subject} ({self.submitted_at:%Y-%m-%d})"


class ChatMessage(models.Model):
    session_id         = models.CharField(max_length=100)
    user_message       = models.TextField()
    assistant_response = models.TextField()
    timestamp          = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Chat {self.session_id} @ {self.timestamp:%Y-%m-%d %H:%M}"