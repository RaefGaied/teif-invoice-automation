import React, { useState, useCallback } from 'react';
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
    IconButton,
    useToast,
    Skeleton,
    Stack,
    Link,
} from '@chakra-ui/react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { FiFileText, FiX, FiDownload, FiEye, FiEdit2, FiTrash2 } from 'react-icons/fi';
import { Link as RouterLink } from 'react-router-dom';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';

import { invoiceApi } from '../../services/invoiceApi';
import type { Invoice, InvoiceStatus, PaginatedResponse } from '../../types/invoice';
import InvoiceFilters from './InvoiceFilters';

interface InvoiceListProps {
    limit?: number;
    showPagination?: boolean;
    showFilters?: boolean;
    clientId?: number;
    status?: InvoiceStatus;
}

interface InvoiceFiltersState {
    status?: string;
    clientId?: string;
    startDate?: Date | null;
    endDate?: Date | null;
    amountMin?: string;
    amountMax?: string;
}

const statusColors: Record<InvoiceStatus, string> = {
    draft: 'gray',
    sent: 'blue',
    paid: 'green',
    overdue: 'orange',
    cancelled: 'red',
    refunded: 'purple',
} as const;

const InvoiceList: React.FC<InvoiceListProps> = ({
    limit = 10,
    showPagination = true,
    showFilters = true,
    clientId,
    status,
}) => {
    const [page, setPage] = useState(1);
    const [searchQuery, setSearchQuery] = useState('');
    const [filters, setFilters] = useState<InvoiceFiltersState>({});

    const toast = useToast();
    const queryClient = useQueryClient();

    const fetchInvoices = useCallback(async (): Promise<PaginatedResponse<Invoice>> => {
        const params: Record<string, unknown> = {
            page,
            limit,
            search: searchQuery,
            ...filters,
        };

        if (clientId) params.clientId = clientId;
        if (status) params.status = status;

        const response = await invoiceApi.getInvoices(params);
        return response;
    }, [page, limit, searchQuery, filters, clientId, status]);

    const {
        data: response,
        isLoading,
        isError,
    } = useQuery({
        queryKey: ['invoices', { page, limit, searchQuery, filters, clientId, status }],
        queryFn: fetchInvoices,
        placeholderData: (previousData: PaginatedResponse<Invoice> | undefined) =>
            previousData ?? {
                data: [],
                total: 0,
                page: 1,
                limit,
                totalPages: 0,
                hasNextPage: false,
                hasPreviousPage: false,
                from: 0,
                to: 0
            },
    });

    const { data: invoices = [], total = 0 } = response || {};

    const handleSearch = (query: string) => {
        setSearchQuery(query);
        setPage(1);
    };

    const handleFilterChange = (newFilters: InvoiceFiltersState) => {
        setFilters(newFilters);
        setPage(1);
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
                queryClient.invalidateQueries({ queryKey: ['invoices'] });
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

    if (isLoading && !response) {
        return (
            <Stack spacing={4}>
                {[...Array(5)].map((_, i) => (
                    <Skeleton key={i} height="60px" />
                ))}
            </Stack>
        );
    }

    if (isError) {
        return (
            <Box textAlign="center" py={10}>
                <Icon as={FiX} boxSize={10} color="red.500" mb={4} />
                <Text color="red.500" mb={4}>
                    Une erreur est survenue lors du chargement des factures.
                </Text>
                <Button colorScheme="blue" onClick={() => queryClient.invalidateQueries({ queryKey: ['invoices'] })}>
                    Réessayer
                </Button>
            </Box>
        );
    }

    if (invoices.length === 0) {
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

    const startItem = (page - 1) * limit + 1;
    const endItem = Math.min(page * limit, total);

    return (
        <Box>
            {showFilters && (
                <InvoiceFilters
                    onSearch={handleSearch}
                    onFilterChange={handleFilterChange}
                    onReset={handleResetFilters}
                    defaultFilters={filters}
                    clients={[]} // Add your clients data here if needed
                    statuses={Object.keys(statusColors) as InvoiceStatus[]}
                />
            )}

            <Box overflowX="auto" mt={6}>
                <Table variant="simple">
                    <Thead>
                        <Tr>
                            <Th>N° Facture</Th>
                            <Th>Client</Th>
                            <Th>Date</Th>
                            <Th>Échéance</Th>
                            <Th>Montant</Th>
                            <Th>Statut</Th>
                            <Th>Actions</Th>
                        </Tr>
                    </Thead>
                    <Tbody>
                        {invoices.map((invoice) => (
                            <Tr key={invoice.id} _hover={{ bg: 'gray.50' }}>
                                <Td>
                                    <Link as={RouterLink} to={`/invoices/${invoice.id}`} color="blue.500" fontWeight="medium">
                                        {invoice.invoiceNumber}
                                    </Link>
                                </Td>
                                <Td>{invoice.client?.name || 'N/A'}</Td>
                                <Td>
                                    {invoice.issueDate || invoice.createdAt
                                        ? format(new Date(invoice.issueDate || invoice.createdAt as string | number | Date), 'dd MMM yyyy')
                                        : 'N/A'}
                                </Td>
                                <Td>
                                    {invoice.dueDate
                                        ? format(new Date(invoice.dueDate as string | number | Date), 'dd MMM yyyy')
                                        : 'N/A'}
                                </Td>
                                <Td>{formatCurrency(invoice.totalAmount)}</Td>
                                <Td>
                                    <Badge colorScheme={statusColors[invoice.status]}>
                                        {invoice.status}
                                    </Badge>
                                </Td>
                                <Td>
                                    <Flex gap={2}>
                                        <IconButton
                                            as={RouterLink}
                                            to={`/invoices/${invoice.id}`}
                                            aria-label="Voir la facture"
                                            icon={<FiEye />}
                                            size="sm"
                                            variant="ghost"
                                        />
                                        <IconButton
                                            as="a"
                                            href={`/api/invoices/${invoice.id}/download`}
                                            download
                                            aria-label="Télécharger la facture"
                                            icon={<FiDownload />}
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
                                            onClick={() => handleDelete(invoice.id)}
                                            aria-label="Supprimer la facture"
                                            icon={<FiTrash2 />}
                                            size="sm"
                                            variant="ghost"
                                            colorScheme="red"
                                        />
                                    </Flex>
                                </Td>
                            </Tr>
                        ))}
                    </Tbody>
                </Table>
            </Box>

            {showPagination && total > limit && (
                <Flex justifyContent="space-between" alignItems="center" mt={6}>
                    <Text color="gray.600" fontSize="sm">
                        Affichage de {startItem} à {endItem} sur {total} factures
                    </Text>
                    <Flex gap={2}>
                        <Button
                            onClick={() => setPage((p) => Math.max(1, p - 1))}
                            isDisabled={page === 1}
                            size="sm"
                            variant="outline"
                        >
                            Précédent
                        </Button>
                        <Button
                            onClick={() => setPage((p) => p + 1)}
                            isDisabled={endItem >= total}
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
