import React, { useState, useEffect, useCallback } from 'react';
import {
    Table,
    Thead,
    Tbody,
    Tr,
    Th,
    Td,
    Box,
    Text,
    Badge,
    Flex,
    Icon,
    Button,
    useDisclosure,
    useToast,
    Skeleton,
    Stack,
    useBreakpointValue,
    Link,
} from '@chakra-ui/react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { FiFileText, FiSearch, FiFilter, FiX, FiDownload, FiEye, FiEdit2, FiTrash2 } from 'react-icons/fi';
import { Link as RouterLink } from 'react-router-dom';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';

import { invoiceApi } from '../../services/api';
import { Invoice, InvoiceStatus } from '../../types/invoice';
import { InvoiceFilters } from './InvoiceFilters';
import { useAuth } from '../../contexts/AuthContext';

interface InvoiceListProps {
    limit?: number;
    showPagination?: boolean;
    showFilters?: boolean;
    clientId?: number;
    status?: InvoiceStatus;
}

const statusColors: Record<InvoiceStatus, string> = {
    draft: 'gray',
    sent: 'blue',
    paid: 'green',
    overdue: 'orange',
    cancelled: 'red',
    refunded: 'purple',
};

const InvoiceList: React.FC<InvoiceListProps> = ({
    limit = 10,
    showPagination = true,
    showFilters = true,
    clientId,
    status,
}) => {
    const [page, setPage] = useState(1);
    const [searchQuery, setSearchQuery] = useState('');
    const [filters, setFilters] = useState<{
        status?: string;
        clientId?: string;
        startDate?: Date | null;
        endDate?: Date | null;
        amountMin?: string;
        amountMax?: string;
    }>({});

    const toast = useToast();
    const { user } = useAuth();
    const queryClient = useQueryClient();
    const isMobile = useBreakpointValue({ base: true, md: false });

    // Mock clients data - replace with actual API call
    const clients = [
        { id: 1, name: 'Client A' },
        { id: 2, name: 'Client B' },
        { id: 3, name: 'Client C' },
    ];

    const statuses: InvoiceStatus[] = ['draft', 'sent', 'paid', 'overdue', 'cancelled', 'refunded'];

    const fetchInvoices = useCallback(async () => {
        const params: any = {
            page,
            limit,
            search: searchQuery,
            ...filters,
        };

        // Add clientId and status from props if provided
        if (clientId) params.clientId = clientId;
        if (status) params.status = status;

        const response = await invoiceApi.getInvoices(params);
        return response.data;
    }, [page, limit, searchQuery, filters, clientId, status]);

    const {
        data: invoicesData,
        isLoading,
        isError,
        error,
        refetch,
    } = useQuery({
        queryKey: ['invoices', { page, limit, searchQuery, filters, clientId, status }],
        queryFn: fetchInvoices,
        keepPreviousData: true,
    });

    const handleSearch = (query: string) => {
        setSearchQuery(query);
        setPage(1); // Reset to first page on new search
    };

    const handleFilterChange = (newFilters: any) => {
        setFilters(newFilters);
        setPage(1); // Reset to first page on new filters
    };

    const handleResetFilters = () => {
        setFilters({});
        setSearchQuery('');
        setPage(1);
    };

    const handleDelete = async (id: number) => {
        if (window.confirm('Êtes-vous sûr de vouloir supprimer cette facture ?')) {
            try {
                await invoiceApi.deleteInvoice(id);
                toast({
                    title: 'Facture supprimée',
                    status: 'success',
                    duration: 3000,
                    isClosable: true,
                });
                queryClient.invalidateQueries(['invoices']);
            } catch (error) {
                console.error('Error deleting invoice:', error);
                toast({
                    title: 'Erreur',
                    description: 'Une erreur est survenue lors de la suppression de la facture',
                    status: 'error',
                    duration: 5000,
                    isClosable: true,
                });
            }
        }
    };

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('fr-TN', {
            style: 'currency',
            currency: 'TND',
            minimumFractionDigits: 3,
        }).format(amount);
    };

    // Show skeleton loading state
    if (isLoading && !invoicesData) {
        return (
            <Stack spacing={4}>
                {[...Array(5)].map((_, i) => (
                    <Skeleton key={i} height="60px" />
                ))}
            </Stack>
        );
    }

    // Show error state
    if (isError) {
        return (
            <Box textAlign="center" py={10}>
                <Icon as={FiX} boxSize={10} color="red.500" mb={4} />
                <Text color="red.500" mb={4}>
                    Une erreur est survenue lors du chargement des factures.
                </Text>
                <Button colorScheme="blue" onClick={() => refetch()}>
                    Réessayer
                </Button>
            </Box>
        );
    }

    // Show empty state
    if (invoicesData?.data.length === 0) {
        return (
            <Box textAlign="center" py={10}>
                <Icon as={FiFileText} boxSize={10} color="gray.400" mb={4} />
                <Text color="gray.500" mb={4}>
                    Aucune facture trouvée.
                </Text>
                <Button as={RouterLink} to="/invoices/new" colorScheme="blue">
                    Créer une facture
                </Button>
            </Box>
        );
    }

    return (
        <Box>
            {showFilters && (
                <InvoiceFilters
                    onSearch={handleSearch}
                    onFilterChange={handleFilterChange}
                    onReset={handleResetFilters}
                    clients={clients}
                    statuses={statuses}
                    defaultFilters={filters}
                />
            )}

            <Box overflowX="auto">
                <Table variant="simple" size={isMobile ? 'sm' : 'md'}>
                    <Thead>
                        <Tr>
                            <Th>N° Facture</Th>
                            <Th>Client</Th>
                            <Th>Date</Th>
                            <Th>Échéance</Th>
                            <Th isNumeric>Montant</Th>
                            <Th>Statut</Th>
                            <Th></Th>
                        </Tr>
                    </Thead>
                    <Tbody>
                        {invoicesData?.data.map((invoice: Invoice) => (
                            <Tr key={invoice.id} _hover={{ bg: 'gray.50' }}>
                                <Td>
                                    <Link as={RouterLink} to={`/invoices/${invoice.id}`} color="blue.500" fontWeight="medium">
                                        #{invoice.invoiceNumber}
                                    </Link>
                                </Td>
                                <Td>
                                    <Text fontWeight="medium">{invoice.client?.name || 'N/A'}</Text>
                                    <Text fontSize="sm" color="gray.500">
                                        {invoice.client?.email || ''}
                                    </Text>
                                </Td>
                                <Td>
                                    {invoice.issueDate
                                        ? format(new Date(invoice.issueDate), 'dd MMM yyyy', { locale: fr })
                                        : 'N/A'}
                                </Td>
                                <Td>
                                    {invoice.dueDate
                                        ? format(new Date(invoice.dueDate), 'dd MMM yyyy', { locale: fr })
                                        : 'N/A'}
                                </Td>
                                <Td isNumeric fontWeight="bold">
                                    {formatCurrency(invoice.totalAmount)}
                                </Td>
                                <Td>
                                    <Badge
                                        colorScheme={statusColors[invoice.status]}
                                        px={2}
                                        py={1}
                                        borderRadius="md"
                                        textTransform="capitalize"
                                    >
                                        {invoice.status}
                                    </Badge>
                                </Td>
                                <Td>
                                    <Flex justifyContent="flex-end" gap={2}>
                                        <IconButton
                                            as={RouterLink}
                                            to={`/invoices/${invoice.id}`}
                                            aria-label="Voir la facture"
                                            icon={<FiEye />}
                                            size="sm"
                                            variant="ghost"
                                        />
                                        <IconButton
                                            as={RouterLink}
                                            to={`/invoices/${invoice.id}/edit`}
                                            aria-label="Modifier la facture"
                                            icon={<FiEdit2 />}
                                            size="sm"
                                            variant="ghost"
                                            colorScheme="blue"
                                        />
                                        <IconButton
                                            aria-label="Télécharger la facture"
                                            icon={<FiDownload />}
                                            size="sm"
                                            variant="ghost"
                                            colorScheme="green"
                                            onClick={() => {
                                                // Handle download
                                                toast({
                                                    title: 'Téléchargement',
                                                    description: 'Téléchargement de la facture...',
                                                    status: 'info',
                                                    duration: 2000,
                                                    isClosable: true,
                                                });
                                            }}
                                        />
                                        <IconButton
                                            aria-label="Supprimer la facture"
                                            icon={<FiTrash2 />}
                                            size="sm"
                                            variant="ghost"
                                            colorScheme="red"
                                            onClick={() => handleDelete(invoice.id)}
                                        />
                                    </Flex>
                                </Td>
                            </Tr>
                        ))}
                    </Tbody>
                </Table>
            </Box>

            {showPagination && invoicesData && invoicesData.total > limit && (
                <Flex justifyContent="space-between" alignItems="center" mt={6}>
                    <Text color="gray.600" fontSize="sm">
                        Affichage de {invoicesData.from} à {invoicesData.to} sur {invoicesData.total} factures
                    </Text>
                    <Flex gap={2}>
                        <Button
                            onClick={() => setPage((p) => Math.max(p - 1, 1))}
                            isDisabled={page === 1}
                            size="sm"
                            variant="outline"
                        >
                            Précédent
                        </Button>
                        <Button
                            onClick={() => setPage((p) => p + 1)}
                            isDisabled={!invoicesData.nextPage}
                            size="sm"
                            variant="outline"
                        >
                            Suivant
                        </Button>
                    </Flex>
                </Flex>
            )}
        </Box>
    );
};

export default InvoiceList;
