/**
 * Shared Role Types
 * 
 * Canonical source for user role definitions and utilities.
 * All role-related types and functions should be imported from here.
 */

export type UserRole = 'admin' | 'owner' | 'operations' | 'guest'

/**
 * Get the user's role based on their user type string.
 * 
 * @param userType - The user type from Frappe (e.g., 'System Manager', 'Operations User', 'Item Owner')
 * @returns The mapped UserRole
 */
export function getUserRole(userType: string | null | undefined): UserRole {
  if (!userType) return 'guest'
  
  const userTypeLower = userType.toLowerCase()
  
  // Admin roles: explicit admin or system manager
  if (userTypeLower.includes('admin') || userTypeLower.includes('system manager')) {
    return 'admin'
  }
  
  // Operations roles: operations or support
  if (userTypeLower.includes('operations') || userTypeLower.includes('support')) {
    return 'operations'
  }
  
  // Owner roles: explicit owner
  if (userTypeLower.includes('owner')) {
    return 'owner'
  }
  
  // Default for authenticated users without explicit role
  return 'owner'
}
