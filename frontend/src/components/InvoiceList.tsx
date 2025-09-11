import React, { useEffect, useState } from 'react';
import {
    Box,
    Button,
    Flex,
    Heading,
    Spinner,
    Table,
    Thead,
    Tbody,
    Tr,
    Th,
    Td,
    Text,
    Badge,
    useDisclosure,
    Modal,
    ModalOverlay,
    ModalContent,
    ModalHeader,
    ModalBody,
    ModalCloseButton,
    useToast,
    HStack,
} from '@chakra-ui/react';
import { ViewIcon, DeleteIcon } from '@chakra-ui/icons';
import { invoiceApi } from '../services/api';

interface Invoice {
    id: number;
    invoice_number: string;
    date: string;
    total_amount: number;
    status: 'draft' | 'paid' | 'overdue' | 'cancelled';
    // Add other invoice fields as needed
}

interface InvoiceListProps {
    limit?: number;
    showPagination?: boolean;
}

const InvoiceList: React.FC<InvoiceListProps> = ({
    limit,
    showPagination = true,
}) => {
    const [invoices, setInvoices] = useState<Invoice[]>([]);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);
    const { isOpen, onOpen, onClose } = useDisclosure();
    const toast = useToast();
    const itemsPerPage = limit || 10;

    const fetchInvoices = async (page: number = 1) => {
        try {
            setIsLoading(true);
            const response = await invoiceApi.getInvoices({
                page,
                limit: itemsPerPage,
            });

            setInvoices(response.data.invoices);
            setTotalPages(Math.ceil(response.data.total / itemsPerPage));
            setCurrentPage(page);
        } catch (err) {
            console.error('Error fetching invoices:', err);
            setError('Failed to load invoices');
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchInvoices(currentPage);
    }, [currentPage, itemsPerPage]);

    const handleDelete = async (id: number) => {
        if (window.confirm('Are you sure you want to delete this invoice?')) {
            try {
                await invoiceApi.deleteInvoice(id);
                toast({
                    title: 'Success',
                    description: 'Invoice deleted successfully',
                    status: 'success',
                    duration: 3000,
                    isClosable: true,
                });
                fetchInvoices();
            } catch (err) {
                toast({
                    title: 'Error',
                    description: 'Failed to delete invoice',
                    status: 'error',
                    duration: 3000,
                    isClosable: true,
                });
            }
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'paid':
                return 'green';
            case 'overdue':
                return 'red';
            case 'draft':
                return 'yellow';
            case 'cancelled':
                return 'gray';
            default:
                return 'blue';
        }
    };

    if (isLoading) {
        return (
            <Flex justify="center" align="center" minH="200px">
                <Spinner size="xl" />
            </Flex>
        );
    }

    if (error) {
        return (
            <Box p={5} color="red.500">
                {error}
            </Box>
        );
    }

    return (
        <Box p={5}>
            <Flex justify="space-between" align="center" mb={5}>
                <Heading size="lg">Invoices</Heading>
                <Button colorScheme="blue" onClick={() => window.location.href = '/invoices/new'}>
                    Create Invoice
                </Button>
            </Flex>

            <Box overflowX="auto">
                <Table variant="simple">
                    <Thead>
                        <Tr>
                            <Th>Invoice #</Th>
                            <Th>Date</Th>
                            <Th isNumeric>Amount</Th>
                            <Th>Status</Th>
                            <Th>Actions</Th>
                        </Tr>
                    </Thead>
                    <Tbody>
                        {invoices.length > 0 ? (
                            invoices.map((invoice) => (
                                <Tr key={invoice.id}>
                                    <Td>{invoice.invoice_number}</Td>
                                    <Td>{new Date(invoice.date).toLocaleDateString()}</Td>
                                    <Td isNumeric>${invoice.total_amount.toFixed(2)}</Td>
                                    <Td>
                                        <Badge colorScheme={getStatusColor(invoice.status)}>
                                            {invoice.status.toUpperCase()}
                                        </Badge>
                                    </Td>
                                    <Td>
                                        <Button
                                            size="sm"
                                            colorScheme="blue"
                                            leftIcon={<ViewIcon />}
                                            mr={2}
                                            onClick={() => {
                                                setSelectedInvoice(invoice);
                                                onOpen();
                                            }}
                                        >
                                            View
                                        </Button>
                                        <Button
                                            size="sm"
                                            colorScheme="red"
                                            variant="outline"
                                            leftIcon={<DeleteIcon />}
                                            onClick={() => handleDelete(invoice.id)}
                                        >
                                            Delete
                                        </Button>
                                    </Td>
                                </Tr>
                            ))
                        ) : (
                            <Tr>
                                <Td colSpan={5} textAlign="center" py={10}>
                                    <Text color="gray.500">No invoices found</Text>
                                </Td>
                            </Tr>
                        )}
                    </Tbody>
                </Table>
            </Box>

            {showPagination && totalPages > 1 && (
                <Flex justify="flex-end" mt={4}>
                    <HStack spacing={2}>
                        <Button
                            onClick={() => fetchInvoices(currentPage - 1)}
                            isDisabled={currentPage === 1}
                            size="sm"
                        >
                            Précédent
                        </Button>
                        <Text>
                            Page {currentPage} sur {totalPages}
                        </Text>
                        <Button
                            onClick={() => fetchInvoices(currentPage + 1)}
                            isDisabled={currentPage === totalPages}
                            size="sm"
                        >
                            Suivant
                        </Button>
                    </HStack>
                </Flex>
            )}

            {/* Invoice Details Modal */}
            <Modal isOpen={isOpen} onClose={onClose} size="xl">
                <ModalOverlay />
                <ModalContent>
                    <ModalHeader>Invoice Details</ModalHeader>
                    <ModalCloseButton />
                    <ModalBody pb={6}>
                        {selectedInvoice && (
                            <Box>
                                <Text><strong>Invoice #:</strong> {selectedInvoice.invoice_number}</Text>
                                <Text><strong>Date:</strong> {new Date(selectedInvoice.date).toLocaleDateString()}</Text>
                                <Text><strong>Amount:</strong> ${selectedInvoice.total_amount.toFixed(2)}</Text>
                                <Text>
                                    <strong>Status:</strong>{' '}
                                    <Badge colorScheme={getStatusColor(selectedInvoice.status)} ml={2}>
                                        {selectedInvoice.status.toUpperCase()}
                                    </Badge>
                                </Text>
                                {/* Add more invoice details here */}
                            </Box>
                        )}
                    </ModalBody>
                </ModalContent>
            </Modal>
        </Box>
    );
};

export default InvoiceList;
