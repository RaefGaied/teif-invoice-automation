import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
    Modal,
    ModalOverlay,
    ModalContent,
    ModalHeader,
    ModalCloseButton,
    ModalBody,
    Tabs,
    TabList,
    TabPanels,
    Tab,
    TabPanel,
} from '@chakra-ui/react';
import { FiUpload, FiDatabase } from 'react-icons/fi';
import { TeifUploader } from './TeifUploader';
import { TeifDbUploader } from './TeifDbUploader';

interface TeifUploadModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess?: () => void;
}

export const TeifUploadModal = ({ isOpen, onClose, onSuccess }: TeifUploadModalProps) => {
    const { t } = useTranslation();
    const [tabIndex, setTabIndex] = useState(0);

    const handleSuccess = () => {
        if (onSuccess) {
            onSuccess();
        }
        onClose();
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose} size="4xl" isCentered>
            <ModalOverlay />
            <ModalContent>
                <ModalHeader>{t('teif.upload.modalTitle')}</ModalHeader>
                <ModalCloseButton />
                <ModalBody pb={6}>
                    <Tabs
                        index={tabIndex}
                        onChange={setTabIndex}
                        variant="enclosed"
                        colorScheme="blue"
                    >
                        <TabList mb={4}>
                            <Tab>
                                <FiUpload style={{ marginRight: '8px' }} />
                                {t('teif.upload.fileUpload')}
                            </Tab>
                            <Tab>
                                <FiDatabase style={{ marginRight: '8px' }} />
                                {t('teif.upload.fromDatabase')}
                            </Tab>
                        </TabList>

                        <TabPanels>
                            <TabPanel px={0}>
                                <TeifUploader onSuccess={handleSuccess} />
                            </TabPanel>
                            <TabPanel px={0}>
                                <TeifDbUploader onSuccess={handleSuccess} />
                            </TabPanel>
                        </TabPanels>
                    </Tabs>
                </ModalBody>
            </ModalContent>
        </Modal>
    );
};
