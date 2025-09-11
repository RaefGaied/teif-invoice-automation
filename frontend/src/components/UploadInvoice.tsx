import React, { useState } from 'react';
import { Button, Box, useToast, VStack, Text } from '@chakra-ui/react';
import { invoiceApi } from '../services/api';

const UploadInvoice: React.FC = () => {
    const [isUploading, setIsUploading] = useState(false);
    const toast = useToast();

    const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        try {
            setIsUploading(true);
            await invoiceApi.createInvoice(formData);
            toast({
                title: 'Success',
                description: 'Invoice uploaded successfully',
                status: 'success',
                duration: 3000,
                isClosable: true,
            });
            // Refresh the invoice list after successful upload
            window.location.reload();
        } catch (error) {
            console.error('Upload failed:', error);
            toast({
                title: 'Error',
                description: 'Failed to upload invoice',
                status: 'error',
                duration: 3000,
                isClosable: true,
            });
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <Box p={5} borderWidth={1} borderRadius="md" mb={5}>
            <VStack spacing={4}>
                <Text fontSize="lg" fontWeight="bold">Upload New Invoice</Text>
                <input
                    type="file"
                    id="file-upload"
                    accept=".pdf"
                    onChange={handleFileChange}
                    style={{ display: 'none' }}
                />
                <Button
                    as="label"
                    htmlFor="file-upload"
                    colorScheme="blue"
                    isLoading={isUploading}
                    loadingText="Uploading..."
                    cursor="pointer"
                >
                    Select PDF File
                </Button>
                <Text fontSize="sm" color="gray.500">
                    Only PDF files are accepted
                </Text>
            </VStack>
        </Box>
    );
};

export default UploadInvoice;
