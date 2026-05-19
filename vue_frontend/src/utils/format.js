export function formatCurrencyZAR(value) {
  const num = Number(value || 0)
  return new Intl.NumberFormat('en-ZA', {
    style: 'currency',
    currency: 'ZAR',
    minimumFractionDigits: 2,
  }).format(num)
}

export function formatNumber(value) {
  const num = Number(value || 0)
  return new Intl.NumberFormat('en-ZA').format(num)
}
