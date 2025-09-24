import React, { useState } from 'react';
import {
  Box,
  Button,
  VStack,
  Text,
  useToast,
  Heading,
  useDisclosure,
} from '@chakra-ui/react';
import { FiUpload } from 'react-icons/fi';
import { invoiceApi } from '../services/api';
import { TeifUploadModal } from './invoices/TeifUploadModal';

const UploadInvoice: React.FC = () => {
  const [isUploading, setIsUploading] = useState(false);
  const toast = useToast();
  const { isOpen, onOpen, onClose } = useDisclosure();

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
      // 🔄 Ici tu peux invalider le cache react-query plutôt que window.reload()
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

  const handleUploadSuccess = () => {
    toast({
      title: 'Success',
      description: 'Invoice processed successfully',
      status: 'success',
      duration: 3000,
      isClosable: true,
    });
    // Tu peux rafraîchir les données ici
  };

  return (
    <Box p={6}>
      <VStack spacing={6} align="stretch">
        <Heading size="lg">Upload New Invoice</Heading>

        {/* Upload simple PDF */}
        <Box p={5} borderWidth={1} borderRadius="md" bg="white" boxShadow="sm">
          <VStack spacing={4}>
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
              leftIcon={<FiUpload />}
              cursor="pointer"
            >
              Select PDF File
            </Button>
            <Text fontSize="sm" color="gray.500">
              Only PDF files are accepted
            </Text>
          </VStack>
        </Box>

        {/* OU utiliser ton modal Teif */}
        <Button colorScheme="teal" onClick={onOpen} leftIcon={<FiUpload />}>
          Advanced Upload (TEIF)
        </Button>

        <TeifUploadModal
          isOpen={isOpen}
          onClose={onClose}
          onSuccess={handleUploadSuccess}
        />
      </VStack>
    </Box>
  );
};

export default UploadInvoice;
