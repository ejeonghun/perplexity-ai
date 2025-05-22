import platform
import browser_cookie3 # type: ignore

# Define a set of common browser functions to try from browser_cookie3
# This helps in iterating and also if some browsers are not available on a particular OS.
SUPPORTED_BROWSERS_FUNCTIONS = [
    browser_cookie3.chrome,
    browser_cookie3.firefox,
    browser_cookie3.edge,
    browser_cookie3.safari,
    browser_cookie3.chromium,
    browser_cookie3.opera,
    browser_cookie3.brave,
    browser_cookie3.vivaldi,
    # Add other browser functions from browser_cookie3 if needed
]

def get_perplexity_cookies() -> dict:
    '''
    Attempts to fetch cookies for the domain ".perplexity.ai" from various installed browsers.

    Returns:
        A dictionary of cookie_name: cookie_value pairs if found, otherwise an empty dictionary.
    '''
    cookies_found = {}
    os_name = platform.system()
    print(f"[browser_cookie_fetcher] Detected OS: {os_name}")

    for browser_func in SUPPORTED_BROWSERS_FUNCTIONS:
        try:
            print(f"[browser_cookie_fetcher] Trying browser: {browser_func.__name__}...")
            # browser_cookie3 functions load cookies for all domains by default.
            # We need to filter for ".perplexity.ai"
            # The domain_name parameter in browser_cookie3 functions filters cookies
            # that are "for" that domain, including subdomains if the cookie is set that way.
            # Perplexity.ai cookies are typically set for ".perplexity.ai"
            cj = browser_func(domain_name=".perplexity.ai")
            
            for cookie in cj:
                if cookie.domain.endswith("perplexity.ai"): # Ensure it's for the correct domain
                    cookies_found[cookie.name] = cookie.value
            
            if cookies_found:
                print(f"[browser_cookie_fetcher] Found {len(cookies_found)} cookies for .perplexity.ai in {browser_func.__name__}.")
                # Return on first success to avoid mixing cookies from multiple browsers if that's not desired
                # Or, could collect from all and merge, but let's start with first-found.
                return cookies_found 
        except browser_cookie3.BrowserCookieError as e:
            print(f"[browser_cookie_fetcher] No cookies found or error with {browser_func.__name__}: {e}")
        except Exception as e:
            # Catch other potential errors, e.g., if a browser is not installed
            # or if there's an unexpected issue with the library.
            print(f"[browser_cookie_fetcher] Error accessing cookies for {browser_func.__name__}: {e}")

    if not cookies_found:
        print("[browser_cookie_fetcher] No .perplexity.ai cookies found in any supported browser.")
    
    return cookies_found

if __name__ == '__main__':
    # For testing the module directly
    print("Attempting to fetch .perplexity.ai cookies...")
    cookies = get_perplexity_cookies()
    if cookies:
        print("\nFetched Cookies:")
        for name, value in cookies.items():
            print(f"  {name}: {value}")
    else:
        print("\nNo cookies found.")
