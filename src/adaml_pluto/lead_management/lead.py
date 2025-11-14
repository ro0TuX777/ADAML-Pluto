"""Lead data model and status tracking."""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class LeadStatus(str, Enum):
    """Enum for lead status tracking."""

    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    UNQUALIFIED = "unqualified"
    OPPORTUNITY = "opportunity"
    CONVERTED = "converted"
    LOST = "lost"


class Lead(BaseModel):
    """
    Lead data model for managing sales prospects.

    Attributes:
        id: Unique identifier for the lead
        first_name: Lead's first name
        last_name: Lead's last name
        email: Lead's email address
        company: Lead's company name
        title: Lead's job title
        phone: Lead's phone number
        status: Current status of the lead
        source: Source of the lead (e.g., website, referral, campaign)
        score: Lead score (0-100)
        notes: Additional notes about the lead
        custom_fields: Dictionary for custom field data
        created_at: Timestamp when lead was created
        updated_at: Timestamp when lead was last updated
    """

    id: Optional[str] = None
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    email: EmailStr
    company: Optional[str] = None
    title: Optional[str] = None
    phone: Optional[str] = None
    status: LeadStatus = LeadStatus.NEW
    source: Optional[str] = None
    score: int = Field(default=0, ge=0, le=100)
    notes: str = ""
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
        }
    )

    def update_status(self, status: LeadStatus) -> None:
        """
        Update the lead's status and timestamp.

        Args:
            status: New status for the lead
        """
        self.status = status
        self.updated_at = datetime.now()

    def add_note(self, note: str) -> None:
        """
        Add a note to the lead's notes.

        Args:
            note: Note text to add
        """
        timestamp = datetime.now().isoformat()
        new_note = f"[{timestamp}] {note}"
        if self.notes:
            self.notes += f"\n{new_note}"
        else:
            self.notes = new_note
        self.updated_at = datetime.now()

    def update_score(self, score: int) -> None:
        """
        Update the lead's score.

        Args:
            score: New score value (0-100)

        Raises:
            ValueError: If score is not between 0 and 100
        """
        if not 0 <= score <= 100:
            raise ValueError("Score must be between 0 and 100")
        self.score = score
        self.updated_at = datetime.now()

    def get_full_name(self) -> str:
        """
        Get the lead's full name.

        Returns:
            Full name as a string
        """
        return f"{self.first_name} {self.last_name}"
