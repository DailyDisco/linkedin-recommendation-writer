// Type declaration for gtag
declare global {
  function gtag(...args: unknown[]): void;
}

/**
 * Google Analytics 4 (GA4) utility functions for LinkedIn Recommendation Writer
 */

// GA4 Configuration
const GA4_MEASUREMENT_ID = import.meta.env.VITE_GA4_MEASUREMENT_ID;
const ENABLE_ANALYTICS = import.meta.env.VITE_ENABLE_ANALYTICS === 'true';

/**
 * Initialize Google Analytics 4
 * Call this once when the app starts
 */
export const initializeGA4 = (): void => {
  if (!ENABLE_ANALYTICS || !GA4_MEASUREMENT_ID) {
    console.log('GA4 analytics disabled or measurement ID not configured');
    return;
  }

  // Initialize gtag with GA4 measurement ID
  gtag('js', new Date());
  gtag('config', GA4_MEASUREMENT_ID, {
    debug_mode: import.meta.env.DEV, // Enable debug mode in development
    send_page_view: true, // Automatically track page views
  });

  console.log('GA4 initialized with measurement ID:', GA4_MEASUREMENT_ID);
};

/**
 * Track a custom event
 */
export const trackEvent = (
  eventName: string,
  parameters: Record<string, string | number | boolean> = {}
): void => {
  if (!ENABLE_ANALYTICS || !GA4_MEASUREMENT_ID) {
    console.log(
      'GA4 tracking disabled, would have tracked:',
      eventName,
      parameters
    );
    return;
  }

  gtag('event', eventName, {
    ...parameters,
    timestamp: new Date().toISOString(),
  });

  console.log('GA4 event tracked:', eventName, parameters);
};

/**
 * Track page views manually (useful for SPA route changes)
 */
export const trackPageView = (pagePath: string, pageTitle?: string): void => {
  if (!ENABLE_ANALYTICS || !GA4_MEASUREMENT_ID) {
    console.log(
      'GA4 tracking disabled, would have tracked page view:',
      pagePath
    );
    return;
  }

  gtag('event', 'page_view', {
    page_path: pagePath,
    page_title: pageTitle || document.title,
  });

  console.log('GA4 page view tracked:', pagePath);
};

/**
 * Track user engagement events
 */
export const trackEngagement = {
  // User authentication events
  userLogin: (method: 'email' | 'google' | 'github' = 'email') => {
    trackEvent('login', { method });
  },

  userRegister: (method: 'email' | 'google' | 'github' = 'email') => {
    trackEvent('sign_up', { method });
  },

  userLogout: () => {
    trackEvent('logout');
  },

  // Recommendation generation events
  recommendationGenerated: (
    options: {
      githubUsername?: string;
      tone?: string;
      length?: string;
      hasKeywords?: boolean;
    } = {}
  ) => {
    const params: Record<string, string | number | boolean> = {
      github_username_provided: !!options.githubUsername,
    };
    if (options.tone !== undefined) {
      params.tone = options.tone;
    }
    if (options.length !== undefined) {
      params.length = options.length;
    }
    if (options.hasKeywords !== undefined) {
      params.has_keywords = options.hasKeywords;
    }
    trackEvent('generate_recommendation', params);
  },

  // History and profile events
  viewHistory: () => {
    trackEvent('view_history');
  },

  viewProfile: () => {
    trackEvent('view_profile');
  },

  // GitHub analysis events
  githubProfileAnalyzed: (
    options: {
      repositoriesCount?: number;
      languagesCount?: number;
      hasRecentActivity?: boolean;
    } = {}
  ) => {
    const params: Record<string, string | number | boolean> = {};
    if (options.repositoriesCount !== undefined) {
      params.repositories_count = options.repositoriesCount;
    }
    if (options.languagesCount !== undefined) {
      params.languages_count = options.languagesCount;
    }
    if (options.hasRecentActivity !== undefined) {
      params.has_recent_activity = options.hasRecentActivity;
    }
    trackEvent('github_profile_analyzed', params);
  },

  // Feature usage events
  keywordRefinementUsed: () => {
    trackEvent('keyword_refinement_used');
  },

  recommendationCopied: () => {
    trackEvent('recommendation_copied');
  },

  recommendationEdited: () => {
    trackEvent('recommendation_edited');
  },

  // Error tracking
  errorOccurred: (errorType: string, errorMessage?: string) => {
    const params: Record<string, string | number | boolean> = {
      error_type: errorType,
    };
    if (errorMessage !== undefined) {
      params.error_message = errorMessage.substring(0, 100); // Truncate for privacy
    }
    trackEvent('error_occurred', params);
  },

  // Search and navigation events
  searchPerformed: (searchTerm: string) => {
    trackEvent('search', {
      search_term: searchTerm,
    });
  },

  navigationClick: (destination: string, source?: string) => {
    const params: Record<string, string | number | boolean> = {
      destination,
    };
    if (source !== undefined) {
      params.source = source;
    }
    trackEvent('navigation_click', params);
  },
};

/**
 * Track conversion events (important business metrics)
 */
export const trackConversion = {
  // User completes the full recommendation generation flow
  recommendationCompleted: () => {
    trackEvent('recommendation_completed', {
      value: 1, // Can be adjusted based on business value
      currency: 'USD',
    });
  },

  // User returns after initial visit
  userReturned: (daysSinceLastVisit?: number) => {
    const params: Record<string, string | number | boolean> = {};
    if (daysSinceLastVisit !== undefined) {
      params.days_since_last_visit = daysSinceLastVisit;
    }
    trackEvent('user_returned', params);
  },

  // User engages deeply with the app
  deepEngagement: (sessionDuration: number, actionsCount: number) => {
    trackEvent('deep_engagement', {
      session_duration: sessionDuration,
      actions_count: actionsCount,
    });
  },
};

/**
 * Track performance metrics
 */
export const trackPerformance = {
  apiCallCompleted: (endpoint: string, duration: number, success: boolean) => {
    trackEvent('api_call', {
      endpoint: endpoint,
      duration_ms: duration,
      success: success,
    });
  },

  pageLoadTime: (duration: number, page: string) => {
    trackEvent('page_load', {
      page,
      duration_ms: duration,
    });
  },
};

/**
 * Set user properties for better segmentation
 */
export const setUserProperties = (
  properties: Record<string, string | number | boolean>
): void => {
  if (!ENABLE_ANALYTICS || !GA4_MEASUREMENT_ID) {
    console.log(
      'GA4 tracking disabled, would have set user properties:',
      properties
    );
    return;
  }

  gtag('config', GA4_MEASUREMENT_ID, {
    custom_map: Object.keys(properties).reduce(
      (acc, key, index) => {
        acc[`custom_user_param_${index + 1}`] = key;
        return acc;
      },
      {} as Record<string, string>
    ),
    ...properties,
  });

  console.log('GA4 user properties set:', properties);
};

/**
 * Check if analytics is enabled
 */
export const isAnalyticsEnabled = (): boolean => {
  return ENABLE_ANALYTICS && !!GA4_MEASUREMENT_ID;
};

/**
 * Get current GA4 measurement ID
 */
export const getMeasurementId = (): string | undefined => {
  return GA4_MEASUREMENT_ID;
};
