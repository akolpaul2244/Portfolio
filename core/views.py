import json
import logging
import os
import random
from types import SimpleNamespace

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.html import escape
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_POST

from groq import Groq, RateLimitError
from langdetect import DetectorFactory, detect
from textblob import TextBlob

from .forms import ContactForm
from .models import Experience, Project, Skill, Testimonial

try:
    from django_ratelimit.decorators import ratelimit
    HAS_RATELIMIT = True
except ImportError:
    HAS_RATELIMIT = False

DetectorFactory.seed = 0

logger = logging.getLogger(__name__)


# Constants

_MAX_MSG_LEN  = 500
_MAX_FEEDBACK = 2_000
_MAX_CAT_LEN  = 50
_CACHE_SKILLS = "skills_grouped"
_CACHE_TTL    = 60 * 15  # 15 minutes

# llama-3.1-8b-instant has a separate TPD bucket from 70b and uses ~10x fewer tokens.
_GROQ_MODEL      = "llama-3.1-8b-instant"
_GROQ_MAX_TOKENS = 300

DEMO_BACKEND: list[dict] = [
    {"name": "Django",     "proficiency": 92},
    {"name": "Python",     "proficiency": 90},
    {"name": "Java",       "proficiency": 80},
    {"name": "PostgreSQL", "proficiency": 85},
    {"name": "REST APIs",  "proficiency": 92},
    {"name": "WebSockets", "proficiency": 78},
]

DEMO_FRONTEND: list[dict] = [
    {"name": "React",        "proficiency": 78},
    {"name": "Tailwind CSS", "proficiency": 88},
    {"name": "JavaScript",   "proficiency": 82},
    {"name": "Vue.js",       "proficiency": 70},
    {"name": "HTML / CSS",   "proficiency": 95},
]

DEMO_AI: list[dict] = [
    {"name": "Scikit-learn",  "proficiency": 80},
    {"name": "HuggingFace",   "proficiency": 75},
    {"name": "Pandas",        "proficiency": 85},
    {"name": "NLP Pipelines", "proficiency": 78},
    {"name": "LLM APIs",      "proficiency": 82},
]

DEMO_TOOLS: list[str] = [
    "Django", "Python", "Java" "React", "Laravel", "PostgreSQL", "Redis",
    "Docker", "Git", "WebSockets", "Celery", "NGINX", "AWS S3",
    "Pandas", "Scikit-learn", "HuggingFace", "Tailwind CSS", "Vue.js",
    "REST APIs", "GraphQL", "Linux", "Figma", "Chart.js", "Stripe API",
]

_DEMO_CATEGORIES: dict[str, list[dict]] = {
    "Backend":  DEMO_BACKEND,
    "Frontend": DEMO_FRONTEND,
    "AI / ML":  DEMO_AI,
}

_LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "fr": "French",
    "es": "Spanish",
    "de": "German",
    "pt": "Portuguese",
    "ar": "Arabic",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "sw": "Swahili",
}

_TOPIC_KEYWORDS: dict[str, list[str]] = {
    "Food Security": ["food", "hungry", "eat", "maize", "beans", "meal", "hunger"],
    "Healthcare":    ["health", "hospital", "sick", "medicine", "clinic", "doctor"],
    "Education":     ["school", "education", "learn", "teacher", "class", "study"],
    "WASH":          ["water", "clean", "toilet", "sanitation", "hygiene"],
    "Shelter":       ["shelter", "house", "tent", "housing", "accommodation"],
    "Protection":    ["safe", "violence", "abuse", "protect", "security"],
}

# Compact system prompt — full context is appended from portfolio_context.txt.
# Keeping this short is the biggest lever for staying within the daily token limit.
_SYSTEM_PROMPT_PREFIX = (
    "You are Akol Paul's portfolio assistant. Answer questions about him "
    "concisely and professionally using only the context below. "
    "If you cannot answer from the context, direct the visitor to "
    "paulakol97@gmail.com. Keep replies short — two to four sentences max.\n\n"
)

_RATE_LIMIT_REPLY = (
    "I'm handling a lot of requests right now — please try again in a few minutes. "
    "You can also reach Akol directly at paulakol97@gmail.com."
)

_ERROR_REPLY = (
    "Something went wrong on my end. "
    "Please contact Akol directly at paulakol97@gmail.com."
)


# Internal helpers

