from apps.assurances.models import VehicleAssurance
from apps.notifications.models import Notification, NotificationEventType
from apps.notifications.services.recipient_resolver import resolve_assurance_recipients
from apps.users.models import CustomUser

_ROLE_LABELS = {
    "SUPER_ADMIN": "Super Admin",
    "ADMIN": "Admin",
    "AGENT": "Agent",
    "DEALER": "Dealer",
}

_SECTION_LABELS = {
    "DATA": "Data pengajuan",
    "DOCUMENTS": "Berkas",
    "GENERAL": "Umum",
}


def _actor_label(actor: CustomUser | None) -> str:
    if not actor:
        return "Sistem"
    role = _ROLE_LABELS.get(actor.role, actor.role)
    return f"{role} ({actor.username})"


def _assurance_ref(assurance: VehicleAssurance) -> str:
    if assurance.assurance_number:
        return assurance.assurance_number
    short_id = str(assurance.id)[:8].upper()
    return f"{assurance.dealer.code} #{short_id}"


def _build_copy(assurance: VehicleAssurance, actor: CustomUser | None, event_type: str, section: str) -> tuple[str, str]:
    who = _actor_label(actor)
    ref = _assurance_ref(assurance)
    if event_type == NotificationEventType.ASSURANCE_SUBMITTED:
        return "Pengajuan jaminan dikirim", f"{who} mengirim pengajuan {ref} ({assurance.vehicle_object}) untuk diverifikasi."
    if event_type == NotificationEventType.REVISION_REQUESTED:
        part = _SECTION_LABELS.get(section, "Umum")
        return "Perbaikan pengajuan diminta", f"{who} meminta perbaikan pada {part} untuk pengajuan {ref}."
    if event_type == NotificationEventType.ASSURANCE_APPROVED:
        return "Pengajuan jaminan disetujui", f"{who} menyetujui pengajuan {ref} ({assurance.vehicle_object}); status ACTIVE."
    if event_type == NotificationEventType.ASSURANCE_REJECTED:
        return "Pengajuan jaminan ditolak", f"{who} menolak pengajuan {ref} secara final; lihat rincian alasan."
    return "Catatan baru pada pengajuan", f"{who} menambahkan catatan pada pengajuan {ref}."


def dispatch_assurance_notifications(
    *,
    assurance: VehicleAssurance,
    actor: CustomUser | None,
    event_type: str,
    section: str = "GENERAL",
    dedupe_key: str | None = None,
) -> list[Notification]:
    """Create non-PII in-app notifications inside the active database transaction."""
    recipient_ids = resolve_assurance_recipients(assurance, actor, event_type)
    if not recipient_ids:
        return []
    title, message = _build_copy(assurance, actor, event_type, section)
    target_path = f"/assurances/{assurance.pk}"
    actor_role = actor.role if actor else ""
    actor_username = actor.username if actor else ""
    records = [
        Notification(
            recipient_id=recipient_id,
            actor=actor,
            assurance=assurance,
            event_type=event_type,
            actor_role=actor_role,
            actor_username=actor_username,
            title=title[:120],
            message=message[:255],
            target_path=target_path[:200],
            dedupe_key=dedupe_key[:120] if dedupe_key else None,
        )
        for recipient_id in recipient_ids
    ]
    return Notification.objects.bulk_create(records, ignore_conflicts=bool(dedupe_key))
