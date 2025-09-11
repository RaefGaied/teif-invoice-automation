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
} from '@chakra-ui/react';
import { DownloadIcon, CopyIcon, CheckIcon } from '@chakra-ui/icons';
import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

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
    const { hasCopied, onCopy } = useClipboard(xmlContent);

    const bgColor = useColorModeValue('gray.50', 'gray.800');
    const borderColor = useColorModeValue('gray.200', 'gray.700');

    useEffect(() => {
        if (isOpen && previewUrl) {
            const fetchXmlContent = async () => {
                try {
                    setIsLoading(true);
                    const response = await fetch(previewUrl);
                    const text = await response.text();
                    setXmlContent(text);
                } catch (error) {
                    console.error('Error loading XML content:', error);
                    setXmlContent(t('teif.preview.errorLoading'));
                } finally {
                    setIsLoading(false);
                }
            };

            fetchXmlContent();
        }
    }, [isOpen, previewUrl, t]);

    const formatXml = (xml: string) => {
        try {
            // Simple XML formatting - for better formatting consider using a proper XML formatter
            const formatted = xml
                .replace(/></g, '>\n<')
                .replace(/\s*<\/([^>]+)>/g, (match, p1) => `</${p1}>\n`)
                .replace(/(<[^/][^>]*>)(?!\s*<)/g, '$1\n');

            return formatted;
        } catch (error) {
            console.error('Error formatting XML:', error);
            return xml;
        }
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose} size="6xl" scrollBehavior="inside">
            <ModalOverlay />
            <ModalContent maxH="90vh">
                <ModalHeader>
                    {t('teif.preview.title')} {invoiceNumber && `- ${invoiceNumber}`}
                </ModalHeader>
                <ModalCloseButton />
                <ModalBody p={0} display="flex" flexDirection="column">
                    <Box
                        p={4}
                        bg={bgColor}
                        borderBottomWidth="1px"
                        borderColor={borderColor}
                        display="flex"
                        justifyContent="space-between"
                        alignItems="center"
                    >
                        <Text fontSize="sm" color="gray.500">
                            {t('teif.preview.subtitle')}
                        </Text>
                        <Box>
                            <Tooltip label={t('common.copyToClipboard')} placement="top">
                                <IconButton
                                    aria-label={t('common.copy')}
                                    icon={hasCopied ? <CheckIcon /> : <CopyIcon />}
                                    onClick={onCopy}
                                    size="sm"
                                    mr={2}
                                    variant="ghost"
                                />
                            </Tooltip>
                            <Button
                                leftIcon={<DownloadIcon />}
                                size="sm"
                                colorScheme="blue"
                                onClick={onDownload}
                            >
                                {t('teif.actions.download')}
                            </Button>
                        </Box>
                    </Box>
                    <Box flex="1" overflow="auto" p={4} bg="white" _dark={{ bg: 'gray.900' }}>
                        {isLoading ? (
                            <Text>{t('common.loading')}...</Text>
                        ) : (
                            <Code
                                as="pre"
                                p={4}
                                width="100%"
                                height="100%"
                                whiteSpace="pre-wrap"
                                overflowX="auto"
                                fontFamily="mono"
                                fontSize="sm"
                                borderRadius="md"
                                bg={bgColor}
                            >
                                {formatXml(xmlContent)}
                            </Code>
                        )}
                    </Box>
                </ModalBody>
                <ModalFooter borderTopWidth="1px" borderColor={borderColor}>
                    <Button variant="ghost" mr={3} onClick={onClose}>
                        {t('common.close')}
                    </Button>
                </ModalFooter>
            </ModalContent>
        </Modal>
    );
};
