import { apiClient } from './client';

export interface WalletBalanceResponse {
  user_id: string;
  balance: number;
  currency: string;
}

export interface PaymentChargeResponse {
  id: string;
  code: string;
  hosted_url: string;
  amount: number;
  currency: string;
  status: string;
  expires_at: string;
  metadata: Record<string, string>;
}

export interface CreateDepositChargeRequest {
  user_id: string;
  amount: number;
  redirect_url?: string;
}

export const paymentsApi = {
  getBalance: async (userId: string): Promise<WalletBalanceResponse> => {
    const { data } = await apiClient.get<WalletBalanceResponse>(`/payments/balance/${userId}`);
    return data;
  },

  createDepositCharge: async (request: CreateDepositChargeRequest): Promise<PaymentChargeResponse> => {
    const { data } = await apiClient.post<PaymentChargeResponse>('/payments/charges/deposit', request);
    return data;
  },
};