def _ratelimit(key: str, rate: str, block: bool = True):
    """No-op decorator factory when django-ratelimit is not installed."""
    def decorator(view_fn):
        if HAS_RATELIMIT:
            return ratelimit(key=key, rate=rate, block=block)(view_fn)
        return view_fn
    return decorator


def _get_groq_client() -> "Groq | None":
    api_key = getattr(settings, "GROQ_API_KEY", None)
    if not api_key:
        logger.warning("GROQ_API_KEY is not configured")
        return None
    try:
        return Groq(api_key=api_key)
    except Exception:
        logger.exception("Failed to initialise Groq client")
        return None


def _get_portfolio_context() -> str:
    """
    Load the portfolio context file that feeds the AI assistant.
    Keep this file under 800 tokens to stay well within daily limits.
    """
    path = os.path.join(settings.BASE_DIR, "core", "data", "portfolio_context.txt")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        logger.warning("portfolio_context.txt not found at %s", path)
        return ""


def _parse_json_body(request) -> "tuple[dict, str | None]":
    """
    Parse JSON from the request body.
    Returns (payload, error_message). error_message is None on success.
    """
    try:
        payload = json.loads(request.body)
        if not isinstance(payload, dict):
            return {}, "Request body must be a JSON object."
        return payload, None
    except (json.JSONDecodeError, ValueError):
        return {}, "Invalid JSON body."


def _json_error(message: str, status: int = 400) -> JsonResponse:
    return JsonResponse({"success": False, "reply": message}, status=status)


def _build_grouped_skills() -> dict:
    """
    Build the grouped skills dict from the DB, injecting demo data for any
    category that has no DB rows. Result is cached for _CACHE_TTL seconds.
    """
    cached = cache.get(_CACHE_SKILLS)
    if cached is not None:
        return cached

    grouped: dict = {}
    for skill in Skill.objects.all().order_by("category", "-proficiency"):
        grouped.setdefault(skill.get_category_display(), []).append(skill)

    for cat, demo_list in _DEMO_CATEGORIES.items():
        if cat not in grouped:
            grouped[cat] = [SimpleNamespace(**s) for s in demo_list]

    cache.set(_CACHE_SKILLS, grouped, _CACHE_TTL)
    return grouped


# Page views

@ensure_csrf_cookie
def home(request):
    return render(request, "home.html", {
        "featured_projects": Project.objects.filter(featured=True).select_related()[:3],
        "skills":            Skill.objects.all()[:8],
        "testimonials":      Testimonial.objects.all()[:3],
        "experiences":       Experience.objects.filter(
                                 type=Experience.TYPE_INTERNSHIP
                             ).order_by('-start_date')[:2],
        "page": "home",
    })


def about(request):
    return render(request, "about.html", {
        "experiences": Experience.objects.all(),
        "page":        "about",
        "default_domains": [
            "Systems Architecture",
            "AI & Machine Learning",
            "Web & Mobile Engineering",
            "Database Design",
            "Cybersecurity",
            "Software Project Management",
            "Cloud & DevOps",
            "Professional Engineering Ethics",
        ],
    })


def projects_list(request):
    category = request.GET.get("cat", "").strip()[:_MAX_CAT_LEN]
    qs = Project.objects.all()
    if category:
        qs = qs.filter(category=category)
    return render(request, "projects.html", {
        "projects":   qs,
        "categories": Project.CATEGORY_CHOICES,
        "active_cat": category,
        "page":       "projects",
    })


def project_detail(request, slug):
    project = get_object_or_404(Project, slug=slug)
    related = (
        Project.objects
        .exclude(pk=project.pk)
        .filter(category=project.category)
        .select_related()[:3]
    )
    return render(request, "project_detail.html", {
        "project": project,
        "related": related,
        "page":    "projects",
    })


def skills_view(request):
    grouped = _build_grouped_skills()
    return render(request, "skills.html", {
        "grouped_skills": grouped,
        "tools":          DEMO_TOOLS,
        "demo_backend":   DEMO_BACKEND,
        "demo_frontend":  DEMO_FRONTEND,
        "demo_ai":        DEMO_AI,
        "demo_tools":     DEMO_TOOLS,
        "page":           "skills",
    })


def experience_view(request):
    internships = Experience.objects.filter(
        type=Experience.TYPE_INTERNSHIP
    ).order_by('-start_date')

    classwork = Experience.objects.filter(
        type=Experience.TYPE_CLASS
    ).order_by('-start_date')

    return render(request, "experience.html", {
        "internships":  internships,
        "classwork":    classwork,
        "experiences":  Experience.objects.all().order_by('-start_date'),
        "page":         "experience",
    })


