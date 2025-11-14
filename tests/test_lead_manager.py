"""Tests for lead manager."""

import pytest
from pathlib import Path
import tempfile
import os

from adaml_pluto.lead_management.lead_manager import LeadManager
from adaml_pluto.lead_management.lead import LeadStatus


class TestLeadManager:
    """Test cases for the LeadManager."""
    
    def test_create_lead(self):
        """Test creating a lead through the manager."""
        manager = LeadManager()
        
        lead = manager.create_lead({
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com"
        })
        
        assert lead.id is not None
        assert lead.first_name == "John"
        assert len(manager.leads) == 1
    
    def test_get_lead(self):
        """Test retrieving a lead by ID."""
        manager = LeadManager()
        
        lead = manager.create_lead({
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com"
        })
        
        retrieved = manager.get_lead(lead.id)
        assert retrieved is not None
        assert retrieved.id == lead.id
        assert retrieved.email == lead.email
    
    def test_update_lead(self):
        """Test updating a lead."""
        manager = LeadManager()
        
        lead = manager.create_lead({
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com"
        })
        
        updated = manager.update_lead(lead.id, {
            "company": "TechCorp",
            "score": 75
        })
        
        assert updated.company == "TechCorp"
        assert updated.score == 75
    
    def test_delete_lead(self):
        """Test deleting a lead."""
        manager = LeadManager()
        
        lead = manager.create_lead({
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com"
        })
        
        assert len(manager.leads) == 1
        result = manager.delete_lead(lead.id)
        
        assert result is True
        assert len(manager.leads) == 0
    
    def test_list_leads(self):
        """Test listing all leads."""
        manager = LeadManager()
        
        manager.create_lead({
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com"
        })
        manager.create_lead({
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane@example.com"
        })
        
        leads = manager.list_leads()
        assert len(leads) == 2
    
    def test_list_leads_by_status(self):
        """Test filtering leads by status."""
        manager = LeadManager()
        
        lead1 = manager.create_lead({
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "status": LeadStatus.NEW
        })
        lead2 = manager.create_lead({
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane@example.com",
            "status": LeadStatus.QUALIFIED
        })
        
        new_leads = manager.list_leads(status=LeadStatus.NEW)
        qualified_leads = manager.list_leads(status=LeadStatus.QUALIFIED)
        
        assert len(new_leads) == 1
        assert len(qualified_leads) == 1
        assert new_leads[0].id == lead1.id
    
    def test_list_leads_by_score(self):
        """Test filtering leads by minimum score."""
        manager = LeadManager()
        
        manager.create_lead({
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "score": 50
        })
        manager.create_lead({
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane@example.com",
            "score": 80
        })
        
        high_score_leads = manager.list_leads(min_score=70)
        assert len(high_score_leads) == 1
        assert high_score_leads[0].score == 80
    
    def test_search_leads(self):
        """Test searching leads."""
        manager = LeadManager()
        
        manager.create_lead({
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "company": "TechCorp"
        })
        manager.create_lead({
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane@other.com",
            "company": "OtherCo"
        })
        
        results = manager.search_leads("TechCorp")
        assert len(results) == 1
        assert results[0].company == "TechCorp"
        
        results = manager.search_leads("Jane")
        assert len(results) == 1
        assert results[0].first_name == "Jane"
    
    def test_get_stats(self):
        """Test getting lead statistics."""
        manager = LeadManager()
        
        manager.create_lead({
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "score": 60,
            "status": LeadStatus.NEW
        })
        manager.create_lead({
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane@example.com",
            "score": 80,
            "status": LeadStatus.QUALIFIED
        })
        
        stats = manager.get_stats()
        
        assert stats["total_leads"] == 2
        assert stats["average_score"] == 70.0
        assert stats["by_status"][LeadStatus.NEW.value] == 1
        assert stats["by_status"][LeadStatus.QUALIFIED.value] == 1
    
    def test_persistence(self):
        """Test saving and loading leads."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "leads.json"
            
            # Create manager and add leads
            manager1 = LeadManager(storage_path=storage_path)
            lead = manager1.create_lead({
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com"
            })
            
            # Create new manager and load leads
            manager2 = LeadManager(storage_path=storage_path)
            
            assert len(manager2.leads) == 1
            loaded_lead = manager2.get_lead(lead.id)
            assert loaded_lead.first_name == "John"
            assert loaded_lead.email == "john@example.com"
