import { Box, VStack, HStack, Text, Button, useDisclosure, useToast, useColorModeValue } from '@chakra-ui/react';
import { FiUpload, FiFileText, FiDownload, FiRefreshCw } from 'react-icons/fi';
import { useTranslation } from 'react-i18next';
import { useTeif } from '../../../hooks/useTeif';
import { TeifStatusBadge } from './TeifStatusBadge';
import { TeifUploadModal } from './TeifUploadModal';
import { TeifPreviewModal } from './TeifPreviewModal';

interface TeifManagerProps {
  invoiceId: number;
  invoiceNumber?: string;
  teifStatus?: 'pending' | 'generating' | 'generated' | 'signed' | 'error';
  lastUpdated?: Date | string;
  onRefresh?: () => void;
  onTeifGenerated?: () => void;
}

export const TeifManager = ({
  invoiceId,
  invoiceNumber,
  teifStatus = 'pending',
  lastUpdated,
  onRefresh,
  onTeifGenerated,
}: TeifManagerProps) => {
  const { t } = useTranslation();
  const toast = useToast();
  
  // Color mode values
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const textMuted = useColorModeValue('gray.600', 'gray.400');
  
  // Modals
  const {
    isOpen: isUploadModalOpen,
    onOpen: onOpenUploadModal,
    onClose: onCloseUploadModal,
  } = useDisclosure();
  
  const {
    isOpen: isPreviewOpen,
    onOpen: onOpenPreview,
    onClose: onClosePreview,
  } = useDisclosure();

  // TEIF hooks
  const {
    generateTeif,
    downloadTeif,
    previewTeif,
    clearPreview,
    isGenerating,
    previewUrl,
  } = useTeif(invoiceId);

  const handleGenerateTeif = async () => {
    try {
      await generateTeif.mutateAsync();
      toast({
        title: t('teif.generation.success'),
        status: 'success',
        duration: 3000,
        isClosable: true,
        position: 'top-right',
      });
      if (onTeifGenerated) {
        onTeifGenerated();
      }
    } catch (error) {
      console.error('Failed to generate TEIF:', error);
      toast({
        title: t('common.error'),
        description: t('teif.generation.error'),
        status: 'error',
        duration: 5000,
        isClosable: true,
        position: 'top-right',
      });
    }
  };

  const handleDownloadTeif = async () => {
    try {
      const fileName = invoiceNumber ? `facture_${invoiceNumber}.xml` : undefined;
      await downloadTeif(fileName);
    } catch (error) {
      toast({
        title: t('common.error'),
        description: t('teif.download.error'),
        status: 'error',
        duration: 5000,
        isClosable: true,
        position: 'top-right',
      });
    }
  };

  const handlePreviewTeif = async () => {
    try {
      await previewTeif();
      onOpenPreview();
    } catch (error) {
      console.error('Failed to load TEIF preview:', error);
      toast({
        title: t('common.error'),
        description: t('teif.preview.error'),
        status: 'error',
        duration: 5000,
        isClosable: true,
        position: 'top-right',
      });
    }
  };

  const handleUploadSuccess = () => {
    onCloseUploadModal();
    if (onTeifGenerated) {
      onTeifGenerated();
    }
  };

  return (
    <Box 
      w="100%"
      borderRadius="lg"
      overflow="hidden"
      boxShadow="sm"
      borderWidth="1px"
      borderColor={borderColor}
      bg={cardBg}
    >
      <Box 
        px={6} 
        py={4} 
        borderBottomWidth="1px"
        borderColor={borderColor}
        bg={useColorModeValue('gray.50', 'gray.900')}
      >
        <Text fontSize="lg" fontWeight="semibold">
          {t('teif.title')}
        </Text>
        <Text fontSize="sm" color={textMuted} mt={1}>
          {t('teif.subtitle')}
        </Text>
      </Box>

      <VStack spacing={4} p={6} align="stretch">
        {/* Status Bar */}
        <Box 
          p={4}
          borderRadius="md"
          borderWidth="1px"
          borderColor={borderColor}
          bg={useColorModeValue('white', 'gray.700')}
        >
          <HStack justifyContent="space-between" alignItems="center">
            <HStack spacing={4}>
              <TeifStatusBadge status={teifStatus} lastUpdated={lastUpdated} />
              <Text fontSize="sm" color={textMuted}>
                {lastUpdated 
                  ? `${t('teif.lastUpdated')}: ${new Date(lastUpdated).toLocaleString()}` 
                  : t('teif.neverGenerated')}
              </Text>
            </HStack>
            <Button
              size="sm"
              variant="ghost"
              leftIcon={<FiRefreshCw size="16px" />}
              onClick={onRefresh}
              isLoading={isGenerating}
              colorScheme="blue"
              _hover={{ bg: useColorModeValue('blue.50', 'blue.900') }}
            >
              {t('common.refresh')}
            </Button>
          </HStack>
        </Box>

        {/* Action Buttons */}
        <HStack spacing={3} flexWrap="wrap">
          <Button
            leftIcon={<FiUpload size="16px" />}
            colorScheme="blue"
            onClick={onOpenUploadModal}
            isDisabled={isGenerating}
            size="md"
            variant="outline"
            _hover={{
              bg: useColorModeValue('blue.50', 'blue.900'),
              transform: 'translateY(-1px)',
            }}
            transition="all 0.2s"
          >
            {t('teif.actions.uploadPdf')}
          </Button>
          
          <Button
            leftIcon={<FiFileText size="16px" />}
            onClick={handleGenerateTeif}
            isLoading={isGenerating}
            loadingText={t('teif.generating')}
            colorScheme="blue"
            size="md"
            _hover={{
              transform: 'translateY(-1px)',
              boxShadow: 'md',
            }}
            transition="all 0.2s"
          >
            {t('teif.actions.generateTeif')}
          </Button>
          
          {(teifStatus === 'generated' || teifStatus === 'signed') && (
            <>
              <Button
                leftIcon={<FiFileText size="16px" />}
                onClick={handlePreviewTeif}
                variant="outline"
                size="md"
                colorScheme="teal"
                _hover={{
                  bg: useColorModeValue('teal.50', 'teal.900'),
                  transform: 'translateY(-1px)',
                }}
                transition="all 0.2s"
              >
                {t('teif.actions.preview')}
              </Button>
              <Button
                leftIcon={<FiDownload size="16px" />}
                onClick={handleDownloadTeif}
                colorScheme="teal"
                variant="solid"
                size="md"
                _hover={{
                  transform: 'translateY(-1px)',
                  boxShadow: 'md',
                }}
                transition="all 0.2s"
              >
                {t('teif.actions.download')}
              </Button>
            </>
          )}
        </HStack>
      </VStack>

      {/* Modals */}
      <TeifUploadModal 
        isOpen={isUploadModalOpen} 
        onClose={onCloseUploadModal} 
        onSuccess={handleUploadSuccess} 
      />
      
      <TeifPreviewModal
        isOpen={isPreviewOpen}
        onClose={() => {
          clearPreview();
          onClosePreview();
        }}
        previewUrl={previewUrl}
        invoiceNumber={invoiceNumber}
        onDownload={handleDownloadTeif}
      />
    </Box>
  );
};
