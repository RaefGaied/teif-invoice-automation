// src/pages/NotFound.tsx
import { Box, Button, Container, Heading, Text } from '@chakra-ui/react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

const NotFound = () => {
  const navigate = useNavigate();
  const { t } = useTranslation('common');

  return (
    <Container maxW="container.md" py={20} textAlign="center">
      <Heading as="h1" size="2xl" mb={4}>
        404
      </Heading>
      <Text fontSize="xl" mb={8}>
        {t('notFound.message', 'Page not found')}
      </Text>
      <Button colorScheme="blue" onClick={() => navigate('/')}>
        {t('actions.backToHome', 'Back to Home')}
      </Button>
    </Container>
  );
};

export default NotFound;