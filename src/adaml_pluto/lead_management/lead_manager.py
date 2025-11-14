"""Lead manager for CRUD operations and lead list management."""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from adaml_pluto.lead_management.lead import Lead, LeadStatus


class LeadManager:
    """
    Manager class for handling lead operations.

    Supports creating, reading, updating, and deleting leads,
    as well as filtering and searching functionality.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize the LeadManager.

        Args:
            storage_path: Optional path to store leads data
        """
        self.leads: Dict[str, Lead] = {}
        self.storage_path = storage_path
        if storage_path and storage_path.exists():
            self.load_leads()

    def create_lead(self, lead_data: Dict[str, Any]) -> Lead:
        """
        Create a new lead.

        Args:
            lead_data: Dictionary containing lead information

        Returns:
            Created Lead object
        """
        # Generate unique ID if not provided
        if "id" not in lead_data or not lead_data["id"]:
            lead_data["id"] = str(uuid.uuid4())

        lead = Lead(**lead_data)
        self.leads[lead.id] = lead

        if self.storage_path:
            self.save_leads()

        return lead

    def get_lead(self, lead_id: str) -> Optional[Lead]:
        """
        Get a lead by ID.

        Args:
            lead_id: Unique identifier of the lead

        Returns:
            Lead object if found, None otherwise
        """
        return self.leads.get(lead_id)

    def update_lead(self, lead_id: str, updates: Dict[str, Any]) -> Optional[Lead]:
        """
        Update a lead's information.

        Args:
            lead_id: Unique identifier of the lead
            updates: Dictionary of fields to update

        Returns:
            Updated Lead object if found, None otherwise
        """
        lead = self.leads.get(lead_id)
        if not lead:
            return None

        # Update fields
        for key, value in updates.items():
            if hasattr(lead, key):
                setattr(lead, key, value)

        lead.updated_at = datetime.now()

        if self.storage_path:
            self.save_leads()

        return lead

    def delete_lead(self, lead_id: str) -> bool:
        """
        Delete a lead.

        Args:
            lead_id: Unique identifier of the lead

        Returns:
            True if deleted, False if not found
        """
        if lead_id in self.leads:
            del self.leads[lead_id]
            if self.storage_path:
                self.save_leads()
            return True
        return False

    def list_leads(
        self,
        status: Optional[LeadStatus] = None,
        min_score: Optional[int] = None,
        company: Optional[str] = None,
    ) -> List[Lead]:
        """
        List leads with optional filtering.

        Args:
            status: Filter by lead status
            min_score: Filter by minimum score
            company: Filter by company name

        Returns:
            List of filtered leads
        """
        filtered_leads = list(self.leads.values())

        if status:
            filtered_leads = [lead for lead in filtered_leads if lead.status == status]

        if min_score is not None:
            filtered_leads = [lead for lead in filtered_leads if lead.score >= min_score]

        if company:
            filtered_leads = [
                lead
                for lead in filtered_leads
                if lead.company and company.lower() in lead.company.lower()
            ]

        return filtered_leads

    def search_leads(self, query: str) -> List[Lead]:
        """
        Search leads by name, email, or company.

        Args:
            query: Search query string

        Returns:
            List of matching leads
        """
        query_lower = query.lower()
        results = []

        for lead in self.leads.values():
            if (
                query_lower in lead.first_name.lower()
                or query_lower in lead.last_name.lower()
                or query_lower in lead.email.lower()
                or (lead.company and query_lower in lead.company.lower())
            ):
                results.append(lead)

        return results

    def save_leads(self) -> None:
        """Save leads to storage file."""
        if not self.storage_path:
            return

        leads_data = {lead_id: lead.model_dump(mode="json") for lead_id, lead in self.leads.items()}

        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, "w") as f:
            json.dump(leads_data, f, indent=2, default=str)

    def load_leads(self) -> None:
        """Load leads from storage file."""
        if not self.storage_path or not self.storage_path.exists():
            return

        with open(self.storage_path, "r") as f:
            leads_data = json.load(f)

        self.leads = {lead_id: Lead(**lead_dict) for lead_id, lead_dict in leads_data.items()}

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about leads.

        Returns:
            Dictionary with lead statistics
        """
        total = len(self.leads)
        by_status = {}

        for status in LeadStatus:
            by_status[status.value] = len(
                [lead for lead in self.leads.values() if lead.status == status]
            )

        avg_score = (
            sum(lead.score for lead in self.leads.values()) / total if total > 0 else 0
        )

        return {
            "total_leads": total,
            "by_status": by_status,
            "average_score": round(avg_score, 2),
        }
