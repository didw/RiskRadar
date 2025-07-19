import { useEffect } from 'react';
import { useSubscription } from '@apollo/client';
import { RISK_UPDATE_SUBSCRIPTION } from '@/graphql/queries/risk';

interface UseRiskSubscriptionOptions {
  companyId?: string;
  onUpdate?: (data: any) => void;
}

export function useRiskSubscription({ companyId, onUpdate }: UseRiskSubscriptionOptions) {
  const { data, loading, error } = useSubscription(RISK_UPDATE_SUBSCRIPTION, {
    variables: { companyId },
    skip: !companyId,
  });

  useEffect(() => {
    if (data && onUpdate) {
      onUpdate(data.riskUpdate);
    }
  }, [data, onUpdate]);

  return { data: data?.riskUpdate, loading, error };
}