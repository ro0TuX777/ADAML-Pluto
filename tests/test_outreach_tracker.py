"""Tests for outreach tracker."""

import pytest
from pathlib import Path
import tempfile

from adaml_pluto.email_tools.outreach_tracker import (
    OutreachRecord,
    OutreachStatus,
    OutreachTracker
)


class TestOutreachRecord:
    """Test cases for OutreachRecord."""
    
    def test_create_record(self):
        """Test creating an outreach record."""
        record = OutreachRecord(
            lead_id="123",
            template_name="initial_outreach",
            subject="Test subject"
        )
        
        assert record.lead_id == "123"
        assert record.template_name == "initial_outreach"
        assert record.status == OutreachStatus.PENDING
        assert record.id is not None
    
    def test_update_status(self):
        """Test updating record status."""
        record = OutreachRecord(
            lead_id="123",
            template_name="test",
            subject="Test"
        )
        
        record.update_status(OutreachStatus.SENT, "Email sent successfully")
        
        assert record.status == OutreachStatus.SENT
        assert len(record.status_history) == 1
        assert record.status_history[0]["status"] == OutreachStatus.SENT.value
        assert "Email sent successfully" in record.status_history[0]["note"]


class TestOutreachTracker:
    """Test cases for OutreachTracker."""
    
    def test_create_outreach(self):
        """Test creating an outreach record."""
        tracker = OutreachTracker()
        
        record = tracker.create_outreach(
            lead_id="123",
            template_name="initial_outreach",
            subject="Test subject"
        )
        
        assert record.id is not None
        assert len(tracker.records) == 1
    
    def test_mark_sent(self):
        """Test marking an outreach as sent."""
        tracker = OutreachTracker()
        
        record = tracker.create_outreach(
            lead_id="123",
            template_name="test",
            subject="Test"
        )
        
        updated = tracker.mark_sent(record.id)
        
        assert updated is not None
        assert updated.status == OutreachStatus.SENT
        assert updated.sent_at is not None
    
    def test_update_status(self):
        """Test updating outreach status."""
        tracker = OutreachTracker()
        
        record = tracker.create_outreach(
            lead_id="123",
            template_name="test",
            subject="Test"
        )
        
        updated = tracker.update_status(
            record.id,
            OutreachStatus.REPLIED,
            "Got a positive response"
        )
        
        assert updated.status == OutreachStatus.REPLIED
    
    def test_get_outreach(self):
        """Test getting an outreach record."""
        tracker = OutreachTracker()
        
        record = tracker.create_outreach(
            lead_id="123",
            template_name="test",
            subject="Test"
        )
        
        retrieved = tracker.get_outreach(record.id)
        
        assert retrieved is not None
        assert retrieved.id == record.id
    
    def test_get_lead_outreach(self):
        """Test getting all outreach for a lead."""
        tracker = OutreachTracker()
        
        tracker.create_outreach(
            lead_id="123",
            template_name="initial",
            subject="First"
        )
        tracker.create_outreach(
            lead_id="123",
            template_name="follow_up",
            subject="Second"
        )
        tracker.create_outreach(
            lead_id="456",
            template_name="initial",
            subject="Different lead"
        )
        
        lead_records = tracker.get_lead_outreach("123")
        
        assert len(lead_records) == 2
        assert all(r.lead_id == "123" for r in lead_records)
    
    def test_get_stats(self):
        """Test getting outreach statistics."""
        tracker = OutreachTracker()
        
        # Create and mark some outreach records
        r1 = tracker.create_outreach("1", "test", "Test 1")
        r2 = tracker.create_outreach("2", "test", "Test 2")
        r3 = tracker.create_outreach("3", "test", "Test 3")
        
        tracker.mark_sent(r1.id)
        tracker.mark_sent(r2.id)
        tracker.mark_sent(r3.id)
        
        tracker.update_status(r1.id, OutreachStatus.REPLIED)
        tracker.update_status(r2.id, OutreachStatus.OPENED)
        
        stats = tracker.get_stats()
        
        assert stats["total_outreach"] == 3
        assert stats["by_status"][OutreachStatus.REPLIED.value] == 1
        assert stats["by_status"][OutreachStatus.OPENED.value] == 1
        assert stats["response_rate"] > 0
        assert stats["open_rate"] > 0
    
    def test_persistence(self):
        """Test saving and loading outreach records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "outreach.json"
            
            # Create tracker and add record
            tracker1 = OutreachTracker(storage_path=storage_path)
            record = tracker1.create_outreach(
                lead_id="123",
                template_name="test",
                subject="Test subject"
            )
            tracker1.mark_sent(record.id)
            
            # Create new tracker and load records
            tracker2 = OutreachTracker(storage_path=storage_path)
            
            assert len(tracker2.records) == 1
            loaded = tracker2.get_outreach(record.id)
            assert loaded is not None
            assert loaded.lead_id == "123"
            assert loaded.status == OutreachStatus.SENT
