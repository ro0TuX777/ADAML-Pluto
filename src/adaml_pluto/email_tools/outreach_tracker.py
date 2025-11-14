"""Outreach tracking for SDR campaigns."""

from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
import json
from pathlib import Path
import uuid


class OutreachStatus(str, Enum):
    """Status of an outreach attempt."""
    
    PENDING = "pending"
    SENT = "sent"
    OPENED = "opened"
    CLICKED = "clicked"
    REPLIED = "replied"
    BOUNCED = "bounced"
    UNSUBSCRIBED = "unsubscribed"


class OutreachRecord:
    """Record of a single outreach attempt."""
    
    def __init__(
        self,
        id: Optional[str] = None,
        lead_id: str = "",
        template_name: str = "",
        subject: str = "",
        sent_at: Optional[datetime] = None,
        status: OutreachStatus = OutreachStatus.PENDING,
        notes: str = ""
    ):
        """
        Initialize an outreach record.
        
        Args:
            id: Unique identifier
            lead_id: ID of the lead contacted
            template_name: Name of email template used
            subject: Email subject line
            sent_at: Timestamp when email was sent
            status: Current status of the outreach
            notes: Additional notes
        """
        self.id = id or str(uuid.uuid4())
        self.lead_id = lead_id
        self.template_name = template_name
        self.subject = subject
        self.sent_at = sent_at
        self.status = status
        self.notes = notes
        self.status_history: List[Dict[str, str]] = []
    
    def update_status(self, status: OutreachStatus, note: str = "") -> None:
        """
        Update the outreach status.
        
        Args:
            status: New status
            note: Optional note about the status change
        """
        self.status = status
        self.status_history.append({
            "status": status.value,
            "timestamp": datetime.now().isoformat(),
            "note": note
        })
    
    def to_dict(self) -> Dict:
        """Convert record to dictionary."""
        return {
            "id": self.id,
            "lead_id": self.lead_id,
            "template_name": self.template_name,
            "subject": self.subject,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "status": self.status.value,
            "notes": self.notes,
            "status_history": self.status_history
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "OutreachRecord":
        """Create record from dictionary."""
        record = cls(
            id=data.get("id"),
            lead_id=data.get("lead_id", ""),
            template_name=data.get("template_name", ""),
            subject=data.get("subject", ""),
            sent_at=datetime.fromisoformat(data["sent_at"]) if data.get("sent_at") else None,
            status=OutreachStatus(data.get("status", OutreachStatus.PENDING)),
            notes=data.get("notes", "")
        )
        record.status_history = data.get("status_history", [])
        return record


class OutreachTracker:
    """
    Tracker for managing outreach campaigns and follow-ups.
    
    Tracks all email outreach attempts, their status, and engagement.
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize the OutreachTracker.
        
        Args:
            storage_path: Optional path to store outreach data
        """
        self.records: Dict[str, OutreachRecord] = {}
        self.storage_path = storage_path
        if storage_path and storage_path.exists():
            self.load_records()
    
    def create_outreach(
        self,
        lead_id: str,
        template_name: str,
        subject: str
    ) -> OutreachRecord:
        """
        Create a new outreach record.
        
        Args:
            lead_id: ID of the lead being contacted
            template_name: Name of the email template used
            subject: Email subject line
        
        Returns:
            Created OutreachRecord
        """
        record = OutreachRecord(
            lead_id=lead_id,
            template_name=template_name,
            subject=subject
        )
        self.records[record.id] = record
        
        if self.storage_path:
            self.save_records()
        
        return record
    
    def mark_sent(self, record_id: str) -> Optional[OutreachRecord]:
        """
        Mark an outreach as sent.
        
        Args:
            record_id: Outreach record ID
        
        Returns:
            Updated record if found, None otherwise
        """
        record = self.records.get(record_id)
        if record:
            record.sent_at = datetime.now()
            record.update_status(OutreachStatus.SENT)
            if self.storage_path:
                self.save_records()
        return record
    
    def update_status(
        self,
        record_id: str,
        status: OutreachStatus,
        note: str = ""
    ) -> Optional[OutreachRecord]:
        """
        Update the status of an outreach.
        
        Args:
            record_id: Outreach record ID
            status: New status
            note: Optional note
        
        Returns:
            Updated record if found, None otherwise
        """
        record = self.records.get(record_id)
        if record:
            record.update_status(status, note)
            if self.storage_path:
                self.save_records()
        return record
    
    def get_outreach(self, record_id: str) -> Optional[OutreachRecord]:
        """
        Get an outreach record by ID.
        
        Args:
            record_id: Outreach record ID
        
        Returns:
            OutreachRecord if found, None otherwise
        """
        return self.records.get(record_id)
    
    def get_lead_outreach(self, lead_id: str) -> List[OutreachRecord]:
        """
        Get all outreach records for a specific lead.
        
        Args:
            lead_id: Lead ID
        
        Returns:
            List of outreach records for the lead
        """
        return [
            record for record in self.records.values()
            if record.lead_id == lead_id
        ]
    
    def get_stats(self) -> Dict:
        """
        Get outreach statistics.
        
        Returns:
            Dictionary with outreach statistics
        """
        total = len(self.records)
        by_status = {}
        
        for status in OutreachStatus:
            by_status[status.value] = len([
                r for r in self.records.values() if r.status == status
            ])
        
        replied = by_status.get(OutreachStatus.REPLIED.value, 0)
        sent = by_status.get(OutreachStatus.SENT.value, 0)
        opened = by_status.get(OutreachStatus.OPENED.value, 0)
        
        response_rate = (replied / sent * 100) if sent > 0 else 0
        open_rate = (opened / sent * 100) if sent > 0 else 0
        
        return {
            "total_outreach": total,
            "by_status": by_status,
            "response_rate": round(response_rate, 2),
            "open_rate": round(open_rate, 2)
        }
    
    def save_records(self) -> None:
        """Save outreach records to storage file."""
        if not self.storage_path:
            return
        
        records_data = {
            record_id: record.to_dict()
            for record_id, record in self.records.items()
        }
        
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, 'w') as f:
            json.dump(records_data, f, indent=2)
    
    def load_records(self) -> None:
        """Load outreach records from storage file."""
        if not self.storage_path or not self.storage_path.exists():
            return
        
        with open(self.storage_path, 'r') as f:
            records_data = json.load(f)
        
        self.records = {
            record_id: OutreachRecord.from_dict(record_dict)
            for record_id, record_dict in records_data.items()
        }
