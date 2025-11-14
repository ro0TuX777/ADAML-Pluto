"""Tests for email template manager."""

import pytest
from pathlib import Path
import tempfile

from adaml_pluto.email_tools.template_manager import EmailTemplate, EmailTemplateManager


class TestEmailTemplate:
    """Test cases for EmailTemplate."""
    
    def test_create_template(self):
        """Test creating an email template."""
        template = EmailTemplate(
            name="test",
            subject="Hello {name}",
            body="Dear {name}, this is a test.",
            description="Test template"
        )
        
        assert template.name == "test"
        assert template.subject == "Hello {name}"
        assert "Test template" in template.description
    
    def test_render_template(self):
        """Test rendering a template with variables."""
        template = EmailTemplate(
            name="test",
            subject="Hello {name}",
            body="Dear {name}, welcome to {company}!"
        )
        
        rendered = template.render({
            "name": "John",
            "company": "TechCorp"
        })
        
        assert rendered["subject"] == "Hello John"
        assert rendered["body"] == "Dear John, welcome to TechCorp!"
    
    def test_to_dict(self):
        """Test converting template to dictionary."""
        template = EmailTemplate(
            name="test",
            subject="Test subject",
            body="Test body"
        )
        
        data = template.to_dict()
        
        assert data["name"] == "test"
        assert data["subject"] == "Test subject"
        assert data["body"] == "Test body"
    
    def test_from_dict(self):
        """Test creating template from dictionary."""
        data = {
            "name": "test",
            "subject": "Test subject",
            "body": "Test body",
            "description": "Test desc"
        }
        
        template = EmailTemplate.from_dict(data)
        
        assert template.name == "test"
        assert template.subject == "Test subject"


class TestEmailTemplateManager:
    """Test cases for EmailTemplateManager."""
    
    def test_default_templates(self):
        """Test that default templates are created."""
        manager = EmailTemplateManager()
        
        templates = manager.list_templates()
        
        assert "initial_outreach" in templates
        assert "follow_up" in templates
        assert "value_proposition" in templates
    
    def test_add_template(self):
        """Test adding a custom template."""
        manager = EmailTemplateManager()
        
        template = EmailTemplate(
            name="custom",
            subject="Custom subject",
            body="Custom body"
        )
        
        manager.add_template(template)
        
        assert "custom" in manager.list_templates()
        retrieved = manager.get_template("custom")
        assert retrieved.name == "custom"
    
    def test_get_template(self):
        """Test retrieving a template."""
        manager = EmailTemplateManager()
        
        template = manager.get_template("initial_outreach")
        
        assert template is not None
        assert template.name == "initial_outreach"
    
    def test_delete_template(self):
        """Test deleting a template."""
        manager = EmailTemplateManager()
        
        template = EmailTemplate(
            name="to_delete",
            subject="Test",
            body="Test"
        )
        manager.add_template(template)
        
        assert "to_delete" in manager.list_templates()
        
        result = manager.delete_template("to_delete")
        
        assert result is True
        assert "to_delete" not in manager.list_templates()
    
    def test_render_template(self):
        """Test rendering a template through the manager."""
        manager = EmailTemplateManager()
        
        rendered = manager.render_template("initial_outreach", {
            "first_name": "John",
            "company": "TechCorp",
            "industry": "SaaS",
            "pain_point": "scaling",
            "sender_name": "Jane"
        })
        
        assert rendered is not None
        assert "John" in rendered["body"]
        assert "TechCorp" in rendered["subject"]
    
    def test_persistence(self):
        """Test saving and loading templates."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "templates.json"
            
            # Create manager and add template
            manager1 = EmailTemplateManager(storage_path=storage_path)
            template = EmailTemplate(
                name="persist_test",
                subject="Test",
                body="Test body"
            )
            manager1.add_template(template)
            
            # Create new manager and load templates
            manager2 = EmailTemplateManager(storage_path=storage_path)
            
            retrieved = manager2.get_template("persist_test")
            assert retrieved is not None
            assert retrieved.name == "persist_test"
