import React from 'react';
import { RouterProvider } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { router } from './router';
import { LocaleProvider } from '../i18n/LocaleContext';
import { AuthProvider } from '../features/auth/AuthContext';
import { ErrorBoundary } from '../components/ui/ErrorBoundary';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
});

export const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <LocaleProvider>
          <AuthProvider>
            <RouterProvider router={router} />
          </AuthProvider>
        </LocaleProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
};

