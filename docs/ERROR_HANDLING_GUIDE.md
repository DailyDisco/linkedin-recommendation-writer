# Error Handling Guide

This document outlines the comprehensive error handling strategy implemented in the LinkedIn Recommendation Writer application.

## Table of Contents

1. [Overview](#overview)
2. [Frontend Error Handling](#frontend-error-handling)
   - [Global Error Handling](#global-error-handling)
   - [React Error Boundaries](#react-error-boundaries)
   - [API Error Handling](#api-error-handling)
   - [UI Error Components](#ui-error-components)
3. [Backend Error Handling](#backend-error-handling)
   - [Custom Exceptions](#custom-exceptions)
   - [Middleware Integration](#middleware-integration)
   - [Error Response Format](#error-response-format)
4. [Testing](#testing)
5. [Best Practices](#best-practices)
6. [Usage Examples](#usage-examples)

## Overview

The error handling system is designed to provide:

- **Comprehensive Coverage**: Catches errors at multiple levels (global, component, API, server)
- **User-Friendly Messages**: Provides contextual error messages with recovery suggestions
- **Structured Logging**: Logs errors with sufficient context for debugging
- **Graceful Degradation**: Allows applications to continue functioning when possible
- **Consistent UX**: Unified error display and handling patterns

## Frontend Error Handling

### Global Error Handling

The global error handler catches unhandled errors that occur outside of React's error boundaries.

**Location**: `frontend/app/utils/globalErrorHandler.ts`

**Features**:

- Handles uncaught exceptions
- Handles unhandled promise rejections
- Handles resource loading errors
- Shows user-friendly toast notifications
- Logs structured error information

**Initialization**:

```typescript
import { initializeGlobalErrorHandling } from './utils/globalErrorHandler';

// Initialize in root.tsx
if (typeof window !== 'undefined') {
  initializeGlobalErrorHandling();
}
```

### React Error Boundaries

Enhanced error boundaries provide contextual error handling for React components.

**Location**: `frontend/app/components/ui/error-boundary.tsx`

**Features**:

- Unique error ID generation for tracking
- Contextual error messages based on error type
- Recovery suggestions for users
- Error reporting functionality
- Development mode stack traces

**Usage**:

```typescript
import { ErrorBoundary } from './components/ui/error-boundary';

function MyComponent() {
  return (
    <ErrorBoundary
      errorContext='User Profile Form'
      showErrorReport={true}
      onError={(error, errorInfo, errorId) => {
        // Custom error handling logic
        console.log('Custom error handler:', errorId);
      }}
    >
      <ProfileForm />
    </ErrorBoundary>
  );
}
```

### API Error Handling

Comprehensive API error mapping with user-friendly messages and recovery suggestions.

**Location**: `frontend/app/services/api.ts`

**Error Types**:

- `NETWORK_ERROR`: Network connectivity issues
- `AUTHENTICATION_ERROR`: Authentication failures (401)
- `AUTHORIZATION_ERROR`: Permission issues (403)
- `VALIDATION_ERROR`: Invalid input data (400)
- `NOT_FOUND_ERROR`: Resource not found (404)
- `RATE_LIMIT_ERROR`: Rate limiting (429)
- `SERVER_ERROR`: Server errors (5xx)
- `SERVICE_UNAVAILABLE`: Service unavailable (502-504)
- `TIMEOUT_ERROR`: Request timeouts
- `UNKNOWN_ERROR`: Unclassified errors

**Usage**:

```typescript
import { handleApiError, ApiErrorType } from './services/api';

try {
  const response = await api.get('/users');
} catch (error) {
  const result = handleApiError(error, {
    context: 'User List Loading',
    onRetry: () => fetchUsers(),
  });

  if (result.canRetry && result.onRetry) {
    // Show retry option
  }
}
```

### UI Error Components

Consistent error display components for different contexts.

#### ErrorAlert

General-purpose error alert with suggestions and actions.

```typescript
import { ErrorAlert } from './components/ui/error-alert';

<ErrorAlert
  title='Connection Error'
  message='Unable to connect to the server'
  suggestions={['Check your internet connection', 'Try again in a few minutes']}
  onRetry={() => retryConnection()}
  showRetryButton={true}
/>;
```

#### FormError

Field-level validation error display.

```typescript
import { FormError } from './components/ui/form-error';

<FormError error={formik.errors.email} touched={formik.touched.email} />;
```

#### LoadingError

Error state for loading operations.

```typescript
import { LoadingError } from './components/ui/loading-error';

<LoadingError
  error='Failed to load recommendations'
  onRetry={() => loadRecommendations()}
  isRetrying={loading}
/>;
```

## Backend Error Handling

### Custom Exceptions

Structured exception classes with user-friendly messages and error codes.

**Location**: `backend/app/core/exceptions.py`

**Exception Types**:

- `BaseApplicationError`: Base class for all custom exceptions
- `ValidationError`: Input validation failures
- `NotFoundError`: Resource not found
- `ExternalServiceError`: Third-party service failures
- `GitHubAPIError`: GitHub API specific errors
- `GeminiAPIError`: AI service errors
- `DatabaseError`: Database operation failures
- `CacheError`: Cache operation failures
- `RateLimitError`: Rate limiting violations
- `ConfigurationError`: Configuration issues

**Usage**:

```python
from app.core.exceptions import ValidationError, NotFoundError

def get_user(user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError("User", str(user_id))

    if not user.is_active:
        raise ValidationError("User account is not active")

    return user
```

### Middleware Integration

The error handling middleware processes exceptions and returns consistent error responses.

**Location**: `backend/app/core/middleware.py`

**Features**:

- Automatic exception type detection
- HTTP status code mapping
- PII filtering for logging
- Structured error responses
- Request ID correlation

### Error Response Format

Consistent JSON error response format:

```json
{
  "error": "VALIDATION_ERROR",
  "message": "The provided data is invalid. Please check your input and try again.",
  "type": "validation_error",
  "request_id": "req_123456789",
  "details": {
    "field": "email",
    "issue": "invalid_format"
  }
}
```

## Testing

Comprehensive test coverage for error handling components.

### Frontend Tests

**Global Error Handler Tests** (`frontend/app/utils/__tests__/globalErrorHandler.test.ts`):

- Error context creation
- Event handler functionality
- Toast notification display
- Error logging structure

**Error Boundary Tests** (`frontend/app/components/ui/__tests__/error-boundary.test.tsx`):

- Error boundary rendering
- Error recovery functionality
- Custom fallback components
- Error reporting features

**API Error Tests** (`frontend/app/services/__tests__/api.test.ts`):

- Error type detection
- Error message mapping
- Recovery suggestion generation
- Toast notification handling

### Running Tests

```bash
# Frontend tests
cd frontend
npm test -- --testPathPattern=error

# Backend tests
cd backend
python -m pytest tests/ -k error
```

## Best Practices

### Error Handling Principles

1. **Fail Gracefully**: Always provide fallback UI and recovery options
2. **Be Specific**: Give users actionable error messages, not generic ones
3. **Log Appropriately**: Include context but filter sensitive information
4. **Test Error Paths**: Ensure error states are tested and work correctly
5. **Provide Recovery**: Always give users options to resolve or retry

### Frontend Best Practices

```typescript
// ✅ Good: Specific error handling with context
try {
  await api.generateRecommendation(data);
} catch (error) {
  const result = handleApiError(error, {
    context: 'Recommendation Generation',
    onRetry: () => generateRecommendation(),
  });

  if (result.type === ApiErrorType.AUTHENTICATION_ERROR) {
    // Handle auth-specific logic
    redirectToLogin();
  }
}

// ❌ Bad: Generic error handling
catch (error) {
  console.error(error);
  toast.error('Something went wrong');
}
```

### Backend Best Practices

```python
# ✅ Good: Use specific exceptions with context
def create_recommendation(request_data: dict):
    # Validate input
    if not request_data.get('github_username'):
        raise ValidationError(
            "GitHub username is required",
            field="github_username"
        )

    # Check rate limits
    if is_rate_limited(request.user):
        raise RateLimitError(
            "GitHub API",
            "100 requests per hour"
        )

# ❌ Bad: Generic exceptions
raise Exception("Something failed")
```

### UI/UX Best Practices

1. **Clear Language**: Use simple, non-technical language
2. **Actionable Messages**: Tell users what they can do, not just what went wrong
3. **Progressive Disclosure**: Show basic info first, details on demand
4. **Consistent Styling**: Use the same error components throughout the app
5. **Accessibility**: Ensure error messages are accessible to screen readers

## Usage Examples

### Complete Error Boundary Implementation

```typescript
import { ErrorBoundary } from './components/ui/error-boundary';
import { LoadingError } from './components/ui/loading-error';

function RecommendationForm() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (data: FormData) => {
    setIsLoading(true);
    setError(null);

    try {
      await api.generateRecommendation(data);
      // Success handling
    } catch (err) {
      const result = handleApiError(err, {
        context: 'Recommendation Generation',
        onRetry: () => handleSubmit(data),
      });
      setError(result.message);
    } finally {
      setIsLoading(false);
    }
  };

  if (error) {
    return (
      <LoadingError
        error={error}
        onRetry={() => handleSubmit(formData)}
        isRetrying={isLoading}
      />
    );
  }

  return (
    <ErrorBoundary errorContext='Recommendation Form'>
      <form onSubmit={handleSubmit}>{/* Form content */}</form>
    </ErrorBoundary>
  );
}
```

### Backend API with Proper Error Handling

```python
from fastapi import APIRouter, HTTPException
from app.core.exceptions import ValidationError, NotFoundError, RateLimitError
from app.services.github_service import GitHubService

router = APIRouter()
github_service = GitHubService()

@router.post("/recommendations/generate")
async def generate_recommendation(request: RecommendationRequest):
    try:
        # Validate request
        if not request.github_username:
            raise ValidationError(
                "GitHub username is required",
                field="github_username"
            )

        # Check if user exists on GitHub
        user_data = await github_service.get_user_profile(request.github_username)
        if not user_data:
            raise NotFoundError("GitHub user", request.github_username)

        # Generate recommendation
        recommendation = await generate_ai_recommendation(user_data, request)

        return {"recommendation": recommendation}

    except ValidationError as e:
        # Re-raise to be handled by middleware
        raise
    except NotFoundError as e:
        raise
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Unexpected error in recommendation generation: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while generating the recommendation"
        )
```

### Form Validation with Error Display

```typescript
import { FormError, FormSuccess } from './components/ui/form-error';
import { ErrorAlert } from './components/ui/error-alert';

function GitHubInputForm() {
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  return (
    <form onSubmit={handleSubmit}>
      <div className='space-y-4'>
        <div>
          <label htmlFor='githubUsername'>GitHub Username</label>
          <input
            id='githubUsername'
            name='githubUsername'
            type='text'
            value={formik.values.githubUsername}
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            className={
              formik.errors.githubUsername && formik.touched.githubUsername
                ? 'border-red-500'
                : ''
            }
          />
          <FormError
            error={formik.errors.githubUsername}
            touched={formik.touched.githubUsername}
          />
        </div>

        {submitError && (
          <ErrorAlert
            title='Submission Failed'
            message={submitError}
            onRetry={() => handleSubmit(formik.values)}
            showRetryButton={!isSubmitting}
          />
        )}

        {submitSuccess && (
          <FormSuccess message='Recommendation generated successfully!' />
        )}
      </div>
    </form>
  );
}
```

This comprehensive error handling system ensures that users receive helpful, actionable error messages while providing developers with the information needed to diagnose and fix issues effectively.
