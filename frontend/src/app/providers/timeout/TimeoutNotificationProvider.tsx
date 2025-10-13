import type { PropsWithChildren } from 'react'
import { createContext, useContext, useEffect, useMemo, useState } from 'react'

import type { StatementTimeoutEvent } from '../../../services/api-client'
import { addStatementTimeoutListener } from '../../../services/api-client'

interface TimeoutNotificationContextValue {
  event: StatementTimeoutEvent | null
  dismiss: () => void
}

const TimeoutNotificationContext = createContext<TimeoutNotificationContextValue | undefined>(undefined)

export function TimeoutNotificationProvider({ children }: PropsWithChildren) {
  const [event, setEvent] = useState<StatementTimeoutEvent | null>(null)

  useEffect(() => {
    return addStatementTimeoutListener((payload) => {
      setEvent(payload)
    })
  }, [])

  const value = useMemo<TimeoutNotificationContextValue>(
    () => ({
      event,
      dismiss: () => setEvent(null),
    }),
    [event],
  )

  return (
    <TimeoutNotificationContext.Provider value={value}>{children}</TimeoutNotificationContext.Provider>
  )
}

export function useTimeoutNotificationContext(): TimeoutNotificationContextValue {
  const context = useContext(TimeoutNotificationContext)
  if (!context) {
    throw new Error('useTimeoutNotificationContext must be used within a TimeoutNotificationProvider')
  }
  return context
}
