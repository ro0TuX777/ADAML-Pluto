"""
Basic example of using the ADAML-Pluto SDR toolkit.

This example demonstrates:
- Creating and managing leads
- Using email templates
- Tracking outreach campaigns
"""

import sys
from pathlib import Path

# Add src to path for direct execution
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from adaml_pluto import Lead, LeadManager, LeadStatus
from adaml_pluto import EmailTemplateManager, OutreachTracker
from adaml_pluto.email_tools.outreach_tracker import OutreachStatus


def main():
    """Run the basic example."""
    print("=" * 60)
    print("ADAML-Pluto SDR Toolkit - Basic Example")
    print("=" * 60)
    
    # Initialize managers with in-memory storage (no persistence)
    lead_manager = LeadManager()
    template_manager = EmailTemplateManager()
    outreach_tracker = OutreachTracker()
    
    print("\n1. Creating leads...")
    print("-" * 60)
    
    # Create sample leads
    leads_data = [
        {
            "first_name": "Sarah",
            "last_name": "Johnson",
            "email": "sarah.johnson@techcorp.com",
            "company": "TechCorp Inc",
            "title": "VP of Engineering",
            "source": "LinkedIn",
            "score": 85
        },
        {
            "first_name": "Michael",
            "last_name": "Chen",
            "email": "m.chen@innovate.io",
            "company": "Innovate.io",
            "title": "CTO",
            "source": "Conference",
            "score": 92
        },
        {
            "first_name": "Emily",
            "last_name": "Rodriguez",
            "email": "emily.r@startupxyz.com",
            "company": "StartupXYZ",
            "title": "Head of Sales",
            "source": "Referral",
            "score": 78
        }
    ]
    
    created_leads = []
    for lead_data in leads_data:
        lead = lead_manager.create_lead(lead_data)
        created_leads.append(lead)
        print(f"✓ Created lead: {lead.get_full_name()} ({lead.email})")
        print(f"  Company: {lead.company}, Score: {lead.score}")
    
    print(f"\nTotal leads created: {len(created_leads)}")
    
    # Display lead statistics
    print("\n2. Lead Statistics")
    print("-" * 60)
    stats = lead_manager.get_stats()
    print(f"Total leads: {stats['total_leads']}")
    print(f"Average score: {stats['average_score']}")
    print("\nLeads by status:")
    for status, count in stats['by_status'].items():
        if count > 0:
            print(f"  {status}: {count}")
    
    # Email template demonstration
    print("\n3. Email Templates")
    print("-" * 60)
    print("Available templates:")
    for template_name in template_manager.list_templates():
        template = template_manager.get_template(template_name)
        print(f"  - {template_name}: {template.description}")
    
    # Render an email for the first lead
    print("\n4. Rendering Email Template")
    print("-" * 60)
    first_lead = created_leads[0]
    
    email = template_manager.render_template("initial_outreach", {
        "first_name": first_lead.first_name,
        "company": first_lead.company,
        "industry": "SaaS",
        "pain_point": "scaling their engineering team",
        "sender_name": "Alex Thompson"
    })
    
    print(f"To: {first_lead.email}")
    print(f"Subject: {email['subject']}")
    print(f"\n{email['body']}")
    
    # Track outreach
    print("\n5. Tracking Outreach")
    print("-" * 60)
    
    # Create outreach records for all leads
    for lead in created_leads:
        outreach = outreach_tracker.create_outreach(
            lead_id=lead.id,
            template_name="initial_outreach",
            subject=f"Quick question about {lead.company}"
        )
        # Mark as sent
        outreach_tracker.mark_sent(outreach.id)
        print(f"✓ Tracked outreach to {lead.get_full_name()}")
    
    # Simulate some responses
    all_records = list(outreach_tracker.records.values())
    if len(all_records) >= 2:
        outreach_tracker.update_status(
            all_records[0].id,
            OutreachStatus.OPENED,
            "Email opened"
        )
        outreach_tracker.update_status(
            all_records[1].id,
            OutreachStatus.REPLIED,
            "Positive response - interested in demo"
        )
        
        # Update lead status for the one who replied
        lead_manager.update_lead(
            all_records[1].lead_id,
            {"status": LeadStatus.QUALIFIED}
        )
    
    # Display outreach statistics
    print("\n6. Outreach Statistics")
    print("-" * 60)
    outreach_stats = outreach_tracker.get_stats()
    print(f"Total outreach: {outreach_stats['total_outreach']}")
    print(f"Response rate: {outreach_stats['response_rate']}%")
    print(f"Open rate: {outreach_stats['open_rate']}%")
    print("\nOutreach by status:")
    for status, count in outreach_stats['by_status'].items():
        if count > 0:
            print(f"  {status}: {count}")
    
    # Search functionality
    print("\n7. Search Functionality")
    print("-" * 60)
    search_query = "TechCorp"
    results = lead_manager.search_leads(search_query)
    print(f"Search results for '{search_query}':")
    for lead in results:
        print(f"  - {lead.get_full_name()} at {lead.company}")
    
    # Filter leads
    print("\n8. Filtering Leads")
    print("-" * 60)
    high_score_leads = lead_manager.list_leads(min_score=80)
    print(f"Leads with score >= 80:")
    for lead in high_score_leads:
        print(f"  - {lead.get_full_name()}: {lead.score}")
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
