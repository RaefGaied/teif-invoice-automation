import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
    Button,
    VStack,
    Text,
    useToast,
    Table,
    Thead,
    Tbody,
    Tr,
    Th,
    Td,
    Checkbox,
    HStack,
    Icon,
    Box,
} from '@chakra-ui/react';
import { FiDatabase, FiFileText, FiDownload } from 'react-icons/fi';
import { useQuery, useMutation } from '@tanstack/react-query';
import { teifService } from '../../services/teifService';
import { invoiceApi } from '../../services/invoiceApi';
import type { Invoice, InvoiceStatus } from '../../types/invoice';

interface InvoiceWithStatus extends Invoice {
    status: InvoiceStatus;
    clientName?: string;
    customerName?: string;
    invoice_date?: string;
    total_with_tax?: number;
}

export const TeifDbUploader = ({ onSuccess }: { onSuccess?: () => void }) => {
    const { t } = useTranslation();
    const toast = useToast();
    const [selectedInvoices, setSelectedInvoices] = useState<number[]>([]);
    const [isGenerating, setIsGenerating] = useState(false);

    // Fetch invoices from the database
    const { data: invoices = [], isLoading, error: fetchError } = useQuery<InvoiceWithStatus[]>({
        queryKey: ['invoices'],
        queryFn: async () => {
            try {
                console.log('Fetching invoices...');
                const response = await invoiceApi.getInvoices({ limit: 50 });
                console.log('Invoices API response:', response);
                return response.data || [];
            } catch (error) {
                console.error('Error fetching invoices:', error);
                throw error;
            }
        },
    });

    // Log any fetch errors
    useEffect(() => {
        if (fetchError) {
            console.error('Error in useQuery:', fetchError);
            toast({
                title: 'Erreur',
                description: 'Impossible de charger les factures. Veuillez réessayer.',
                status: 'error',
                duration: 5000,
                isClosable: true,
            });
        }
    }, [fetchError]);

    // Log when invoices are loaded
    useEffect(() => {
        if (invoices.length > 0) {
            console.log('Invoices loaded:', invoices);
        }
    }, [invoices]);

    // Mutation for generating TEIF XML
    const generateTeifMutation = useMutation({
        mutationFn: async (invoiceId: number) => {
            return teifService.generateTeif(invoiceId);
        },
        onSuccess: (data, invoiceId) => {
            // Create and download the XML file
            const blob = new Blob([data], { type: 'application/xml' });
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `invoice_${invoiceId}_${new Date().toISOString().split('T')[0]}.xml`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);

            toast({
                title: t('teif.generate.success'),
                status: 'success',
                duration: 3000,
                isClosable: true,
            });

            if (onSuccess) {
                onSuccess();
            }
        },
        onError: (error: Error) => {
            console.error('Error generating TEIF:', error);
            toast({
                title: t('teif.generate.error'),
                description: error.message,
                status: 'error',
                duration: 5000,
                isClosable: true,
            });
        },
        onSettled: () => {
            setIsGenerating(false);
        },
    });

    const handleSelectInvoice = (invoiceId: number) => {
        setSelectedInvoices(prev =>
            prev.includes(invoiceId)
                ? prev.filter(id => id !== invoiceId)
                : [...prev, invoiceId]
        );
    };

    const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.checked) {
            setSelectedInvoices(invoices.map(invoice => invoice.id));
        } else {
            setSelectedInvoices([]);
        }
    };

    const handleGenerateSelected = async () => {
        if (selectedInvoices.length === 0) {
            toast({
                title: t('teif.selectInvoices'),
                status: 'warning',
                duration: 3000,
                isClosable: true,
            });
            return;
        }

        setIsGenerating(true);

        try {
            // Process invoices sequentially to avoid overwhelming the server
            for (const invoiceId of selectedInvoices) {
                try {
                    const xml = await teifService.generateTeif(invoiceId);

                    // Create and download the XML file
                    const blob = new Blob([xml], { type: 'application/xml' });
                    const url = window.URL.createObjectURL(blob);
                    const link = document.createElement('a');
                    link.href = url;
                    link.setAttribute('download', `facture_${invoiceId}_${new Date().toISOString().split('T')[0]}.xml`);
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    window.URL.revokeObjectURL(url);

                    // Small delay between downloads
                    await new Promise(resolve => setTimeout(resolve, 100));
                } catch (error) {
                    console.error(`Error downloading invoice ${invoiceId}:`, error);
                    toast({
                        title: `Error downloading invoice ${invoiceId}`,
                        status: 'error',
                        duration: 3000,
                        isClosable: true,
                    });
                }
            }

            toast({
                title: t('teif.download.complete'),
                status: 'success',
                duration: 3000,
                isClosable: true,
            });

        } catch (error) {
            console.error('Error processing invoices:', error);
            toast({
                title: t('teif.download.error'),
                status: 'error',
                duration: 5000,
                isClosable: true,
            });
        } finally {
            setIsGenerating(false);
        }
    };

    if (isLoading) {
        return (
            <VStack spacing={4} align="center" justify="center" minH="200px">
                <Text>Chargement des factures en cours...</Text>
            </VStack>
        );
    }

    if (fetchError) {
        return (
            <VStack spacing={4} align="center" justify="center" minH="200px">
                <Text color="red.500">Erreur lors du chargement des factures</Text>
                <Button
                    colorScheme="blue"
                    onClick={() => window.location.reload()}
                >
                    Réessayer
                </Button>
            </VStack>
        );
    }

    return (
        <VStack spacing={4} align="stretch">
            <Text fontSize="lg" fontWeight="bold">
                <Icon as={FiDatabase} mr={2} />
                {t('teif.selectFromDatabase')}
            </Text>

            {invoices.length === 0 ? (
                <Box textAlign="center" py={6}>
                    <Text>{t('teif.noInvoices')}</Text>
                </Box>
            ) : (
                <>
                    <Box overflowX="auto">
                        <Table variant="simple" size="sm">
                            <Thead>
                                <Tr>
                                    <Th><Checkbox onChange={handleSelectAll} isChecked={selectedInvoices.length === invoices.length} /></Th>
                                    <Th>{t('invoice.invoiceNumber')}</Th>
                                    <Th>{t('invoice.customer')}</Th>
                                    <Th>{t('invoice.date')}</Th>
                                    <Th>{t('invoice.amount')}</Th>
                                    <Th>{t('invoice.status')}</Th>
                                    <Th>{t('common.actions')}</Th>
                                </Tr>
                            </Thead>
                            <Tbody>
                                {invoices.map((invoice) => (
                                    <Tr key={invoice.id}>
                                        <Td>
                                            <Checkbox
                                                isChecked={selectedInvoices.includes(invoice.id)}
                                                onChange={() => handleSelectInvoice(invoice.id)}
                                            />
                                        </Td>
                                        <Td>{invoice.invoiceNumber || `INV-${invoice.id}`}</Td>
                                        <Td>{invoice.clientName || invoice.customerName || 'N/A'}</Td>
                                        <Td>{invoice.invoice_date ? new Date(invoice.invoice_date).toLocaleDateString() : new Date(invoice.issueDate).toLocaleDateString()}</Td>
                                        <Td>{(invoice.total_with_tax || invoice.totalAmount || 0).toFixed(3)} TND</Td>
                                        <Td>
                                            <Box
                                                as="span"
                                                px={2}
                                                py={1}
                                                borderRadius="md"
                                                bg={`${statusColors[invoice.status.toLowerCase() as keyof typeof statusColors] || 'gray'}.100`}
                                                color={`${statusColors[invoice.status.toLowerCase() as keyof typeof statusColors] || 'gray'}.800`}
                                                fontSize="xs"
                                                fontWeight="medium"
                                                textTransform="capitalize"
                                            >
                                                {invoice.status}
                                            </Box>
                                        </Td>
                                        <Td>
                                            <Button
                                                size="sm"
                                                leftIcon={<FiDownload />}
                                                variant="ghost"
                                                onClick={() => {
                                                    setIsGenerating(true);
                                                    generateTeifMutation.mutate(invoice.id);
                                                }}
                                                isLoading={isGenerating && generateTeifMutation.variables === invoice.id}
                                            >
                                                {t('common.download')}
                                            </Button>
                                        </Td>
                                    </Tr>
                                ))}
                            </Tbody>
                        </Table>
                    </Box>

                    <HStack justifyContent="flex-end" mt={4}>
                        <Button
                            colorScheme="blue"
                            leftIcon={<FiFileText />}
                            onClick={handleGenerateSelected}
                            isLoading={isGenerating}
                            isDisabled={selectedInvoices.length === 0}
                        >
                            {t('teif.generateSelected', { count: selectedInvoices.length })}
                        </Button>
                    </HStack>
                </>
            )}
        </VStack>
    );
};

// Status colors mapping
const statusColors: Record<string, string> = {
    draft: 'gray',
    processing: 'blue',
    generated: 'green',
    error: 'red',
    paid: 'green',
    unpaid: 'orange',
    cancelled: 'red',
    refunded: 'purple',
    archived: 'gray',
    sent: 'blue',
    overdue: 'red',
} as const;
