// src/pages/InvoiceDetails.tsx
import { useParams } from 'react-router-dom';
import { Box, Heading, Text } from '@chakra-ui/react';
import { useTranslation } from 'react-i18next';

const InvoiceDetails = () => {
  const { id } = useParams<{ id: string }>();
  const { t } = useTranslation('common');
  
  return (
    <Box p={6}>
      <Heading as="h1" size="xl" mb={6}>
        {t('invoice.title', 'Invoice')} #{id}
      </Heading>
      {/* Add your invoice details component here */}
    </Box>
  );
};

export default InvoiceDetails;