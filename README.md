# AkolPaul.dev — Developer Portfolio

A personal portfolio website built with Django, showcasing my projects, skills, and experience as a Software Engineering student at Makerere University.

---

## Live Demo

[akolpaul.dev](https://akolpaul.dev) <!-- Update with your Railway URL -->

---

## Features

- **Project Showcase** — Six featured projects with descriptions, tech stacks, and live links
- **GitHub Activity Chart** — Live contributions chart powered by Chart.js and the GitHub public events API
- **Animated Tech Stack** — Orbit diagram visualizing core technologies
- **Contact Form** — Gmail SMTP email delivery with HTML templates, honeypot spam protection, and rate limiting
- **Security Hardened** — CSP headers, rate limiting, WhiteNoise static files, and environment-based config
- **Fixture-Based Content** — Projects and skills seeded from Django fixtures

---

## Tech Stack

| Layer         | Technology          |
|---------------|---------------------|
| Backend       | Django 4.x          |
| Frontend      | HTML5, CSS3, JavaScript |
| Charts        | Chart.js            |
| Static Files  | WhiteNoise          |
| Email         | Gmail SMTP          |
| Security      | django-csp, django-ratelimit |
| Config        | python-decouple     |
| Deployment    | Railway             |

---

## Projects Featured

| Project              | Description                                                         |
|----------------------|---------------------------------------------------------------------|
| Afriplay             | Real-time Ugandan football coverage platform (Django Channels + React) |
| RefuConnect          | Refugee information and services platform                          |
| SALT-KD              | Multilingual speech processing for Ugandan languages (ML research) |
| 8TechBank            | Flask banking app demonstrating secure vs vulnerable web practices |
| Balirah Beauty Salon | Django booking and CMS web app for a luxury barber studio          |
| OCS                  | Operational Command System for Redsquare Creative Agency           |

---

## Local Setup

```bash
# Clone the repository
git clone https://github.com/akolpaul2244/<repo-name>.git
cd <repo-name>

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your values

# Run migrations
python manage.py migrate

# Load fixture data
python manage.py loaddata projects skills

# Start the development server
python manage.py runserver
```

---

## Environment Variables

Create a `.env` file in the root directory:

```env
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Email (Gmail SMTP)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# GitHub (for activity chart)
GITHUB_USERNAME=akolpaul2244
```

---

## Deployment (Railway)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and link project
railway login
railway link

# Deploy
railway up
```

Ensure `ALLOWED_HOSTS`, `DEBUG=False`, and `SECRET_KEY` are set in Railway environment variables.

---

## Project Structure

```
portfolio/
├── core/               # Main app (views, models, urls)
│   ├── fixtures/       # Seed data for projects and skills
│   ├── templates/      # HTML templates
│   └── static/         # CSS, JS, images
├── portfolio/          # Django project settings
│   ├── settings.py
│   └── urls.py
├── requirements.txt
└── manage.py
```

---

## Contact

Akol Paul

- Email: [paulakol97@gmail.com](mailto:paulakol97@gmail.com)
- LinkedIn: [linkedin.com/in/akol-paul-6b662a312](https://linkedin.com/in/akol-paul-6b662a312)
- GitHub: [github.com/akolpaul2244](https://github.com/akolpaul2244)
- Phone: +256 782 457 648

---

## License

This project is open source and available under the [MIT License](LICENSE).