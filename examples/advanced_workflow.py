"""
Advanced example demonstrating SDR workflow with persistence.

This example shows:
- Using persistent storage
- Multi-stage outreach campaign
- Lead qualification workflow
- Analytics and reporting
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path for direct execution
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from adaml_pluto import Lead, LeadManager, LeadStatus
from adaml_pluto import EmailTemplateManager, OutreachTracker
from adaml_pluto.email_tools.outreach_tracker import OutreachStatus


def setup_data_directory():
    """Create data directory for persistent storage."""
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


def create_sample_leads(manager):
    """Create a diverse set of sample leads."""
    print("\n📊 Creating Sample Leads")
    print("=" * 60)
    
    leads_data = [
        {
            "first_name": "Amanda",
            "last_name": "Peterson",
            "email": "amanda.p@techventures.com",
            "company": "TechVentures Inc",
            "title": "Chief Technology Officer",
            "source": "LinkedIn",
            "score": 95,
            "custom_fields": {"industry": "SaaS", "employees": 250}
        },
        {
            "first_name": "David",
            "last_name": "Kim",
            "email": "d.kim@innovate.ai",
            "company": "Innovate AI",
            "title": "VP of Product",
            "source": "Conference",
            "score": 88,
            "custom_fields": {"industry": "AI/ML", "employees": 150}
        },
        {
            "first_name": "Rachel",
            "last_name": "Martinez",
            "email": "rachel.m@cloudstartup.io",
            "company": "CloudStartup",
            "title": "Head of Engineering",
            "source": "Referral",
            "score": 82,
            "custom_fields": {"industry": "Cloud Services", "employees": 75}
        },
        {
            "first_name": "James",
            "last_name": "Wilson",
            "email": "j.wilson@dataops.com",
            "company": "DataOps Solutions",
            "title": "Director of Sales",
            "source": "Website",
            "score": 70,
            "custom_fields": {"industry": "Data Analytics", "employees": 120}
        },
        {
            "first_name": "Lisa",
            "last_name": "Chen",
            "email": "lisa.chen@devtools.co",
            "company": "DevTools Co",
            "title": "Engineering Manager",
            "source": "LinkedIn",
            "score": 65,
            "custom_fields": {"industry": "Developer Tools", "employees": 50}
        }
    ]
    
    leads = []
    for lead_data in leads_data:
        lead = manager.create_lead(lead_data)
        leads.append(lead)
        industry = lead.custom_fields.get("industry", "N/A")
        print(f"✓ {lead.get_full_name()} - {lead.company}")
        print(f"  {lead.title} | {industry} | Score: {lead.score}")
    
    return leads


def run_outreach_campaign(leads, template_mgr, tracker, manager):
    """Execute a multi-touch outreach campaign."""
    print("\n📧 Running Outreach Campaign")
    print("=" * 60)
    
    for i, lead in enumerate(leads):
        # Determine template based on lead score
        if lead.score >= 85:
            template_name = "value_proposition"
            template_vars = {
                "first_name": lead.first_name,
                "company": lead.company,
                "our_company": "ADAML Solutions",
                "similar_company": "TechCorp",
                "result": "40% increase in sales productivity",
                "sender_name": "Sarah Thompson"
            }
        else:
            template_name = "initial_outreach"
            template_vars = {
                "first_name": lead.first_name,
                "company": lead.company,
                "industry": lead.custom_fields.get("industry", "technology"),
                "pain_point": "improving team efficiency",
                "sender_name": "Sarah Thompson"
            }
        
        # Render and create outreach
        email = template_mgr.render_template(template_name, template_vars)
        outreach = tracker.create_outreach(
            lead_id=lead.id,
            template_name=template_name,
            subject=email['subject']
        )
        
        # Mark as sent
        tracker.mark_sent(outreach.id)
        
        print(f"✓ Sent {template_name} to {lead.get_full_name()}")
        
        # Simulate engagement based on score
        if lead.score >= 90:
            tracker.update_status(outreach.id, OutreachStatus.REPLIED, "Very interested!")
            lead.update_status(LeadStatus.QUALIFIED)
            manager.update_lead(lead.id, {"status": LeadStatus.QUALIFIED})
            print(f"  → REPLIED (Qualified)")
        elif lead.score >= 80:
            tracker.update_status(outreach.id, OutreachStatus.OPENED, "Email opened")
            print(f"  → OPENED")
        elif lead.score >= 70:
            tracker.update_status(outreach.id, OutreachStatus.CLICKED, "Clicked link")
            print(f"  → CLICKED")


def follow_up_with_leads(leads, template_mgr, tracker, manager):
    """Follow up with leads who haven't responded."""
    print("\n🔄 Follow-up Campaign")
    print("=" * 60)
    
    for lead in leads:
        if lead.status == LeadStatus.NEW:
            # Get lead's outreach history
            outreach_history = tracker.get_lead_outreach(lead.id)
            
            # Only follow up if previous outreach wasn't replied
            if outreach_history and outreach_history[-1].status != OutreachStatus.REPLIED:
                # Create follow-up
                email = template_mgr.render_template("follow_up", {
                    "first_name": lead.first_name,
                    "company": lead.company,
                    "topic": "our previous conversation",
                    "sender_name": "Sarah Thompson"
                })
                
                follow_up = tracker.create_outreach(
                    lead_id=lead.id,
                    template_name="follow_up",
                    subject=email['subject']
                )
                tracker.mark_sent(follow_up.id)
                
                print(f"✓ Sent follow-up to {lead.get_full_name()}")
                
                # Simulate some responses to follow-ups
                if lead.score >= 75:
                    tracker.update_status(follow_up.id, OutreachStatus.REPLIED, "Interested now")
                    lead.update_status(LeadStatus.CONTACTED)
                    manager.update_lead(lead.id, {"status": LeadStatus.CONTACTED})
                    print(f"  → REPLIED (Now contacted)")


