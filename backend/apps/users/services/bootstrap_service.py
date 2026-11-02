"""Idempotent sample account provisioning without reusable credentials."""
from django.db import transaction

from apps.dealers.models import Dealer, AgentDealerAssignment
from apps.dealers.services.dealer_service import create_dealer, assign_agent_to_dealer
from apps.users.models import CustomUser
from apps.users.services.user_service import create_user

ACCOUNTS = (
    ("superadmin", "superadmin@kevinassurance.com", "SUPER_ADMIN"),
    ("admin_underwriter", "underwriter@kevinassurance.com", "ADMIN"),
    ("agent_budi", "agent.budi@kevinassurance.com", "AGENT"),
    ("dealer_honda_staff", "staff@hondajkt.co.id", "DEALER"),
)


@transaction.atomic
def seed_accounts():
    dealer = Dealer.objects.filter(code="DLR-JKT-001").first()
    if dealer is None:
        dealer = create_dealer({"code": "DLR-JKT-001", "name": "PT Nusantara Honda Motor Jakarta"})
    for username, email, role in ACCOUNTS:
        if not CustomUser.objects.filter(username=username).exists():
            create_user(None, {"username": username, "email": email, "role": role,
                               "dealer": dealer if role == "DEALER" else None,
                               "is_staff": role in ("SUPER_ADMIN", "ADMIN"),
                               "is_superuser": role == "SUPER_ADMIN"})
    agent = CustomUser.objects.get(username="agent_budi")
    if agent.is_agent and not AgentDealerAssignment.objects.filter(agent=agent, dealer=dealer).exists():
        assign_agent_to_dealer(agent, dealer)
