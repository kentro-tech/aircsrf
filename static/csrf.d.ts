/**
 * Get the CSRF token from the cookie.
 */
export function getCsrfToken(cookieName?: string): string;

/**
 * Set up htmx to automatically include the CSRF token in requests.
 */
export function setupHtmxCsrf(cookieName?: string, headerName?: string): void;

/**
 * Populate all CSRF token hidden inputs in forms.
 */
export function populateFormTokens(cookieName?: string, fieldName?: string): void;

/**
 * Initialize CSRF protection with default settings.
 */
export function initCsrf(options?: {
    cookieName?: string;
    headerName?: string;
    fieldName?: string;
}): void;
