import {
    Modal,
    ModalOverlay,
    ModalContent,
    ModalHeader,
    ModalCloseButton,
    ModalBody,
    ModalFooter,
    Button,
    Box,
    Text,
    useClipboard,
    useColorModeValue,
    Code,
    Tooltip,
    IconButton,
    VStack,
    HStack,
    Spinner,
    Alert,
    AlertIcon,
    useBreakpointValue,
} from '@chakra-ui/react';
import { FiDownload, FiCopy, FiCheck, FiX } from 'react-icons/fi';
import { useTranslation } from 'react-i18next';
import { useEffect, useState } from 'react';
import { format } from 'date-fns';

interface TeifPreviewModalProps {
    isOpen: boolean;
    onClose: () => void;
    previewUrl: string | null;
    invoiceNumber?: string;
    onDownload: () => void;
}

export const TeifPreviewModal = ({
    isOpen,
    onClose,
    previewUrl,
    invoiceNumber,
    onDownload,
}: TeifPreviewModalProps) => {
    const { t } = useTranslation();
    const [xmlContent, setXmlContent] = useState<string>('');
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const { hasCopied, onCopy } = useClipboard(xmlContent);

    // Color mode values
    const modalBg = useColorModeValue('white', 'gray.800');
    const codeBg = useColorModeValue('gray.50', 'gray.700');
    const borderColor = useColorModeValue('gray.200', 'gray.600');
    const textMuted = useColorModeValue('gray.600', 'gray.400');
    const headerBg = useColorModeValue('gray.50', 'gray.900');
    const footerBg = useColorModeValue('gray.50', 'gray.700');

    // Responsive sizing
    const modalSize = useBreakpointValue({ base: 'full', md: '4xl', lg: '6xl' });
    const codeFontSize = useBreakpointValue({ base: 'xs', md: 'sm' });

    useEffect(() => {
        if (isOpen && previewUrl) {
            const fetchXmlContent = async () => {
                try {
                    setIsLoading(true);
                    setError(null);
                    const response = await fetch(previewUrl);
                    if (!response.ok) {
                        throw new Error(t('teif.preview.fetchError'));
                    }
                    const text = await response.text();
                    setXmlContent(formatXml(text));
                } catch (err) {
                    console.error('Error loading XML content:', err);
                    setError(err instanceof Error ? err.message : t('common.unknownError'));
                } finally {
                    setIsLoading(false);
                }
            };

            fetchXmlContent();
        } else {
            // Reset state when modal is closed
            setXmlContent('');
            setError(null);
            setIsLoading(true);
        }
    }, [isOpen, previewUrl, t]);

    // Simple XML formatter
    const formatXml = (xml: string): string => {
        try {
            // This is a simple formatter - for production, consider using a proper XML formatter
            const formatted = xml
                .replace(/></g, '>\n<')
                .replace(/\s*<\/([^>]+)>/g, (match, p1) => `</${p1}>\n`)
                .replace(/(<[^/][^>]*>)(?!\s*<)/g, '$1\n')
                .replace(/\n\n/g, '\n')
                .trim();

            return formatted;
        } catch (err) {
            console.error('Error formatting XML:', err);
            return xml; // Return original if formatting fails
        }
    };

    const handleDownloadClick = () => {
        onDownload();
        // Small delay to allow download to start before potentially closing the modal
        setTimeout(() => {
            onClose();
        }, 300);
    };

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            size={modalSize}
            isCentered
            scrollBehavior="inside"
            closeOnOverlayClick={!isLoading}
        >
            <ModalOverlay backdropFilter="blur(4px)" />
            <ModalContent
                maxH="90vh"
                bg={modalBg}
                borderRadius="lg"
                overflow="hidden"
                boxShadow="xl"
            >
                <ModalHeader
                    px={6}
                    py={4}
                    borderBottomWidth="1px"
                    borderColor={borderColor}
                    bg={headerBg}
                    display="flex"
                    justifyContent="space-between"
                    alignItems="center"
                >
                    <VStack align="flex-start" spacing={0}>
                        <Text fontSize="lg" fontWeight="semibold">
                            {t('teif.preview.title')} {invoiceNumber && `- ${invoiceNumber}`}
                        </Text>
                        <Text fontSize="sm" color={textMuted}>
                            {t('teif.preview.subtitle')}
                        </Text>
                    </VStack>
                    <HStack spacing={2}>
                        <Tooltip
                            label={hasCopied ? t('common.copied') : t('common.copyToClipboard')}
                            placement="bottom"
                            hasArrow
                        >
                            <IconButton
                                aria-label={t('common.copyToClipboard')}
                                icon={hasCopied ? <FiCheck /> : <FiCopy />}
                                onClick={onCopy}
                                size="sm"
                                variant="ghost"
                                colorScheme="blue"
                                isDisabled={isLoading || !!error}
                                _hover={{ bg: useColorModeValue('blue.50', 'blue.900') }}
                            />
                        </Tooltip>
                        <ModalCloseButton
                            position="static"
                            size="sm"
                            color={textMuted}
                            _hover={{ color: 'red.500', bg: useColorModeValue('red.50', 'red.900') }}
                        />
                    </HStack>
                </ModalHeader>

                <ModalBody p={0} position="relative">
                    {isLoading ? (
                        <VStack justify="center" h="300px">
                            <Spinner size="xl" color="blue.500" thickness="3px" />
                            <Text mt={4} color={textMuted}>
                                {t('teif.preview.loading')}
                            </Text>
                        </VStack>
                    ) : error ? (
                        <Alert status="error" variant="left-accent" borderRadius="md" m={4}>
                            <AlertIcon />
                            <VStack align="flex-start" spacing={1}>
                                <Text fontWeight="medium">{t('common.error')}</Text>
                                <Text fontSize="sm">{error}</Text>
                            </VStack>
                        </Alert>
                    ) : (
                        <Box
                            as="pre"
                            p={4}
                            m={0}
                            overflowX="auto"
                            fontSize={codeFontSize}
                            fontFamily="mono"
                            whiteSpace="pre-wrap"
                            wordBreak="break-word"
                            bg={codeBg}
                            h="60vh"
                        >
                            <Code
                                as="span"
                                display="block"
                                color={useColorModeValue('gray.800', 'gray.200')}
                                bg="transparent"
                                p={0}
                                whiteSpace="pre"
                                overflowX="auto"
                                sx={{
                                    '& .tag': { color: useColorModeValue('blue.600', 'blue.300') },
                                    '& .attr': { color: useColorModeValue('purple.600', 'purple.300') },
                                    '& .value': { color: useColorModeValue('green.600', 'green.300') },
                                }}
                                dangerouslySetInnerHTML={{
                                    __html: highlightXmlSyntax(xmlContent),
                                }}
                            />
                        </Box>
                    )}
                </ModalBody>

                <ModalFooter
                    px={6}
                    py={3}
                    borderTopWidth="1px"
                    borderColor={borderColor}
                    bg={footerBg}
                    justifyContent="space-between"
                >
                    <Text fontSize="sm" color={textMuted}>
                        {t('teif.preview.generatedOn', { date: format(new Date(), 'PPpp') })}
                    </Text>
                    <HStack spacing={3}>
                        <Button
                            variant="outline"
                            onClick={onClose}
                            leftIcon={<FiX />}
                            isDisabled={isLoading}
                        >
                            {t('common.close')}
                        </Button>
                        <Button
                            colorScheme="blue"
                            onClick={handleDownloadClick}
                            leftIcon={<FiDownload />}
                            isDisabled={isLoading || !!error}
                            _hover={{
                                transform: 'translateY(-1px)',
                                boxShadow: 'md',
                            }}
                            transition="all 0.2s"
                        >
                            {t('teif.actions.downloadXml')}
                        </Button>
                    </HStack>
                </ModalFooter>
            </ModalContent>
        </Modal>
    );
};

// Simple XML syntax highlighter (basic implementation)
const highlightXmlSyntax = (xml: string): string => {
    return xml
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/&lt;([\w:-]+)/g, '<span class="tag">&lt;$1</span>')
        .replace(/([\w:-]+)=/g, '<span class="attr">$1</span>=')
        .replace(/=(["'])(.*?)\1/g, '=<span class="value">$1$2$1</span>');
};
