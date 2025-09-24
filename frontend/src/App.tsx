// src/App.tsx
import { Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ChakraProvider, Box, Spinner, Center } from '@chakra-ui/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { I18nextProvider } from 'react-i18next';
import i18n from './i18n';
import theme from './theme';

// Import layout
import MainLayout from './layouts/MainLayout';

// Import pages
import DashboardPage from './pages/DashboardPage';
import InvoicesPage from './pages/InvoicesPage';
import InvoiceDetailsPage from './pages/InvoiceDetailsPage';
import NotFound from './pages/NotFound';
import UploadInvoice from './components/UploadInvoice';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

const LoadingSpinner = () => (
  <Center h="100vh">
    <Spinner size="xl" color="blue.500" thickness="4px" />
  </Center>
);

const App = () => {
  return (
    <ChakraProvider theme={theme}>
      <QueryClientProvider client={queryClient}>
        <Box minH="100vh" bg="gray.50">
          <Router>
            <Suspense fallback={<LoadingSpinner />}>
              <I18nextProvider i18n={i18n}>
                <Routes>
                  <Route element={<MainLayout />}>
                    <Route path="/" element={<Navigate to="/dashboard" replace />} />
                    <Route path="/dashboard" element={<DashboardPage />} />
                    <Route path="/invoices/upload" element={<UploadInvoice/>} />
                    <Route path="/invoices" element={<InvoicesPage />} />
                    <Route path="/invoices/:id" element={<InvoiceDetailsPage />} />
                  </Route>
                  <Route path="*" element={<NotFound />} />
                </Routes>
              </I18nextProvider>
            </Suspense>
          </Router>
          {process.env.NODE_ENV === 'development' && (
            <ReactQueryDevtools initialIsOpen={false} />
          )}
        </Box>
      </QueryClientProvider>
    </ChakraProvider>
  );
};

export default App;