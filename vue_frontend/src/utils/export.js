export function exportToCSV(filename, rows, headers) {
  if (!rows || rows.length === 0) {
    console.warn('No data to export')
    return
  }
  const cols = headers || Object.keys(rows[0])
  const esc = (val) => {
    if (val === null || val === undefined) return ''
    const str = String(val)
    // Escape quotes and wrap in quotes if contains comma or quote
    const safe = str.replace(/"/g, '""')
    return /[",\n]/.test(safe) ? `"${safe}"` : safe
  }
  const headerLine = cols.map(h => esc(h)).join(',')
  const lines = rows.map(r => cols.map(c => esc(r[c])).join(','))
  const csv = [headerLine, ...lines].join('\n')

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', filename)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