def show_analytics(manager, tracker):
    """Display comprehensive analytics."""
    print("\n📈 Campaign Analytics")
    print("=" * 60)
    
    # Lead statistics
    lead_stats = manager.get_stats()
    print("\nLead Statistics:")
    print(f"  Total Leads: {lead_stats['total_leads']}")
    print(f"  Average Score: {lead_stats['average_score']}")
    print("\n  By Status:")
    for status, count in lead_stats['by_status'].items():
        if count > 0:
            print(f"    • {status.title()}: {count}")
    
    # Outreach statistics
    outreach_stats = tracker.get_stats()
    print("\nOutreach Statistics:")
    print(f"  Total Outreach: {outreach_stats['total_outreach']}")
    print(f"  Response Rate: {outreach_stats['response_rate']:.1f}%")
    print(f"  Open Rate: {outreach_stats['open_rate']:.1f}%")
    print("\n  By Status:")
    for status, count in outreach_stats['by_status'].items():
        if count > 0:
            print(f"    • {status.title()}: {count}")
    
    # High-value leads
    print("\n💎 High-Value Leads (Score >= 85):")
    high_value = manager.list_leads(min_score=85)
    for lead in high_value:
        print(f"  • {lead.get_full_name()} ({lead.company}) - Score: {lead.score}")
        print(f"    Status: {lead.status.value.title()}")


def main():
    """Run the advanced workflow example."""
    print("=" * 60)
    print("ADAML-Pluto SDR Toolkit - Advanced Workflow Example")
    print("=" * 60)
    
    # Setup data directory
    data_dir = setup_data_directory()
    
    # Initialize managers with persistence
    lead_manager = LeadManager(storage_path=data_dir / "leads.json")
    template_manager = EmailTemplateManager(storage_path=data_dir / "templates.json")
    outreach_tracker = OutreachTracker(storage_path=data_dir / "outreach.json")
    
    # Create leads
    leads = create_sample_leads(lead_manager)
    
    # Run initial outreach campaign
    run_outreach_campaign(leads, template_manager, outreach_tracker, lead_manager)
    
    # Follow up with non-responders
    follow_up_with_leads(leads, template_manager, outreach_tracker, lead_manager)
    
    # Show analytics
    show_analytics(lead_manager, outreach_tracker)
    
    # Show qualified leads
    print("\n🎯 Qualified Leads:")
    print("=" * 60)
    qualified = lead_manager.list_leads(status=LeadStatus.QUALIFIED)
    for lead in qualified:
        print(f"✓ {lead.get_full_name()} - {lead.company}")
        print(f"  Email: {lead.email}")
        print(f"  Score: {lead.score}")
        
        # Show outreach history
        history = outreach_tracker.get_lead_outreach(lead.id)
        print(f"  Outreach History: {len(history)} touches")
    
    print("\n" + "=" * 60)
    print("✅ Advanced workflow completed successfully!")
    print(f"📁 Data saved to: {data_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
