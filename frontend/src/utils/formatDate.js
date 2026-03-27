/**
 * Format a date string from YYYY-MM-DD to DD-MM-YYYY for display.
 * Returns the original string if it can't be parsed.
 */
export function formatDate(dateStr) {
  if (!dateStr) return ''
  const parts = dateStr.split('-')
  if (parts.length !== 3 || parts[0].length !== 4) return dateStr
  return `${parts[2]}-${parts[1]}-${parts[0]}`
}
