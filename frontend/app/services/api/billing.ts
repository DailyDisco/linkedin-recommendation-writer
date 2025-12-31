import { api } from './client';
import type {
  PlansResponse,
  CreditPacksResponse,
  CreditBalance,
  CreditPurchase,
  Subscription,
  Usage,
  FeatureAccess,
  CheckoutResponse,
  PortalResponse,
  ApiKey,
  ApiKeyCreated,
  PackType,
} from '../../types';

/**
 * Billing and subscription API endpoints
 */
export const billingApi = {
  // ========== Plans ==========

  /**
   * Get available subscription plans
   */
  async getPlans(): Promise<PlansResponse> {
    const response = await api.get('/billing/plans');
    return response.data;
  },

  // ========== Credit Packs ==========

  /**
   * Get available credit packs for purchase
   */
  async getCreditPacks(): Promise<CreditPacksResponse> {
    const response = await api.get('/billing/credit-packs');
    return response.data;
  },

  /**
   * Get current credit balance
   */
  async getCreditBalance(): Promise<CreditBalance> {
    const response = await api.get('/billing/credits');
    return response.data;
  },

  /**
   * Purchase a credit pack
   */
  async purchaseCreditPack(data: {
    pack_id: PackType;
    success_url?: string;
    cancel_url?: string;
  }): Promise<CheckoutResponse> {
    const response = await api.post('/billing/credits/purchase', data);
    return response.data;
  },

  /**
   * Get credit purchase history
   */
  async getCreditHistory(): Promise<{ purchases: CreditPurchase[] }> {
    const response = await api.get('/billing/credits/history');
    return response.data;
  },

  // ========== Subscriptions ==========

  /**
   * Create a checkout session for subscription
   */
  async createCheckoutSession(data: {
    price_id: string;
    success_url?: string;
    cancel_url?: string;
  }): Promise<CheckoutResponse> {
    const response = await api.post('/billing/checkout', data);
    return response.data;
  },

  /**
   * Create a billing portal session for subscription management
   */
  async createPortalSession(): Promise<PortalResponse> {
    const response = await api.post('/billing/portal');
    return response.data;
  },

  /**
   * Get current subscription details
   */
  async getSubscription(): Promise<Subscription> {
    const response = await api.get('/billing/subscription');
    return response.data;
  },

  // ========== Usage ==========

  /**
   * Get usage statistics
   */
  async getUsage(): Promise<Usage> {
    const response = await api.get('/billing/usage');
    return response.data;
  },

  /**
   * Get feature access based on current plan
   */
  async getFeatures(): Promise<FeatureAccess> {
    const response = await api.get('/billing/features');
    return response.data;
  },

  // ========== API Keys ==========

  /**
   * Create a new API key
   */
  async createApiKey(data: {
    name: string;
    scopes?: string[];
    expires_in_days?: number;
  }): Promise<ApiKeyCreated> {
    const response = await api.post('/billing/api-keys', data);
    return response.data;
  },

  /**
   * List all API keys
   */
  async listApiKeys(): Promise<{ keys: ApiKey[] }> {
    const response = await api.get('/billing/api-keys');
    return response.data;
  },

  /**
   * Revoke an API key
   */
  async revokeApiKey(keyId: number): Promise<{ success: boolean }> {
    const response = await api.delete(`/billing/api-keys/${keyId}`);
    return response.data;
  },
};
