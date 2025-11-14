# ADAML-Pluto

**SDR (Sales Development Representative) Focused Toolkit**

A comprehensive Python toolkit designed for sales development teams to manage leads, automate outreach campaigns, and track performance metrics.

## Features

### 🎯 Lead Management
- **Lead Data Model**: Structured lead information with validation
- **Lead Status Tracking**: Track leads through the sales pipeline (New → Contacted → Qualified → Opportunity → Converted)
- **Lead Scoring**: Assign and track lead scores (0-100)
- **Search & Filter**: Easily find leads by name, email, company, status, or score
- **Persistent Storage**: Save and load leads to/from JSON files

### 📧 Email Tools
- **Template Management**: Create and manage reusable email templates with variable substitution
- **Default Templates**: Pre-configured templates for common outreach scenarios
- **Outreach Tracking**: Monitor email campaigns and track engagement
- **Status Updates**: Track email status (Sent → Opened → Clicked → Replied)
- **Analytics**: Calculate response rates, open rates, and campaign performance

### 📊 Analytics & Reporting
- **Lead Statistics**: Get insights on lead distribution and average scores
- **Outreach Metrics**: Track response rates, open rates, and campaign effectiveness
- **Status Breakdown**: View leads and outreach by status

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/ro0TuX777/ADAML-Pluto.git
cd ADAML-Pluto

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### For Development

```bash
# Install development dependencies
pip install -r requirements-dev.txt
```

## Quick Start

### Lead Management

```python
from adaml_pluto import Lead, LeadManager, LeadStatus
from pathlib import Path

# Initialize lead manager with persistent storage
manager = LeadManager(storage_path=Path("leads.json"))

# Create a new lead
lead = manager.create_lead({
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "company": "Acme Corp",
    "title": "VP of Sales",
    "source": "LinkedIn",
    "score": 75
})

# Update lead status
lead.update_status(LeadStatus.CONTACTED)
manager.update_lead(lead.id, {"status": LeadStatus.CONTACTED})

# Add notes
lead.add_note("Had a great conversation about their pain points")

# Search leads
results = manager.search_leads("Acme")

# Filter leads
qualified_leads = manager.list_leads(status=LeadStatus.QUALIFIED, min_score=70)

# Get statistics
stats = manager.get_stats()
print(f"Total leads: {stats['total_leads']}")
print(f"Average score: {stats['average_score']}")
```

### Email Template Management

```python
from adaml_pluto import EmailTemplateManager
from pathlib import Path

# Initialize template manager
template_mgr = EmailTemplateManager(storage_path=Path("templates.json"))

# List available templates
templates = template_mgr.list_templates()
print(templates)  # ['initial_outreach', 'follow_up', 'value_proposition']

# Render a template
email = template_mgr.render_template("initial_outreach", {
    "first_name": "John",
    "company": "Acme Corp",
    "industry": "SaaS",
    "pain_point": "improving sales efficiency",
    "sender_name": "Jane Smith"
})

print(email['subject'])  # "Quick question about Acme Corp"
print(email['body'])     # Fully rendered email body

# Create a custom template
from adaml_pluto.email_tools.template_manager import EmailTemplate

custom_template = EmailTemplate(
    name="meeting_request",
    subject="Meeting request - {topic}",
    body="Hi {first_name},\n\nI'd love to discuss {topic}...",
    description="Template for meeting requests"
)
template_mgr.add_template(custom_template)
```

### Outreach Tracking

```python
from adaml_pluto import OutreachTracker
from adaml_pluto.email_tools.outreach_tracker import OutreachStatus
from pathlib import Path

# Initialize tracker
tracker = OutreachTracker(storage_path=Path("outreach.json"))

# Create outreach record
outreach = tracker.create_outreach(
    lead_id=lead.id,
    template_name="initial_outreach",
    subject="Quick question about Acme Corp"
)

# Mark as sent
tracker.mark_sent(outreach.id)

# Update status when lead responds
tracker.update_status(
    outreach.id,
    OutreachStatus.REPLIED,
    note="Interested in learning more"
)

# Get all outreach for a lead
lead_outreach = tracker.get_lead_outreach(lead.id)

# Get statistics
stats = tracker.get_stats()
print(f"Response rate: {stats['response_rate']}%")
print(f"Open rate: {stats['open_rate']}%")
```

## Project Structure

```
ADAML-Pluto/
├── src/
│   └── adaml_pluto/
│       ├── __init__.py
│       ├── lead_management/
│       │   ├── __init__.py
│       │   ├── lead.py              # Lead data model
│       │   └── lead_manager.py      # Lead CRUD operations
│       ├── email_tools/
│       │   ├── __init__.py
│       │   ├── template_manager.py  # Email template management
│       │   └── outreach_tracker.py  # Outreach tracking
│       ├── analytics/
│       │   └── __init__.py
│       └── utils/
│           └── __init__.py
├── tests/                           # Test suite
├── examples/                        # Usage examples
├── README.md
├── setup.py
├── requirements.txt
└── requirements-dev.txt
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=adaml_pluto --cov-report=html
```

### Code Quality

```bash
# Format code
black src/

# Lint code
flake8 src/

# Type checking
mypy src/
```

## Use Cases

1. **Lead Qualification**: Score and prioritize leads based on engagement and fit
2. **Outreach Campaigns**: Manage multi-touch email campaigns with templates
3. **Performance Tracking**: Monitor SDR team performance and optimize strategies
4. **Pipeline Management**: Track leads through the entire sales funnel
5. **A/B Testing**: Compare different email templates and approaches

## Requirements

- Python 3.8+
- pydantic >= 2.0.0
- python-dotenv >= 1.0.0

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or contributions, please open an issue on GitHub.