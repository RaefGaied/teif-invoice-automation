import { useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
    Box,
    Button,
    VStack,
    Text,
    Icon,
    useDisclosure,
    useToast,
    Progress,
    HStack,
    Alert,
    AlertIcon,
    AlertTitle,
    AlertDescription,
} from '@chakra-ui/react';
import { FiUpload, FiFile, FiX } from 'react-icons/fi';
import { useDropzone } from 'react-dropzone';
import { useTeif } from '../../hooks/useTeif';

export const TeifUploader = ({ onSuccess }: { onSuccess?: () => void }) => {
    const { t } = useTranslation();
    const toast = useToast();
    const [isUploading, setIsUploading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [file, setFile] = useState<File | null>(null);
    const { uploadPdfInvoice } = useTeif();
    const inputRef = useRef<HTMLInputElement>(null);

    const onDrop = (acceptedFiles: File[]) => {
        if (acceptedFiles.length > 0) {
            const pdfFile = acceptedFiles[0];
            if (pdfFile.type === 'application/pdf') {
                setFile(pdfFile);
            } else {
                toast({
                    title: t('teif.upload.invalidFileType'),
                    status: 'error',
                    duration: 3000,
                    isClosable: true,
                });
            }
        }
    };

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'application/pdf': ['.pdf'],
        },
        maxFiles: 1,
        multiple: false,
    });

    const handleUpload = async () => {
        if (!file) return;

        try {
            setIsUploading(true);
            setUploadProgress(30);

            // Simulate progress (in a real app, you'd use axios's onUploadProgress)
            const progressInterval = setInterval(() => {
                setUploadProgress((prev) => {
                    if (prev >= 90) {
                        clearInterval(progressInterval);
                        return prev;
                    }
                    return prev + 10;
                });
            }, 300);

            await uploadPdfInvoice.mutateAsync(file);

            clearInterval(progressInterval);
            setUploadProgress(100);

            toast({
                title: t('teif.upload.success'),
                status: 'success',
                duration: 3000,
                isClosable: true,
            });

            // Reset form
            setFile(null);
            setUploadProgress(0);

            // Call success callback if provided
            if (onSuccess) {
                onSuccess();
            }
        } catch (error) {
            console.error('Upload failed:', error);
            toast({
                title: t('teif.upload.error'),
                description: error instanceof Error ? error.message : t('common.unknownError'),
                status: 'error',
                duration: 5000,
                isClosable: true,
            });
        } finally {
            setIsUploading(false);
        }
    };

    const removeFile = () => {
        setFile(null);
        setUploadProgress(0);
        if (inputRef.current) {
            inputRef.current.value = '';
        }
    };

    return (
        <VStack spacing={4} w="100%">
            {!file ? (
                <Box
                    {...getRootProps()}
                    borderWidth={2}
                    borderStyle="dashed"
                    borderColor={isDragActive ? 'blue.400' : 'gray.300'}
                    borderRadius="lg"
                    p={8}
                    textAlign="center"
                    w="100%"
                    cursor="pointer"
                    _hover={{ borderColor: 'blue.400', bg: 'blue.50', _dark: { bg: 'blue.900' } }}
                    transition="all 0.2s"
                >
                    <input {...getInputProps()} ref={inputRef} />
                    <Icon as={FiUpload} w={8} h={8} mb={3} color="gray.400" />
                    <Text fontSize="lg" fontWeight="medium" mb={1}>
                        {isDragActive ? t('teif.upload.dropHere') : t('teif.upload.title')}
                    </Text>
                    <Text color="gray.500" fontSize="sm">
                        {t('teif.upload.subtitle')}
                    </Text>
                    <Text mt={2} fontSize="xs" color="gray.400">
                        {t('teif.upload.formats')}
                    </Text>
                </Box>
            ) : (
                <Box w="100%">
                    <Alert status="info" borderRadius="lg" mb={4}>
                        <AlertIcon />
                        <Box flex="1">
                            <AlertTitle>{t('teif.upload.fileSelected')}</AlertTitle>
                            <AlertDescription display="block">
                                {file.name} ({(file.size / 1024).toFixed(2)} KB)
                            </AlertDescription>
                        </Box>
                        <Button
                            size="sm"
                            variant="ghost"
                            onClick={removeFile}
                            rightIcon={<FiX />}
                        >
                            {t('common.remove')}
                        </Button>
                    </Alert>

                    {uploadProgress > 0 && uploadProgress < 100 && (
                        <Box mb={4}>
                            <Text mb={1} fontSize="sm" color="gray.600">
                                {t('common.uploading')}... {uploadProgress}%
                            </Text>
                            <Progress
                                value={uploadProgress}
                                size="sm"
                                colorScheme="blue"
                                borderRadius="full"
                                isAnimated
                                hasStripe
                            />
                        </Box>
                    )}

                    <HStack spacing={3} justifyContent="flex-end">
                        <Button
                            variant="outline"
                            onClick={removeFile}
                            isDisabled={isUploading}
                        >
                            {t('common.cancel')}
                        </Button>
                        <Button
                            colorScheme="blue"
                            onClick={handleUpload}
                            isLoading={isUploading}
                            loadingText={t('common.uploading')}
                            leftIcon={<FiUpload />}
                        >
                            {t('teif.upload.generateTeif')}
                        </Button>
                    </HStack>
                </Box>
            )}
        </VStack>
    );
};
