import React from 'react'
import type { ProjectRole } from '../../types/api'

interface RoleGuardProps {
  currentRole: ProjectRole
  allowedRoles: ProjectRole[]
  children: React.ReactNode
  fallback?: React.ReactNode
  disableOnly?: boolean
  tooltip?: string
}

export const RoleGuard: React.FC<RoleGuardProps> = ({
  currentRole,
  allowedRoles,
  children,
  fallback = null,
  disableOnly = false,
  tooltip,
}) => {
  const isAllowed = allowedRoles.includes(currentRole) || currentRole === 'admin'

  if (isAllowed) {
    return <>{children}</>
  }

  if (disableOnly && React.isValidElement(children)) {
    const formattedRoles = allowedRoles.map((r) => r.replace('_', ' ')).join(', ')
    const defaultTip = tooltip || `Action restricted. Requires ${formattedRoles} role.`

    return React.cloneElement(children as React.ReactElement<any>, {
      disabled: true,
      title: defaultTip,
      className: `${(children as any).props.className || ''} opacity-40 cursor-not-allowed pointer-events-none`,
    })
  }

  return <>{fallback}</>
}
