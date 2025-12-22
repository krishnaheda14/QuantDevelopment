import { useQuery } from '@tanstack/react-query';
import api from '@/services/api';

/**
 * Custom hook to fetch available trading symbols
 * Reduces code duplication across components
 */
export const useSymbols = () => {
  const { data: symbolsData, ...rest } = useQuery({
    queryKey: ['symbols'],
    queryFn: api.getSymbols,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });

  const symbols = Array.isArray(symbolsData) ? symbolsData : [];

  return { symbols, symbolsData, ...rest };
};
