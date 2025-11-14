"""
ADAML-Pluto: SDR (Sales Development Representative) Focused Toolkit

A comprehensive toolkit for sales development teams to manage leads,
automate outreach, and track performance.
"""

__version__ = "0.1.0"
__author__ = "ADAML Team"

from adaml_pluto.lead_management.lead import Lead, LeadStatus
from adaml_pluto.lead_management.lead_manager import LeadManager
from adaml_pluto.email_tools.template_manager import EmailTemplateManager
from adaml_pluto.email_tools.outreach_tracker import OutreachTracker

__all__ = [
    "Lead",
    "LeadStatus",
    "LeadManager",
    "EmailTemplateManager",
    "OutreachTracker",
]
