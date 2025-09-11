import { useDisclosure } from '@chakra-ui/react';
import { useCallback } from 'react';

export const useTeifUploadModal = (onSuccess?: () => void) => {
    const { isOpen, onOpen, onClose } = useDisclosure();

    const handleSuccess = useCallback(() => {
        onClose();
        if (onSuccess) {
            onSuccess();
        }
    }, [onClose, onSuccess]);

    return {
        isOpen,
        onOpen,
        onClose: handleSuccess, // Close with success handling
        modalProps: {
            isOpen,
            onClose: handleSuccess,
            onSuccess: handleSuccess,
        },
    };
};
