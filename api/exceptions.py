class CrUXApiError(Exception):
    """Base exception for CrUX API errors"""
    pass

class InvalidURLError(CrUXApiError):
    """Exception raised when an invalid URL is provided"""
    pass

class ApiConnectionError(CrUXApiError):
    """Exception raised when there's a connection error to the API"""
    pass

class ApiResponseError(CrUXApiError):
    """Exception raised when the API returns an error"""
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message
        super().__init__(f"API returned error {status_code}: {message}")