const STATUS_LABELS = {
  pending: 'Pending',
  under_review: 'Under Review',
  request_documentation: 'Docs Requested',
  approved: 'Approved',
  rejected: 'Rejected',
}

const STATUS_BADGES = {
  approved: 'badge-green',
  rejected: 'badge-red',
  pending: 'badge-yellow',
  under_review: 'badge-blue',
  request_documentation: 'badge-orange',
}

export function useLeaveFormatting() {
  function fmtDate(s) {
    if (!s) return '—'
    try {
      return new Date(s).toLocaleDateString('en-ZA', { year: 'numeric', month: 'short', day: '2-digit' })
    } catch {
      return s
    }
  }

  function statusLabel(s) {
    return STATUS_LABELS[(s || '').toLowerCase()] || s
  }

  function statusBadge(s) {
    return STATUS_BADGES[(s || '').toLowerCase()] || 'badge-gray'
  }

  return { fmtDate, statusLabel, statusBadge }
}
