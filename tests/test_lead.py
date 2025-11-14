"""Tests for lead management module."""

import pytest
from datetime import datetime
from adaml_pluto.lead_management.lead import Lead, LeadStatus


class TestLead:
    """Test cases for the Lead model."""
    
    def test_create_lead(self):
        """Test creating a basic lead."""
        lead = Lead(
            first_name="John",
            last_name="Doe",
            email="john@example.com"
        )
        
        assert lead.first_name == "John"
        assert lead.last_name == "Doe"
        assert lead.email == "john@example.com"
        assert lead.status == LeadStatus.NEW
        assert lead.score == 0
    
    def test_lead_with_all_fields(self):
        """Test creating a lead with all fields."""
        lead = Lead(
            first_name="Jane",
            last_name="Smith",
            email="jane@company.com",
            company="TechCorp",
            title="VP Sales",
            phone="+1234567890",
            source="LinkedIn",
            score=75
        )
        
        assert lead.company == "TechCorp"
        assert lead.title == "VP Sales"
        assert lead.score == 75
        assert lead.source == "LinkedIn"
    
    def test_update_status(self):
        """Test updating lead status."""
        lead = Lead(
            first_name="John",
            last_name="Doe",
            email="john@example.com"
        )
        
        original_time = lead.updated_at
        lead.update_status(LeadStatus.CONTACTED)
        
        assert lead.status == LeadStatus.CONTACTED
        assert lead.updated_at > original_time
    
    def test_add_note(self):
        """Test adding notes to a lead."""
        lead = Lead(
            first_name="John",
            last_name="Doe",
            email="john@example.com"
        )
        
        lead.add_note("First contact made")
        assert "First contact made" in lead.notes
        
        lead.add_note("Follow-up scheduled")
        assert "First contact made" in lead.notes
        assert "Follow-up scheduled" in lead.notes
    
    def test_update_score(self):
        """Test updating lead score."""
        lead = Lead(
            first_name="John",
            last_name="Doe",
            email="john@example.com"
        )
        
        lead.update_score(85)
        assert lead.score == 85
    
    def test_update_score_invalid(self):
        """Test that invalid scores raise an error."""
        lead = Lead(
            first_name="John",
            last_name="Doe",
            email="john@example.com"
        )
        
        with pytest.raises(ValueError):
            lead.update_score(150)
        
        with pytest.raises(ValueError):
            lead.update_score(-10)
    
    def test_get_full_name(self):
        """Test getting full name."""
        lead = Lead(
            first_name="John",
            last_name="Doe",
            email="john@example.com"
        )
        
        assert lead.get_full_name() == "John Doe"
    
    def test_custom_fields(self):
        """Test custom fields functionality."""
        lead = Lead(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            custom_fields={"industry": "SaaS", "employees": 50}
        )
        
        assert lead.custom_fields["industry"] == "SaaS"
        assert lead.custom_fields["employees"] == 50
