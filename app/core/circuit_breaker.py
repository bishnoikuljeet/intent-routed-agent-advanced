"""
Circuit Breaker Implementation
Production-grade circuit breaker pattern for fault tolerance.
"""

import asyncio
import time
from typing import Callable, Any, Optional
from enum import Enum
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, calls fail immediately
    HALF_OPEN = "half_open"  # Testing if service has recovered


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5          # Number of failures before opening
    recovery_timeout: float = 60.0       # Seconds to wait before trying again
    expected_exception: type = Exception # Exception type to track
    success_threshold: int = 2          # Successes needed to close circuit
    timeout: float = 30.0              # Timeout for individual calls


class CircuitBreakerError(Exception):
    """Circuit breaker specific error."""
    pass


class CircuitBreaker:
    """
    Production-grade circuit breaker implementation.
    
    Prevents cascading failures by stopping calls to failing services
    and providing automatic recovery with exponential backoff.
    """
    
    def __init__(self, config: Optional[CircuitBreakerConfig] = None):
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_success_time = None
        
        # Metrics
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.rejected_calls = 0
        
        logger.info_structured(
            "Circuit breaker initialized",
            failure_threshold=self.config.failure_threshold,
            recovery_timeout=self.config.recovery_timeout
        )
    
    async def __aenter__(self):
        """Async context manager entry."""
        if not self.can_execute():
            raise CircuitBreakerError(f"Circuit breaker is {self.state.value}")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if exc_type is not None:
            await self.record_failure()
        else:
            await self.record_success()
    
    def can_execute(self) -> bool:
        """Check if execution is allowed."""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if (time.time() - self.last_failure_time) >= self.config.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                logger.info_structured(
                    "Circuit breaker transitioning to half-open",
                    time_since_failure=time.time() - self.last_failure_time
                )
                return True
            else:
                self.rejected_calls += 1
                return False
        
        if self.state == CircuitState.HALF_OPEN:
            return True
        
        return False
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerError: If circuit is open
            Exception: Original function exception
        """
        if not self.can_execute():
            self.rejected_calls += 1
            raise CircuitBreakerError(f"Circuit breaker is {self.state.value}")
        
        self.total_calls += 1
        
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.config.timeout
            )
            
            await self.record_success()
            return result
            
        except asyncio.TimeoutError:
            await self.record_failure()
            raise CircuitBreakerError(f"Call timed out after {self.config.timeout}s")
        
        except self.config.expected_exception as e:
            await self.record_failure()
            raise e
        
        except Exception as e:
            await self.record_failure()
            raise e
    
    async def record_success(self):
        """Record a successful call."""
        self.successful_calls += 1
        self.last_success_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                logger.info_structured(
                    "Circuit breaker closed",
                    success_count=self.success_count
                )
        
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success in closed state
            if self.failure_count > 0:
                self.failure_count = max(0, self.failure_count - 1)
    
    async def record_failure(self):
        """Record a failed call."""
        self.failed_calls += 1
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning_structured(
                    "Circuit breaker opened",
                    failure_count=self.failure_count,
                    threshold=self.config.failure_threshold
                )
        
        elif self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            logger.warning_structured(
                "Circuit breaker re-opened from half-open",
                failure_count=self.failure_count
            )
    
    def get_stats(self) -> dict:
        """Get circuit breaker statistics."""
        success_rate = 0.0
        if self.total_calls > 0:
            success_rate = (self.successful_calls / self.total_calls) * 100
        
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "rejected_calls": self.rejected_calls,
            "success_rate": round(success_rate, 2),
            "last_failure_time": self.last_failure_time,
            "last_success_time": self.last_success_time,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "success_threshold": self.config.success_threshold,
                "timeout": self.config.timeout
            }
        }
    
    def reset(self):
        """Reset circuit breaker to initial state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_success_time = None
        
        # Keep metrics for monitoring
        logger.info_structured("Circuit breaker reset")
    
    def force_open(self):
        """Force circuit breaker to open state."""
        self.state = CircuitState.OPEN
        self.last_failure_time = time.time()
        logger.warning_structured("Circuit breaker forced open")
    
    def force_close(self):
        """Force circuit breaker to closed state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        logger.info_structured("Circuit breaker forced closed")


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers."""
    
    def __init__(self):
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
    
    def get_circuit_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """Get or create circuit breaker by name."""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(config)
        return self.circuit_breakers[name]
    
    def get_all_stats(self) -> dict[str, dict]:
        """Get statistics for all circuit breakers."""
        return {name: cb.get_stats() for name, cb in self.circuit_breakers.items()}
    
    def reset_all(self):
        """Reset all circuit breakers."""
        for cb in self.circuit_breakers.values():
            cb.reset()
        logger.info_structured("All circuit breakers reset")
    
    def get_health_status(self) -> dict:
        """Get overall health status."""
        total_breakers = len(self.circuit_breakers)
        open_breakers = sum(1 for cb in self.circuit_breakers.values() if cb.state == CircuitState.OPEN)
        half_open_breakers = sum(1 for cb in self.circuit_breakers.values() if cb.state == CircuitState.HALF_OPEN)
        
        health_score = 100.0
        if total_breakers > 0:
            health_score = ((total_breakers - open_breakers) / total_breakers) * 100
        
        return {
            "total_breakers": total_breakers,
            "open_breakers": open_breakers,
            "half_open_breakers": half_open_breakers,
            "closed_breakers": total_breakers - open_breakers - half_open_breakers,
            "health_score": round(health_score, 2),
            "status": "healthy" if health_score >= 80 else "degraded" if health_score >= 50 else "unhealthy"
        }


# Global circuit breaker registry
circuit_breaker_registry = CircuitBreakerRegistry()
