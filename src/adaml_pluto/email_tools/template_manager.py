"""Email template management for SDR outreach."""

from typing import Dict, List, Optional
from pathlib import Path
import json


class EmailTemplate:
    """Email template with variable substitution support."""
    
    def __init__(self, name: str, subject: str, body: str, description: str = ""):
        """
        Initialize an email template.
        
        Args:
            name: Template name/identifier
            subject: Email subject line (supports variables like {first_name})
            body: Email body text (supports variables)
            description: Optional description of the template
        """
        self.name = name
        self.subject = subject
        self.body = body
        self.description = description
    
    def render(self, variables: Dict[str, str]) -> Dict[str, str]:
        """
        Render the template with provided variables.
        
        Args:
            variables: Dictionary mapping variable names to values
        
        Returns:
            Dictionary with rendered 'subject' and 'body'
        """
        rendered_subject = self.subject
        rendered_body = self.body
        
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            rendered_subject = rendered_subject.replace(placeholder, value)
            rendered_body = rendered_body.replace(placeholder, value)
        
        return {
            "subject": rendered_subject,
            "body": rendered_body
        }
    
    def to_dict(self) -> Dict[str, str]:
        """Convert template to dictionary."""
        return {
            "name": self.name,
            "subject": self.subject,
            "body": self.body,
            "description": self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "EmailTemplate":
        """Create template from dictionary."""
        return cls(
            name=data["name"],
            subject=data["subject"],
            body=data["body"],
            description=data.get("description", "")
        )


class EmailTemplateManager:
    """
    Manager for email templates.
    
    Handles creation, storage, and retrieval of email templates
    for SDR outreach campaigns.
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize the EmailTemplateManager.
        
        Args:
            storage_path: Optional path to store templates
        """
        self.templates: Dict[str, EmailTemplate] = {}
        self.storage_path = storage_path
        if storage_path and storage_path.exists():
            self.load_templates()
        else:
            self._init_default_templates()
    
    def _init_default_templates(self) -> None:
        """Initialize with default email templates."""
        default_templates = [
            EmailTemplate(
                name="initial_outreach",
                subject="Quick question about {company}",
                body="""Hi {first_name},

I noticed that {company} is doing great work in {industry}. I wanted to reach out because I think our solution could help with {pain_point}.

Would you be open to a brief 15-minute call next week to explore if there's a fit?

Best regards,
{sender_name}""",
                description="Initial cold outreach template"
            ),
            EmailTemplate(
                name="follow_up",
                subject="Following up - {company}",
                body="""Hi {first_name},

I wanted to follow up on my previous email about {topic}. I understand you're busy, but I genuinely believe this could be valuable for {company}.

Are you available for a quick call this week?

Thanks,
{sender_name}""",
                description="Follow-up email template"
            ),
            EmailTemplate(
                name="value_proposition",
                subject="How {our_company} helped {similar_company}",
                body="""Hi {first_name},

I wanted to share a quick success story. We recently helped {similar_company} achieve {result}.

Given that {company} is in a similar space, I thought this might be relevant to you.

Would love to discuss how we could help {company} achieve similar results.

Best,
{sender_name}""",
                description="Value proposition template with case study"
            )
        ]
        
        for template in default_templates:
            self.templates[template.name] = template
    
    def add_template(self, template: EmailTemplate) -> None:
        """
        Add a new template.
        
        Args:
            template: EmailTemplate object to add
        """
        self.templates[template.name] = template
        if self.storage_path:
            self.save_templates()
    
    def get_template(self, name: str) -> Optional[EmailTemplate]:
        """
        Get a template by name.
        
        Args:
            name: Template name
        
        Returns:
            EmailTemplate if found, None otherwise
        """
        return self.templates.get(name)
    
    def list_templates(self) -> List[str]:
        """
        List all template names.
        
        Returns:
            List of template names
        """
        return list(self.templates.keys())
    
    def delete_template(self, name: str) -> bool:
        """
        Delete a template.
        
        Args:
            name: Template name to delete
        
        Returns:
            True if deleted, False if not found
        """
        if name in self.templates:
            del self.templates[name]
            if self.storage_path:
                self.save_templates()
            return True
        return False
    
    def render_template(self, name: str, variables: Dict[str, str]) -> Optional[Dict[str, str]]:
        """
        Render a template with variables.
        
        Args:
            name: Template name
            variables: Dictionary of variables to substitute
        
        Returns:
            Rendered email with subject and body, or None if template not found
        """
        template = self.get_template(name)
        if not template:
            return None
        return template.render(variables)
    
    def save_templates(self) -> None:
        """Save templates to storage file."""
        if not self.storage_path:
            return
        
        templates_data = {
            name: template.to_dict()
            for name, template in self.templates.items()
        }
        
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, 'w') as f:
            json.dump(templates_data, f, indent=2)
    
    def load_templates(self) -> None:
        """Load templates from storage file."""
        if not self.storage_path or not self.storage_path.exists():
            return
        
        with open(self.storage_path, 'r') as f:
            templates_data = json.load(f)
        
        self.templates = {
            name: EmailTemplate.from_dict(template_dict)
            for name, template_dict in templates_data.items()
        }
