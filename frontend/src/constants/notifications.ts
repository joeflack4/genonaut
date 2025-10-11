import type { KnownNotificationType } from '../services/notification-service'

export const KNOWN_NOTIFICATION_TYPES = [
  'job_completed',
  'job_failed',
  'job_cancelled',
  'system',
  'recommendation',
] as const

export type NotificationFilterType = KnownNotificationType | 'other'

const KNOWN_NOTIFICATION_TYPE_SET = new Set<string>(KNOWN_NOTIFICATION_TYPES)

export const NOTIFICATION_TYPE_LABELS: Record<NotificationFilterType, string> = {
  job_completed: 'Job Completed',
  job_failed: 'Job Failed',
  job_cancelled: 'Job Cancelled',
  system: 'System',
  recommendation: 'Recommendation',
  other: 'Other',
}

export const NOTIFICATION_TYPE_OPTIONS = [
  ...KNOWN_NOTIFICATION_TYPES.map((value) => ({
    value,
    label: NOTIFICATION_TYPE_LABELS[value],
  })),
  { value: 'other' as const, label: NOTIFICATION_TYPE_LABELS.other },
]

export const DEFAULT_NOTIFICATION_TYPES: NotificationFilterType[] = NOTIFICATION_TYPE_OPTIONS.map(
  (option) => option.value as NotificationFilterType
)

export function isKnownNotificationType(value: string): value is KnownNotificationType {
  return KNOWN_NOTIFICATION_TYPE_SET.has(value)
}

export function mapNotificationTypeToFilter(value: string): NotificationFilterType {
  if (value === 'other') {
    return 'other'
  }

  return isKnownNotificationType(value) ? value : 'other'
}

export function getNotificationTypeLabel(value: string): string {
  return NOTIFICATION_TYPE_LABELS[mapNotificationTypeToFilter(value)]
}
