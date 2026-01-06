/**
 * CSRF protection utilities for browser-side token handling.
 * Supports htmx integration and traditional form submissions.
 */

/**
 * Get the CSRF token from the cookie.
 * @param {string} [cookieName='XSRF-TOKEN'] - Name of the cookie containing the token.
 * @returns {string} The CSRF token or empty string if not found.
 */
export function getCsrfToken(cookieName = 'XSRF-TOKEN') {
    const match = document.cookie.match(new RegExp(`(?:^|; )${cookieName}=([^;]+)`));
    return match ? match[1] : '';
}

/**
 * Set up htmx to automatically include the CSRF token in requests.
 * @param {string} [cookieName='XSRF-TOKEN'] - Name of the cookie containing the token.
 * @param {string} [headerName='X-CSRF-Token'] - Name of the header to set.
 */
export function setupHtmxCsrf(cookieName = 'XSRF-TOKEN', headerName = 'X-CSRF-Token') {
    if (typeof window !== 'undefined' && window.htmx) {
        document.body.addEventListener('htmx:configRequest', (evt) => {
            evt.detail.headers[headerName] = getCsrfToken(cookieName);
        });
    }
}

/**
 * Populate all CSRF token hidden inputs in forms.
 * @param {string} [cookieName='XSRF-TOKEN'] - Name of the cookie containing the token.
 * @param {string} [fieldName='csrf_token'] - Name of the form field to populate.
 */
export function populateFormTokens(cookieName = 'XSRF-TOKEN', fieldName = 'csrf_token') {
    const token = getCsrfToken(cookieName);
    document.querySelectorAll(`input[name="${fieldName}"]`).forEach((input) => {
        input.value = token;
    });
}

/**
 * Initialize CSRF protection with default settings.
 * Sets up htmx integration and populates form tokens.
 * @param {Object} [options] - Configuration options.
 * @param {string} [options.cookieName='XSRF-TOKEN'] - Cookie name.
 * @param {string} [options.headerName='X-CSRF-Token'] - Header name for htmx.
 * @param {string} [options.fieldName='csrf_token'] - Form field name.
 */
export function initCsrf(options = {}) {
    const {
        cookieName = 'XSRF-TOKEN',
        headerName = 'X-CSRF-Token',
        fieldName = 'csrf_token'
    } = options;
    
    setupHtmxCsrf(cookieName, headerName);
    populateFormTokens(cookieName, fieldName);
}

if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
        initCsrf();
    });
}
