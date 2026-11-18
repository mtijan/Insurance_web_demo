import type { AppNotification } from '../../types/notification'
import { formatJakartaTime } from '../../utils/roleLabels'

export function NotificationItem({
  item,
  onSelect,
}: {
  item: AppNotification
  onSelect: (item: AppNotification) => void
}) {
  return (
    <li className={item.is_read ? 'notif-item' : 'notif-item unread'}>
      <button type="button" className="notif-item-btn" onClick={() => onSelect(item)}>
        <span className="notif-item-top">
          <strong>{item.title}</strong>
          {!item.is_read && <span className="notif-new-badge">Baru</span>}
        </span>
        <span className="notif-item-msg">{item.message}</span>
        <time className="notif-item-time" dateTime={item.created_at}>
          {formatJakartaTime(item.created_at)}
        </time>
      </button>
    </li>
  )
}
