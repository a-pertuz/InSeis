"""Result object for standardized error handling."""

class Result:
    """
    A result object that contains success/failure information and data.
    Provides a consistent pattern for error handling across the application.
    """
    
    def __init__(self, success=True, data=None, error=None):
        """Initialize a result object."""
        self.success = success
        self.data = data or {}
        self.error = error
        
    @classmethod
    def ok(cls, data=None):
        """Create a successful result."""
        return cls(True, data, None)
        
    @classmethod
    def fail(cls, error="Operation failed", data=None):
        """Create a failed result."""
        return cls(False, data, error)
    
    def __bool__(self):
        """Allow using Result objects in boolean context to check success."""
        return self.success
    
    def __str__(self):
        """String representation for debugging."""
        status = "Success" if self.success else "Failure"
        if self.error:
            return f"{status}: {self.error}"
        return status