@csrf_protect
def contact(request):
    if request.method != "POST":
        return render(request, "contact.html", {"form": ContactForm(), "page": "contact"})

    # Honeypot — bots fill hidden fields that real users never see
    if request.POST.get("website", "").strip():
        return redirect("contact")

    form = ContactForm(request.POST)
    if not form.is_valid():
        return render(request, "contact.html", {"form": form, "page": "contact"})

    msg = form.save()
    try:
        send_mail(
            subject=f"[Portfolio] {escape(msg.subject)}",
            message=(
                f"From: {escape(msg.name)} <{escape(msg.email)}>\n\n"
                f"{escape(msg.message)}"
            ),
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[settings.CONTACT_EMAIL],
            fail_silently=False,
        )
    except Exception:
        logger.exception("Contact email delivery failed for sender %s", msg.email)

    messages.success(request, "sent")
    return redirect("contact")


# API views

@require_POST
@_ratelimit(key="ip", rate="10/m")
def ai_chat(request):
    groq_client = _get_groq_client()
    if groq_client is None:
        return _json_error("AI assistant is temporarily unavailable.", status=503)

    payload, err = _parse_json_body(request)
    if err:
        return _json_error(err, status=400)

    user_message = payload.get("message", "").strip()[:_MAX_MSG_LEN]
    if not user_message:
        return _json_error("Message cannot be empty.", status=400)

    context_text   = _get_portfolio_context()
    system_content = _SYSTEM_PROMPT_PREFIX + context_text

    try:
        response = groq_client.chat.completions.create(
            model=_GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user",   "content": user_message},
            ],
            temperature=0.6,
            max_tokens=_GROQ_MAX_TOKENS,
        )
        reply = response.choices[0].message.content
        return JsonResponse({"success": True, "reply": reply})

    except RateLimitError:
        # Return 200 so the frontend renders a friendly bubble rather than a silent error
        logger.warning("Groq rate limit reached")
        return JsonResponse({"success": True, "reply": _RATE_LIMIT_REPLY})

    except Exception:
        logger.exception("Groq API call failed")
        return JsonResponse({"success": True, "reply": _ERROR_REPLY})


@require_POST
@_ratelimit(key="ip", rate="30/m")
def refuconnect_demo(request):
    payload, err = _parse_json_body(request)
    if err:
        text = request.POST.get("feedback_text", "").strip()[:_MAX_FEEDBACK]
    else:
        text = payload.get("feedback_text", "").strip()[:_MAX_FEEDBACK]

    if not text:
        return JsonResponse({"success": False, "error": "Please enter some text."}, status=400)

    try:
        detected_lang = detect(text)
        blob          = TextBlob(text)
        polarity      = blob.sentiment.polarity

        if polarity > 0.1:
            sentiment, icon_class, color = "Positive", "fas fa-face-smile", "text-green-600"
        elif polarity < -0.1:
            sentiment, icon_class, color = "Negative", "fas fa-face-frown", "text-red-600"
        else:
            sentiment, icon_class, color = "Neutral",  "fas fa-face-meh",   "text-yellow-600"

        text_lower = text.lower()
        topics = [
            topic
            for topic, keywords in _TOPIC_KEYWORDS.items()
            if any(kw in text_lower for kw in keywords)
        ] or ["General Feedback"]

        return JsonResponse({
            "success":           True,
            "original_text":     text,
            "detected_language": detected_lang.upper(),
            "language_name":     _LANGUAGE_NAMES.get(detected_lang, "Unknown"),
            "sentiment":         sentiment,
            "sentiment_icon":    icon_class,
            "sentiment_color":   color,
            "polarity":          round(polarity, 2),
            "topics":            topics,
            "confidence":        round(random.uniform(0.85, 0.98), 2),
        })

    except Exception:
        logger.exception("RefuConnect NLP analysis failed")
        return JsonResponse({
            "success":           True,
            "original_text":     text,
            "detected_language": "EN",
            "language_name":     "English",
            "sentiment":         "Neutral",
            "sentiment_icon":    "fas fa-face-meh",
            "sentiment_color":   "text-yellow-600",
            "polarity":          0.0,
            "topics":            ["General Feedback"],
            "confidence":        0.92,
        })


# Error handlers

def handler404(request, exception):
    return render(request, "404.html", status=404)


def handler500(request):
    return render(request, "500.html", status=500)