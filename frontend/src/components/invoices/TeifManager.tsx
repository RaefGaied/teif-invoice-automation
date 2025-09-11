import { Box, VStack, HStack, Text, Button, useDisclosure, useToast } from '@chakra-ui/react';
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
            });
            if (onTeifGenerated) {
                onTeifGenerated();
            }
        } catch (error) {
            console.error('Failed to generate TEIF:', error);
        }
    };

    const handleDownloadTeif = async () => {
        const fileName = invoiceNumber ? `facture_${invoiceNumber}.xml` : undefined;
        await downloadTeif(fileName);
    };

    const handlePreviewTeif = async () => {
        try {
            await previewTeif();
            onOpenPreview();
        } catch (error) {
            console.error('Failed to load TEIF preview:', error);
        }
    };

    const handleUploadSuccess = () => {
        onCloseUploadModal();
        if (onTeifGenerated) {
            onTeifGenerated();
        }
    };

    return (
        <Box w="100%">
            <VStack spacing={4} align="stretch">
                {/* Status Bar */}
                <Box
                    p={4}
                    borderWidth="1px"
                    borderRadius="md"
                    bg="white"
                    _dark={{ bg: 'gray.800' }}
                >
                    <HStack justifyContent="space-between" alignItems="center">
                        <HStack spacing={4}>
                            <TeifStatusBadge status={teifStatus} lastUpdated={lastUpdated} />
                            <Text fontSize="sm" color="gray.500">
                                {t('teif.lastUpdated')}: {lastUpdated ? new Date(lastUpdated).toLocaleString() : t('common.never')}
                            </Text>
                        </HStack>
                        <Button
                            size="sm"
                            variant="ghost"
                            leftIcon={<FiRefreshCw />}
                            onClick={onRefresh}
                            isLoading={isGenerating}
                        >
                            {t('common.refresh')}
                        </Button>
                    </HStack>
                </Box>

                {/* Action Buttons */}
                <HStack spacing={3} flexWrap="wrap">
                    <Button
                        leftIcon={<FiUpload />}
                        colorScheme="blue"
                        onClick={onOpenUploadModal}
                        isDisabled={isGenerating}
                    >
                        {t('teif.actions.uploadPdf')}
                    </Button>

                    <Button
                        leftIcon={<FiFileText />}
                        onClick={handleGenerateTeif}
                        isLoading={isGenerating}
                        loadingText={t('teif.generating')}
                        variant="outline"
                    >
                        {t('teif.actions.generateTeif')}
                    </Button>

                    {teifStatus === 'generated' || teifStatus === 'signed' ? (
                        <>
                            <Button
                                leftIcon={<FiFileText />}
                                onClick={handlePreviewTeif}
                                variant="outline"
                            >
                                {t('teif.actions.preview')}
                            </Button>
                            <Button
                                leftIcon={<FiDownload />}
                                onClick={handleDownloadTeif}
                                colorScheme="green"
                                variant="outline"
                            >
                                {t('teif.actions.download')}
                            </Button>
                        </>
                    ) : null}
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
                onClose={onClosePreview}
                previewUrl={previewUrl}
                invoiceNumber={invoiceNumber}
                onDownload={handleDownloadTeif}
            />
        </Box>
    );
};
