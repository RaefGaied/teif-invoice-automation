import { Badge, Tooltip, Text, useColorModeValue } from '@chakra-ui/react';
import { useTranslation } from 'react-i18next';

type TeifStatus = 'pending' | 'generating' | 'generated' | 'signed' | 'error';

interface TeifStatusBadgeProps {
    status: TeifStatus;
    lastUpdated?: Date | string;
    showTooltip?: boolean;
}

export const TeifStatusBadge = ({
    status,
    lastUpdated,
    showTooltip = true,
}: TeifStatusBadgeProps) => {
    const { t } = useTranslation();

    const statusConfig = {
        pending: {
            color: 'gray',
            label: t('teif.status.pending'),
            tooltip: t('teif.statusTooltips.pending'),
        },
        generating: {
            color: 'blue',
            label: t('teif.status.generating'),
            tooltip: t('teif.statusTooltips.generating'),
        },
        generated: {
            color: 'green',
            label: t('teif.status.generated'),
            tooltip: t('teif.statusTooltips.generated'),
        },
        signed: {
            color: 'purple',
            label: t('teif.status.signed'),
            tooltip: t('teif.statusTooltips.signed'),
        },
        error: {
            color: 'red',
            label: t('teif.status.error'),
            tooltip: t('teif.statusTooltips.error'),
        },
    };

    const config = statusConfig[status] || statusConfig.pending;
    const updatedText = lastUpdated
        ? t('teif.lastUpdated', { date: new Date(lastUpdated).toLocaleString() })
        : '';

    const badge = (
        <Badge
            colorScheme={config.color}
            px={2}
            py={1}
            borderRadius="md"
            textTransform="none"
            fontWeight="medium"
            display="inline-flex"
            alignItems="center"
        >
            <Box
                as="span"
                w={2}
                h={2}
                borderRadius="full"
                bg={`${config.color}.500`}
                mr={2}
                flexShrink={0}
            />
            <Text as="span" fontSize="sm">
                {config.label}
            </Text>
        </Badge>
    );

    if (!showTooltip) {
        return badge;
    }

    return (
        <Tooltip
            label={
                <Box>
                    <Text>{config.tooltip}</Text>
                    {updatedText && <Text fontSize="xs" mt={1}>{updatedText}</Text>}
                </Box>
            }
            placement="top"
            hasArrow
            bg={useColorModeValue('gray.800', 'gray.200')}
            color={useColorModeValue('white', 'gray.800')}
            p={2}
            borderRadius="md"
        >
            {badge}
        </Tooltip>
    );
};
