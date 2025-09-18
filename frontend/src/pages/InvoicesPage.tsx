// src/pages/InvoicesPage.tsx
import { Box, Heading } from '@chakra-ui/react';
import InvoiceList from '../components/invoices/InvoiceList';

const InvoicesPage = () => {
  return (
    <Box p={6}>
      <Heading as="h1" size="xl" mb={6}>
        Invoices
      </Heading>
      <InvoiceList />
    </Box>
  );
};

export default InvoicesPage;