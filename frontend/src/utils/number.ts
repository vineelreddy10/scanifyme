/**
 * Safe numeric utilities for frontend rendering.
 *
 * Prevents runtime crashes when API data contains:
 * - undefined
 * - null
 * - NaN
 * - non-numeric values
 *
 * RULE: All numeric formatting (toFixed, Math.round, etc.)
 * MUST go through these safe utilities. Never call .toFixed()
 * directly on potentially-undefined values.
 */

/**
 * Check if a value is a valid, finite number.
 * Rejects: undefined, null, NaN, Infinity, -Infinity, non-numbers.
 *
 * @example
 * isValidNumber(123.456)    // true
 * isValidNumber(undefined)  // false
 * isValidNumber(null)       // false
 * isValidNumber(NaN)        // false
 * isValidNumber('123')      // false (string)
 * isValidNumber(Infinity)   // false
 */
export function isValidNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value)
}

/**
 * Safely call toFixed() on a value, returning a fallback on failure.
 *
 * @param value - The value to format (may be undefined, null, NaN, etc.)
 * @param digits - Number of decimal places (default: 2)
 * @param fallback - What to return when value is not a valid number (default: '-')
 * @returns Formatted string or fallback
 *
 * @example
 * safeToFixed(123.456, 2)           // '123.46'
 * safeToFixed(undefined, 2)          // '-'
 * safeToFixed(null, 2, 'N/A')       // 'N/A'
 * safeToFixed(123.456, 6)            // '123.456000'
 * safeToFixed('not a number', 2)     // '-'
 */
export function safeToFixed(
  value: unknown,
  digits: number = 2,
  fallback: string = '—'
): string {
  if (isValidNumber(value)) {
    return value.toFixed(digits)
  }
  return fallback
}

/**
 * Safely round a numeric value, returning a fallback on failure.
 *
 * @param value - The value to round
 * @param fallback - What to return when value is not a valid number (default: 0)
 * @returns Rounded number or fallback
 *
 * @example
 * safeRound(123.5)          // 124
 * safeRound(undefined)      // 0
 * safeRound(123.4)          // 123
 * safeRound('bad', 999)     // 999
 */
export function safeRound(value: unknown, fallback: number = 0): number {
  if (isValidNumber(value)) {
    return Math.round(value)
  }
  return fallback
}

/**
 * Safely perform a math operation on a value, returning a fallback on failure.
 * Use this when you need to chain multiple operations (e.g., divide then round).
 *
 * @param value - The value to operate on
 * @param operation - Function that takes a number and returns a result
 * @param fallback - What to return when value is not a valid number
 * @returns Result of operation or fallback
 *
 * @example
 * safeMath(150, (n) => n / 3, 0)           // 50
 * safeMath(undefined, (n) => n / 3, 0)     // 0
 * safeMath(150, (n) => Math.floor(n / 3), 0) // 50
 */
export function safeMath<T = number>(
  value: unknown,
  operation: (n: number) => T,
  fallback: T
): T {
  if (isValidNumber(value)) {
    return operation(value)
  }
  return fallback
}

/**
 * Safely parse a string to number, returning a fallback on failure.
 *
 * @param value - The value to parse
 * @param fallback - What to return when value is not a valid number (default: 0)
 * @returns Parsed number or fallback
 *
 * @example
 * safeParseNumber('123.45')    // 123.45
 * safeParseNumber(123)         // 123
 * safeParseNumber(undefined)    // 0
 * safeParseNumber('not a num') // 0
 * safeParseNumber('123', -1)   // 123
 */
export function safeParseNumber(value: unknown, fallback: number = 0): number {
  if (isValidNumber(value)) {
    return value
  }
  if (typeof value === 'string') {
    const parsed = parseFloat(value)
    if (Number.isFinite(parsed)) {
      return parsed
    }
  }
  return fallback
}
