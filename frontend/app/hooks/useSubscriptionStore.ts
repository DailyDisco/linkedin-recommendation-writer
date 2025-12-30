import { create } from 'zustand';
import { billingApi } from '../services/api';
import type {
  Plan,
  Subscription,
  Usage,
  FeatureAccess,
  TierType,
} from '../types';

interface SubscriptionState {
  // State
  subscription: Subscription | null;
  usage: Usage | null;
  plans: Plan[];
  features: FeatureAccess | null;
  isLoading: boolean;
  error: string | null;

  // Computed values
  tier: TierType;
  isProOrHigher: boolean;
  isTeamOrHigher: boolean;
  canGenerate: boolean;
  generationsRemaining: number;
  shouldShowUpgradePrompt: boolean;

  // Actions
  fetchSubscription: () => Promise<void>;
  fetchUsage: () => Promise<void>;
  fetchPlans: () => Promise<void>;
  fetchFeatures: () => Promise<void>;
  refreshAll: () => Promise<void>;
  createCheckout: (priceId: string) => Promise<string>;
  openPortal: () => Promise<string>;
  clearError: () => void;
  reset: () => void;
}

const initialState = {
  subscription: null,
  usage: null,
  plans: [],
  features: null,
  isLoading: false,
  error: null,
};

export const useSubscriptionStore = create<SubscriptionState>((set, get) => ({
  ...initialState,

  // Computed getters
  get tier(): TierType {
    return get().subscription?.tier || 'free';
  },

  get isProOrHigher(): boolean {
    const tier = get().tier;
    return ['pro', 'team', 'admin'].includes(tier);
  },

  get isTeamOrHigher(): boolean {
    const tier = get().tier;
    return ['team', 'admin'].includes(tier);
  },

  get canGenerate(): boolean {
    const usage = get().usage;
    if (!usage) return true; // Assume can generate if no usage data
    if (usage.generations_limit === -1) return true; // Unlimited
    return usage.generations_remaining > 0;
  },

  get generationsRemaining(): number {
    const usage = get().usage;
    if (!usage) return -1;
    return usage.generations_remaining;
  },

  get shouldShowUpgradePrompt(): boolean {
    const usage = get().usage;
    if (!usage) return false;
    if (usage.generations_limit === -1) return false; // Unlimited tier
    return usage.generations_remaining <= 0;
  },

  // Actions
  fetchSubscription: async () => {
    set({ isLoading: true, error: null });
    try {
      const subscription = await billingApi.getSubscription();
      set({ subscription, isLoading: false });
    } catch (error) {
      console.error('Failed to fetch subscription:', error);
      set({
        error: 'Failed to fetch subscription',
        isLoading: false,
      });
    }
  },

  fetchUsage: async () => {
    set({ isLoading: true, error: null });
    try {
      const usage = await billingApi.getUsage();
      set({ usage, isLoading: false });
    } catch (error) {
      console.error('Failed to fetch usage:', error);
      set({
        error: 'Failed to fetch usage',
        isLoading: false,
      });
    }
  },

  fetchPlans: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await billingApi.getPlans();
      set({ plans: response.plans, isLoading: false });
    } catch (error) {
      console.error('Failed to fetch plans:', error);
      set({
        error: 'Failed to fetch plans',
        isLoading: false,
      });
    }
  },

  fetchFeatures: async () => {
    try {
      const features = await billingApi.getFeatures();
      set({ features });
    } catch (error) {
      console.error('Failed to fetch features:', error);
    }
  },

  refreshAll: async () => {
    set({ isLoading: true, error: null });
    try {
      const [subscription, usage, plansResponse, features] = await Promise.all([
        billingApi.getSubscription(),
        billingApi.getUsage(),
        billingApi.getPlans(),
        billingApi.getFeatures(),
      ]);
      set({
        subscription,
        usage,
        plans: plansResponse.plans,
        features,
        isLoading: false,
      });
    } catch (error) {
      console.error('Failed to refresh billing data:', error);
      set({
        error: 'Failed to refresh billing data',
        isLoading: false,
      });
    }
  },

  createCheckout: async (priceId: string): Promise<string> => {
    set({ isLoading: true, error: null });
    try {
      const baseUrl = window.location.origin;
      const response = await billingApi.createCheckoutSession({
        price_id: priceId,
        success_url: `${baseUrl}/checkout/success`,
        cancel_url: `${baseUrl}/checkout/cancel`,
      });
      set({ isLoading: false });
      return response.checkout_url;
    } catch (error) {
      console.error('Failed to create checkout:', error);
      set({
        error: 'Failed to create checkout session',
        isLoading: false,
      });
      throw error;
    }
  },

  openPortal: async (): Promise<string> => {
    set({ isLoading: true, error: null });
    try {
      const response = await billingApi.createPortalSession();
      set({ isLoading: false });
      return response.portal_url;
    } catch (error) {
      console.error('Failed to open portal:', error);
      set({
        error: 'Failed to open billing portal',
        isLoading: false,
      });
      throw error;
    }
  },

  clearError: () => set({ error: null }),

  reset: () => set(initialState),
}));

// Helper hook for checking feature access
export function useFeatureAccess(
  feature: keyof FeatureAccess['features']
): boolean {
  const features = useSubscriptionStore(state => state.features);
  return features?.features[feature] ?? false;
}

// Helper hook for checking tier
export function useTier(): TierType {
  return useSubscriptionStore(state => state.subscription?.tier || 'free');
}

// Helper hook for usage
export function useUsage() {
  const usage = useSubscriptionStore(state => state.usage);
  const fetchUsage = useSubscriptionStore(state => state.fetchUsage);

  return {
    usage,
    fetchUsage,
    generationsUsed: usage?.generations_used || 0,
    generationsLimit: usage?.generations_limit || 3,
    generationsRemaining: usage?.generations_remaining || 0,
    isUnlimited: usage?.generations_limit === -1,
    isAtLimit:
      usage?.generations_remaining === 0 && usage?.generations_limit !== -1,
  };
}
