"""Security validation and content filtering service."""

import re
import logging
import hashlib
import time
from typing import Dict, List, Optional, Set, Any, Tuple
from pathlib import Path
from collections import defaultdict, deque
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ContentFilterResult:
    """Result of content filtering operation."""

    def __init__(self, is_safe: bool, message: str = "", filtered_content: str = "", violations: List[str] = None):
        self.is_safe = is_safe
        self.message = message
        self.filtered_content = filtered_content
        self.violations = violations or []


class RateLimiter:
    """Rate limiter for API endpoints and user actions."""

    def __init__(self):
        """Initialize rate limiter."""
        self.requests = defaultdict(lambda: deque())
        self.blocked_ips = {}
        self.blocked_users = {}

    def is_allowed(
        self,
        identifier: str,
        limit: int,
        window_minutes: int = 60,
        identifier_type: str = "user"
    ) -> Tuple[bool, int]:
        """Check if request is allowed under rate limits.

        Args:
            identifier: User ID, IP address, or other identifier
            limit: Maximum requests allowed in window
            window_minutes: Time window in minutes
            identifier_type: Type of identifier ('user', 'ip', 'global')

        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        now = time.time()
        window_seconds = window_minutes * 60
        cutoff_time = now - window_seconds

        # Check if identifier is blocked
        if identifier_type == "ip" and identifier in self.blocked_ips:
            if now < self.blocked_ips[identifier]:
                return False, 0
            else:
                del self.blocked_ips[identifier]

        if identifier_type == "user" and identifier in self.blocked_users:
            if now < self.blocked_users[identifier]:
                return False, 0
            else:
                del self.blocked_users[identifier]

        # Clean old requests
        requests = self.requests[identifier]
        while requests and requests[0] < cutoff_time:
            requests.popleft()

        # Check limit
        if len(requests) >= limit:
            # Block for extended time if severely over limit
            if len(requests) > limit * 2:
                if identifier_type == "ip":
                    self.blocked_ips[identifier] = now + (window_seconds * 2)
                elif identifier_type == "user":
                    self.blocked_users[identifier] = now + (window_seconds * 2)

                logger.warning(f"Blocked {identifier_type} {identifier} for severe rate limit violation: {len(requests)} requests in window")

            return False, 0

        # Add current request
        requests.append(now)
        remaining = max(0, limit - len(requests))

        return True, remaining

    def get_stats(self, identifier: str) -> Dict[str, Any]:
        """Get rate limiting stats for an identifier.

        Args:
            identifier: Identifier to check

        Returns:
            Dictionary with stats
        """
        now = time.time()
        requests = list(self.requests[identifier])

        # Count recent requests
        recent_1min = sum(1 for req_time in requests if now - req_time <= 60)
        recent_5min = sum(1 for req_time in requests if now - req_time <= 300)
        recent_1hour = sum(1 for req_time in requests if now - req_time <= 3600)

        return {
            "identifier": identifier,
            "requests_last_1min": recent_1min,
            "requests_last_5min": recent_5min,
            "requests_last_1hour": recent_1hour,
            "total_tracked_requests": len(requests),
            "is_blocked_ip": identifier in self.blocked_ips,
            "is_blocked_user": identifier in self.blocked_users
        }


class SecurityService:
    """Service for security validation and content filtering."""

    # Default blocked keywords and patterns @question: What content filtering rules should be applied?
    DEFAULT_BLOCKED_KEYWORDS = {
        # Placeholder patterns - these would be configured based on requirements
        "violence": ["violence", "harm", "kill", "murder", "death", "suicide"],
        "explicit": ["nude", "naked", "sex", "porn", "explicit"],
        "illegal": ["illegal", "drug", "weapon", "bomb"],
        # Add more categories as needed
    }

    # File path validation patterns
    SAFE_PATH_PATTERN = re.compile(r'^[a-zA-Z0-9_\-/\.]+$')
    DANGEROUS_PATH_PATTERNS = [
        re.compile(r'\.\.'),  # Path traversal
        re.compile(r'^/'),    # Absolute paths
        re.compile(r'~'),     # Home directory
        re.compile(r'\$'),    # Environment variables
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize security service.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.rate_limiter = RateLimiter()

        # Content filtering configuration
        self.blocked_keywords = self.config.get('blocked_keywords', self.DEFAULT_BLOCKED_KEYWORDS)
        self.enable_content_filtering = self.config.get('enable_content_filtering', True)
        self.filter_sensitivity = self.config.get('filter_sensitivity', 'medium')  # low, medium, high

        # Rate limiting configuration @question: What rate limits should be applied per user?
        self.rate_limits = self.config.get('rate_limits', {
            'generation_requests_per_hour': 10,
            'api_requests_per_minute': 60,
            'model_list_requests_per_minute': 20
        })

        # Tracking
        self.violation_log = deque(maxlen=1000)
        self.security_stats = {
            'content_filtered': 0,
            'rate_limited': 0,
            'path_violations': 0,
            'total_checks': 0
        }

    def validate_prompt_content(self, prompt: str, negative_prompt: str = "") -> ContentFilterResult:
        """Validate and filter prompt content.

        Args:
            prompt: Main prompt text
            negative_prompt: Negative prompt text

        Returns:
            ContentFilterResult with validation results
        """
        self.security_stats['total_checks'] += 1

        if not self.enable_content_filtering:
            return ContentFilterResult(is_safe=True, filtered_content=prompt)

        violations = []
        full_text = f"{prompt} {negative_prompt}".lower()

        # Check against blocked keywords
        for category, keywords in self.blocked_keywords.items():
            for keyword in keywords:
                if keyword.lower() in full_text:
                    violations.append(f"{category}: {keyword}")

        # Apply sensitivity-based filtering
        if violations:
            if self.filter_sensitivity == 'high':
                # Block any violation
                is_safe = False
                message = f"Content contains inappropriate material: {', '.join(violations)}"
                filtered_content = "[FILTERED]"
            elif self.filter_sensitivity == 'medium':
                # Block serious violations, filter others
                serious_categories = ['violence', 'illegal']
                serious_violations = [v for v in violations if any(cat in v for cat in serious_categories)]

                if serious_violations:
                    is_safe = False
                    message = f"Content contains prohibited material: {', '.join(serious_violations)}"
                    filtered_content = "[FILTERED]"
                else:
                    is_safe = True
                    filtered_content = self._filter_content(prompt, violations)
                    message = f"Content partially filtered: {', '.join(violations)}"
            else:  # low sensitivity
                # Log but allow with filtering
                is_safe = True
                filtered_content = self._filter_content(prompt, violations)
                message = f"Content flagged but allowed: {', '.join(violations)}"
        else:
            is_safe = True
            filtered_content = prompt
            message = "Content approved"

        if violations:
            self.security_stats['content_filtered'] += 1
            self._log_violation("content_filter", {
                "prompt_length": len(prompt),
                "violations": violations,
                "is_safe": is_safe
            })

        return ContentFilterResult(
            is_safe=is_safe,
            message=message,
            filtered_content=filtered_content,
            violations=violations
        )

    def validate_file_path(self, file_path: str, allowed_directories: Optional[List[str]] = None) -> Tuple[bool, str]:
        """Validate file path for security.

        Args:
            file_path: Path to validate
            allowed_directories: List of allowed directory prefixes

        Returns:
            Tuple of (is_valid, error_message)
        """
        self.security_stats['total_checks'] += 1

        # Check for dangerous patterns
        for pattern in self.DANGEROUS_PATH_PATTERNS:
            if pattern.search(file_path):
                self.security_stats['path_violations'] += 1
                self._log_violation("path_traversal", {"path": file_path, "pattern": pattern.pattern})
                return False, f"Path contains dangerous pattern: {file_path}"

        # Check if path matches safe pattern
        if not self.SAFE_PATH_PATTERN.match(file_path):
            self.security_stats['path_violations'] += 1
            self._log_violation("invalid_path_chars", {"path": file_path})
            return False, f"Path contains invalid characters: {file_path}"

        # Check allowed directories
        if allowed_directories:
            path_obj = Path(file_path)
            is_allowed = False
            for allowed_dir in allowed_directories:
                try:
                    if path_obj.resolve().is_relative_to(Path(allowed_dir).resolve()):
                        is_allowed = True
                        break
                except (ValueError, OSError):
                    continue

            if not is_allowed:
                self.security_stats['path_violations'] += 1
                self._log_violation("directory_restriction", {"path": file_path, "allowed": allowed_directories})
                return False, f"Path outside allowed directories: {file_path}"

        return True, "Path validated"

    def check_rate_limit(
        self,
        user_id: str,
        operation: str,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str, int]:
        """Check if user/IP is within rate limits.

        Args:
            user_id: User identifier
            operation: Type of operation
            ip_address: Optional IP address

        Returns:
            Tuple of (is_allowed, message, retry_after_seconds)
        """
        self.security_stats['total_checks'] += 1

        # Define limits for different operations
        operation_limits = {
            'generation_request': (self.rate_limits['generation_requests_per_hour'], 60),  # (limit, window_minutes)
            'api_request': (self.rate_limits['api_requests_per_minute'], 1),
            'model_list': (self.rate_limits['model_list_requests_per_minute'], 1)
        }

        limit, window_minutes = operation_limits.get(operation, (60, 1))  # Default limit

        # Check user rate limit
        user_allowed, user_remaining = self.rate_limiter.is_allowed(
            f"user:{user_id}", limit, window_minutes, "user"
        )

        if not user_allowed:
            self.security_stats['rate_limited'] += 1
            self._log_violation("rate_limit_user", {
                "user_id": user_id,
                "operation": operation,
                "limit": limit,
                "window_minutes": window_minutes
            })
            return False, f"Rate limit exceeded for operation '{operation}'", window_minutes * 60

        # Check IP rate limit if provided
        if ip_address:
            ip_limit = limit * 5  # More generous for IP-based limiting
            ip_allowed, ip_remaining = self.rate_limiter.is_allowed(
                f"ip:{ip_address}", ip_limit, window_minutes, "ip"
            )

            if not ip_allowed:
                self.security_stats['rate_limited'] += 1
                self._log_violation("rate_limit_ip", {
                    "ip_address": ip_address,
                    "operation": operation,
                    "limit": ip_limit,
                    "window_minutes": window_minutes
                })
                return False, f"Rate limit exceeded for IP address", window_minutes * 60

        return True, f"Rate limit check passed ({user_remaining} remaining)", 0

    def validate_generation_parameters(self, params: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate generation parameters for security and reasonableness.

        Args:
            params: Generation parameters dictionary

        Returns:
            Tuple of (is_valid, error_messages)
        """
        self.security_stats['total_checks'] += 1
        errors = []

        # Validate image dimensions
        width = params.get('width', 512)
        height = params.get('height', 512)

        if not isinstance(width, int) or width < 64 or width > 2048:
            errors.append("Width must be between 64 and 2048 pixels")

        if not isinstance(height, int) or height < 64 or height > 2048:
            errors.append("Height must be between 64 and 2048 pixels")

        # Check for reasonable image sizes (prevent memory issues)
        if width * height > 2048 * 2048:
            errors.append("Image dimensions too large (maximum 2048x2048)")

        # Validate batch size
        batch_size = params.get('batch_size', 1)
        if not isinstance(batch_size, int) or batch_size < 1 or batch_size > 4:
            errors.append("Batch size must be between 1 and 4")

        # Validate sampling steps
        steps = params.get('sampler_params', {}).get('steps', 20)
        if not isinstance(steps, int) or steps < 1 or steps > 100:
            errors.append("Sampling steps must be between 1 and 100")

        # Validate CFG scale
        cfg = params.get('sampler_params', {}).get('cfg', 7.0)
        if not isinstance(cfg, (int, float)) or cfg < 1.0 or cfg > 30.0:
            errors.append("CFG scale must be between 1.0 and 30.0")

        # Validate model names (basic sanitization)
        checkpoint_model = params.get('checkpoint_model', '')
        if not self._is_safe_model_name(checkpoint_model):
            errors.append("Invalid checkpoint model name")

        lora_models = params.get('lora_models', [])
        for lora in lora_models:
            if not self._is_safe_model_name(lora.get('name', '')):
                errors.append(f"Invalid LoRA model name: {lora.get('name', '')}")

        if errors:
            self._log_violation("parameter_validation", {
                "errors": errors,
                "params": params
            })

        return len(errors) == 0, errors

    def _filter_content(self, content: str, violations: List[str]) -> str:
        """Filter inappropriate content from text.

        Args:
            content: Original content
            violations: List of violations found

        Returns:
            Filtered content
        """
        filtered = content

        # Simple keyword replacement
        for violation in violations:
            if ':' in violation:
                keyword = violation.split(':')[1].strip()
                filtered = re.sub(re.escape(keyword), '[FILTERED]', filtered, flags=re.IGNORECASE)

        return filtered

    def _is_safe_model_name(self, name: str) -> bool:
        """Check if model name is safe.

        Args:
            name: Model name to check

        Returns:
            True if safe
        """
        if not name or not isinstance(name, str):
            return False

        # Allow only alphanumeric, underscores, hyphens, dots, and spaces
        safe_pattern = re.compile(r'^[a-zA-Z0-9_\-\.\s]+$')
        return bool(safe_pattern.match(name)) and len(name) <= 255

    def _log_violation(self, violation_type: str, details: Dict[str, Any]) -> None:
        """Log security violation.

        Args:
            violation_type: Type of violation
            details: Violation details
        """
        violation_record = {
            'timestamp': datetime.utcnow(),
            'type': violation_type,
            'details': details
        }

        self.violation_log.append(violation_record)

        logger.warning(f"Security violation: {violation_type} - {details}")

    def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics.

        Returns:
            Dictionary with security statistics
        """
        recent_violations = [
            v for v in self.violation_log
            if v['timestamp'] > datetime.utcnow() - timedelta(hours=24)
        ]

        violation_types = {}
        for violation in recent_violations:
            violation_type = violation['type']
            violation_types[violation_type] = violation_types.get(violation_type, 0) + 1

        return {
            **self.security_stats,
            'recent_violations_24h': len(recent_violations),
            'violation_types': violation_types,
            'total_violations': len(self.violation_log)
        }

    def get_recent_violations(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent security violations.

        Args:
            hours: Hours to look back

        Returns:
            List of violation records
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [
            v for v in self.violation_log
            if v['timestamp'] > cutoff_time
        ]


# Global security service instance
_security_service = SecurityService()


def get_security_service() -> SecurityService:
    """Get the global security service instance."""
    return _security_service


def validate_prompt_content(prompt: str, negative_prompt: str = "") -> ContentFilterResult:
    """Convenience function to validate prompt content."""
    return _security_service.validate_prompt_content(prompt, negative_prompt)


def check_rate_limit(user_id: str, operation: str, ip_address: Optional[str] = None) -> Tuple[bool, str, int]:
    """Convenience function to check rate limits."""
    return _security_service.check_rate_limit(user_id, operation, ip_address)