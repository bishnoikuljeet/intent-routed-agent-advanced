"""
Production Error Handling
Comprehensive error hierarchy and handling for production systems.
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import traceback


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better handling and monitoring."""
    VALIDATION = "validation"
    PROCESSING = "processing"
    EXTERNAL_SERVICE = "external_service"
    TIMEOUT = "timeout"
    RESOURCE = "resource"
    SECURITY = "security"
    INFRASTRUCTURE = "infrastructure"
    BUSINESS_LOGIC = "business_logic"


@dataclass
class ErrorContext:
    """Context information for errors."""
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    component: Optional[str] = None
    operation: Optional[str] = None
    additional_data: Dict[str, Any] = None


class BaseSystemError(Exception):
    """Base class for all system errors."""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.PROCESSING,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[ErrorContext] = None,
        cause: Optional[Exception] = None,
        user_message: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.context = context or ErrorContext()
        self.cause = cause
        self.user_message = user_message or self._generate_user_message()
        self.timestamp = None  # Will be set when raised
    
    def _generate_user_message(self) -> str:
        """Generate user-friendly error message."""
        if self.severity == ErrorSeverity.CRITICAL:
            return "I'm experiencing technical difficulties. Please try again later."
        elif self.severity == ErrorSeverity.HIGH:
            return "I'm unable to process your request right now. Please try again in a moment."
        elif self.category == ErrorCategory.VALIDATION:
            return "Your request seems incomplete. Could you provide more details?"
        elif self.category == ErrorCategory.TIMEOUT:
            return "Your request is taking longer than expected. Please try again."
        else:
            return "I encountered an issue processing your request. Please try again."
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "user_message": self.user_message,
            "context": {
                "request_id": self.context.request_id,
                "user_id": self.context.user_id,
                "conversation_id": self.context.conversation_id,
                "component": self.context.component,
                "operation": self.context.operation,
                "additional_data": self.context.additional_data or {}
            },
            "cause": str(self.cause) if self.cause else None,
            "traceback": traceback.format_exc() if self.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] else None
        }


class ValidationError(BaseSystemError):
    """Input validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            **kwargs
        )
        self.field = field


class ProcessingError(BaseSystemError):
    """General processing errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.PROCESSING,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )


class ExternalServiceError(BaseSystemError):
    """External service dependency errors."""
    
    def __init__(self, message: str, service_name: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.EXTERNAL_SERVICE,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )
        self.service_name = service_name


class TimeoutError(BaseSystemError):
    """Operation timeout errors."""
    
    def __init__(self, message: str, timeout_seconds: Optional[float] = None, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.TIMEOUT,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )
        self.timeout_seconds = timeout_seconds


class ResourceError(BaseSystemError):
    """Resource exhaustion or allocation errors."""
    
    def __init__(self, message: str, resource_type: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.RESOURCE,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )
        self.resource_type = resource_type


class SecurityError(BaseSystemError):
    """Security-related errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.SECURITY,
            severity=ErrorSeverity.HIGH,
            user_message="Your request was blocked for security reasons.",
            **kwargs
        )


class InfrastructureError(BaseSystemError):
    """Infrastructure or system errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.INFRASTRUCTURE,
            severity=ErrorSeverity.CRITICAL,
            **kwargs
        )


class BusinessLogicError(BaseSystemError):
    """Business logic or domain rule errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.BUSINESS_LOGIC,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )


class PipelineError(BaseSystemError):
    """Pipeline execution errors."""
    
    def __init__(self, message: str, stage: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.PROCESSING,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )
        self.stage = stage


class ContextEnhancementError(BaseSystemError):
    """Context enhancement specific errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.PROCESSING,
            severity=ErrorSeverity.LOW,
            **kwargs
        )


class QualityAssuranceError(BaseSystemError):
    """Quality assurance specific errors."""
    
    def __init__(self, message: str, quality_score: Optional[float] = None, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.PROCESSING,
            severity=ErrorSeverity.LOW,
            **kwargs
        )
        self.quality_score = quality_score


class ErrorHandler:
    """Production-grade error handler."""
    
    def __init__(self):
        self.error_handlers: Dict[ErrorCategory, List[callable]] = {
            category: [] for category in ErrorCategory
        }
    
    def register_handler(self, category: ErrorCategory, handler: callable):
        """Register error handler for specific category."""
        self.error_handlers[category].append(handler)
    
    async def handle_error(self, error: BaseSystemError) -> Dict[str, Any]:
        """Handle error with appropriate handlers."""
        handlers = self.error_handlers.get(error.category, [])
        
        # Execute all handlers for this category
        handler_results = []
        for handler in handlers:
            try:
                result = await handler(error)
                handler_results.append(result)
            except Exception as handler_error:
                # Don't let handler errors break error handling
                handler_results.append({
                    "handler_error": str(handler_error),
                    "status": "failed"
                })
        
        return {
            "error": error.to_dict(),
            "handler_results": handler_results,
            "handled": True
        }
    
    def get_user_message(self, error: BaseSystemError) -> str:
        """Get user-friendly message for error."""
        return error.user_message
    
    def get_severity(self, error: BaseSystemError) -> ErrorSeverity:
        """Get error severity."""
        return error.severity
    
    def should_retry(self, error: BaseSystemError) -> bool:
        """Determine if error is retryable."""
        # Don't retry validation or security errors
        if error.category in [ErrorCategory.VALIDATION, ErrorCategory.SECURITY]:
            return False
        
        # Retry low and medium severity errors
        if error.severity in [ErrorSeverity.LOW, ErrorSeverity.MEDIUM]:
            return True
        
        # Don't retry critical errors
        return False


class ErrorReporter:
    """Error reporting and analytics."""
    
    def __init__(self):
        self.error_counts: Dict[str, int] = {}
        self.error_history: List[Dict[str, Any]] = []
        self.max_history_size = 10000
    
    def report_error(self, error: BaseSystemError):
        """Report an error for analytics."""
        error_key = f"{error.__class__.__name__}:{error.category.value}"
        
        # Increment count
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # Add to history
        error_report = {
            "timestamp": error.timestamp,
            "error_type": error.__class__.__name__,
            "category": error.category.value,
            "severity": error.severity.value,
            "message": error.message,
            "context": error.context.__dict__ if error.context else {}
        }
        
        self.error_history.append(error_report)
        
        # Trim history if needed
        if len(self.error_history) > self.max_history_size:
            self.error_history = self.error_history[-self.max_history_size:]
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary for monitoring."""
        total_errors = sum(self.error_counts.values())
        
        # Group by severity
        severity_counts = {}
        category_counts = {}
        
        for error_report in self.error_history[-1000:]:  # Last 1000 errors
            severity = error_report["severity"]
            category = error_report["category"]
            
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            "total_errors": total_errors,
            "error_types": dict(self.error_counts),
            "recent_severity_breakdown": severity_counts,
            "recent_category_breakdown": category_counts,
            "most_common_errors": sorted(
                self.error_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }
    
    def get_error_rate(self, minutes: int = 60) -> float:
        """Get error rate for recent time period."""
        import time
        cutoff_time = time.time() - (minutes * 60)
        
        recent_errors = [
            error for error in self.error_history
            if error.get("timestamp", 0) >= cutoff_time
        ]
        
        return len(recent_errors) / minutes  # Errors per minute


# Global error handler and reporter
global_error_handler = ErrorHandler()
global_error_reporter = ErrorReporter()
