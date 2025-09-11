import { Modal, ModalOverlay, ModalContent, ModalHeader, ModalBody, ModalCloseButton, useDisclosure } from '@chakra-ui/react';
import { useTranslation } from 'react-i18next';
import { TeifUploader } from './TeifUploader';

interface TeifUploadModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess?: () => void;
}

export const TeifUploadModal = ({ isOpen, onClose, onSuccess }: TeifUploadModalProps) => {
    const { t } = useTranslation();

    const handleSuccess = () => {
        onClose();
        if (onSuccess) {
            onSuccess();
        }
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose} size="xl" isCentered>
            <ModalOverlay />
            <ModalContent>
                <ModalHeader>{t('teif.upload.modalTitle')}</ModalHeader>
                <ModalCloseButton />
                <ModalBody pb={6}>
                    <TeifUploader onSuccess={handleSuccess} />
                </ModalBody>
            </ModalContent>
        </Modal>
    );
};
