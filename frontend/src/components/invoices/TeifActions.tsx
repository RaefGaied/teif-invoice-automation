import { Button, Menu, MenuButton, MenuList, MenuItem, IconButton, useDisclosure, useToast } from '@chakra-ui/react';
import { DownloadIcon, ChevronDownIcon, ViewIcon } from '@chakra-ui/icons';
import { useTeif } from '../../hooks/useTeif';
import { useTranslation } from 'react-i18next';
import { useState } from 'react';
import { TeifPreviewModal } from './TeifPreviewModal';

interface TeifActionsProps {
    invoiceId: number;
    invoiceNumber?: string;
    size?: 'sm' | 'md' | 'lg';
    variant?: 'solid' | 'outline' | 'ghost' | 'link';
    showLabels?: boolean;
}

export const TeifActions = ({
    invoiceId,
    invoiceNumber,
    size = 'md',
    variant = 'outline',
    showLabels = true,
}: TeifActionsProps) => {
    const { t } = useTranslation();
    const toast = useToast();
    const { isOpen, onOpen, onClose } = useDisclosure();
    const [isPreviewLoading, setIsPreviewLoading] = useState(false);

    const {
        generateTeif,
        downloadTeif,
        previewTeif,
        clearPreview,
        isGenerating,
        previewUrl,
    } = useTeif(invoiceId);

    const handlePreview = async () => {
        try {
            setIsPreviewLoading(true);
            await previewTeif();
            onOpen();
        } catch (error) {
            console.error('Failed to load TEIF preview:', error);
        } finally {
            setIsPreviewLoading(false);
        }
    };

    const handleClosePreview = () => {
        clearPreview();
        onClose();
    };

    const handleDownload = async () => {
        const fileName = invoiceNumber ? `facture_${invoiceNumber}.xml` : undefined;
        await downloadTeif(fileName);
    };

    return (
        <>
            <Menu>
                <MenuButton
                    as={Button}
                    size={size}
                    variant={variant}
                    colorScheme="blue"
                    isLoading={isGenerating}
                    loadingText={t('teif.generating')}
                    rightIcon={<ChevronDownIcon />}
                >
                    {showLabels ? t('teif.actions.generate') : ''}
                </MenuButton>
                <MenuList>
                    <MenuItem
                        icon={<ViewIcon />}
                        onClick={handlePreview}
                        isDisabled={isPreviewLoading}
                    >
                        {t('teif.actions.preview')}
                    </MenuItem>
                    <MenuItem
                        icon={<DownloadIcon />}
                        onClick={handleDownload}
                        isDisabled={isGenerating}
                    >
                        {t('teif.actions.download')}
                    </MenuItem>
                </MenuList>
            </Menu>

            <TeifPreviewModal
                isOpen={isOpen}
                onClose={handleClosePreview}
                previewUrl={previewUrl}
                invoiceNumber={invoiceNumber}
                onDownload={handleDownload}
            />
        </>
    );
};

teafService.ts
