export function formatNumber(value) {
  const numericValue = Number(value || 0);
  return Number.isInteger(numericValue)
    ? numericValue.toString()
    : numericValue.toFixed(2);
}

export function getStatusTone(quantity, threshold) {
  if (quantity < threshold) {
    return "critical";
  }
  if (quantity <= threshold * 1.25) {
    return "warning";
  }
  return "healthy";
}
