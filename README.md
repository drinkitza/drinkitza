# Itza Yerba Mate Waitlist System

A clean, streamlined waitlist signup system for Itza Yerba Mate's pre-order campaign.

## Overview

This system allows potential customers to sign up for the Itza Yerba Mate pre-order waitlist. It features:

- Beautiful, responsive waitlist signup form
- Email storage in GitHub repository
- Local CSV backup of emails
- Beautifully designed HTML confirmation emails
- Fallback email queuing system for reliability

## Key Features

### Waitlist Signup

- Clean, user-friendly form that captures email addresses
- Client-side and server-side email validation
- Duplicate email prevention
- Responsive design that works on all devices

### Email Storage

- Primary storage in GitHub repository for easy access and backup
- Local CSV backup for redundancy
- Structured storage with timestamps

### Email Confirmation

- Beautifully designed HTML email template
- Highlights the six natural ingredients
- Maintains brand's irreverent "no powders, no bullshit" messaging
- Cross-email client compatibility

## Technical Architecture

### Frontend
- Static HTML/CSS/JavaScript
- Responsive design
- Client-side form validation

### Backend
- Flask web application
- GitHub API integration for email storage
- Email sending with two methods:
  1. EmailJS service (primary)
  2. SMTP email sending (fallback)
- Email queuing system for handling temporary failures

## Setup Instructions

### Environment Variables

The following environment variables are required:

```
# GitHub Integration
GITHUB_TOKEN=your_github_token

# EmailJS Configuration (Primary Email Method)
EMAIL_SERVICE_URL=your_emailjs_service_id
EMAIL_SERVICE_USER_ID=your_emailjs_user_id
EMAIL_SERVICE_TEMPLATE_ID=your_emailjs_template_id
EMAIL_SERVICE_ACCESS_TOKEN=your_emailjs_access_token

# SMTP Configuration (Fallback Email Method)
SENDER_EMAIL=your_email@gmail.com
SENDER_APP_PASSWORD=your_app_password
```

### Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables
4. Run the application: `python app.py`

## Files Overview

- `app.py` - Main Flask application
- `waitlist.html` - Waitlist signup form
- `emails/waitlist.csv` - Local CSV backup of emails
- `emails/confirmation_template.html` - HTML email template
- `emails/queue/` - Directory for queued emails (if sending fails)
- `process_email_queue.py` - Script to process queued emails

## Processing Queued Emails

If emails fail to send (due to network issues, etc.), they are stored in the `emails/queue/` directory. To process these queued emails:

```
python process_email_queue.py
```

This script will attempt to send all queued emails using both EmailJS and SMTP methods.

## Brand Elements

### Color Scheme
- Primary Green: #2D5A27
- Accent Orange: #FF7F3F
- Background Cream: #FFFAF5

### Typography
- Headings: Caesar Dressing (with Arial fallback)
- Body: Inter (with Arial fallback)

### Brand Voice
- Irreverent, direct, nature-focused
- Core Message: "No powders. No bullshit. Just as the gods intended."
