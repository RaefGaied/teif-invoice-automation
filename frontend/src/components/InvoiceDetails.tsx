import React, { useState, useEffect } from 'react';
import {
    Modal, ModalOverlay, ModalContent, ModalHeader, ModalFooter, ModalBody, ModalCloseButton,
    Button, Text, VStack, HStack, Box, Divider, Table, Thead, Tbody, Tr, Th, Td,
    Badge, useToast, useDisclosure, IconButton, Tooltip, useColorModeValue
} from '@chakra-ui/react';
import { DownloadIcon, PrintIcon, EmailIcon } from '@chakra-ui/icons';
import { invoiceApi } from '../services/api';
import { format } from 'date-fns';

interface InvoiceDetailsProps {
    isOpen: boolean;
    onClose: () => void;
    invoiceId: number;
}
interface Invoice {
    id: number;
    invoice_number: string;
    issue_date: string;
    due_date: string;
    status: 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled';
    subtotal: number;
    tax_amount: number;
    total_amount: number;
    items: Array<{
        id: number;
        description: string;
        quantity: number;
        unit_price: number;
        tax_rate: number;
        total: number;
    }>;
    company: {
        name: string;
        address: string;
        city: string;
        postal_code: string;
        tax_identification_number?: string;
    };
    customer: {
        name: string;
        email?: string;
        address: string;
        city: string;
        postal_code: string;
    };
}

const InvoiceDetails: React.FC<InvoiceDetailsProps> = ({ isOpen, onClose, invoiceId }) => {
    const [invoice, setInvoice] = useState<Invoice | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const toast = useToast();

    useEffect(() => {
        if (isOpen) {
            fetchInvoice();
        }
    }, [isOpen]);

    const fetchInvoice = async () => {
        try {
            const response = await invoiceApi.getInvoice(invoiceId);
            setInvoice(response.data);
        } catch (error) {
            toast({
                title: 'Erreur',
                description: 'Impossible de charger les détails de la facture',
                status: 'error',
                duration: 5000,
            });
        } finally {
            setIsLoading(false);
        }
    };

    const handleDownloadPdf = async () => {
        try {
            const response = await invoiceApi.downloadPdf(invoiceId);
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `facture-${invoice?.invoice_number}.pdf`);
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (error) {
            toast({
                title: 'Erreur',
                description: 'Échec du téléchargement du PDF',
                status: 'error',
                duration: 5000,
            });
        }
    };

    const formatDate = (dateString: string) => {
        return format(new Date(dateString), 'dd/MM/yyyy');
    };

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('fr-TN', {
            style: 'currency',
            currency: 'TND',
            minimumFractionDigits: 3,
        }).format(amount);
    };

    const statusColors = {
        draft: 'gray',
        sent: 'blue',
        paid: 'green',
        overdue: 'red',
        cancelled: 'red',
    };

    if (isLoading) {
        return (
            <Modal isOpen={isOpen} onClose={onClose} size="6xl">
                <ModalOverlay />
                <ModalContent>
                    <ModalHeader>Chargement...</ModalHeader>
                    <ModalCloseButton />
                    <ModalBody p={8} textAlign="center">
                        <Text>Chargement des détails de la facture...</Text>
                    </ModalBody>
                </ModalContent>
            </Modal>
        );
    }

    if (!invoice) {
        return (
            <Modal isOpen={isOpen} onClose={onClose} size="6xl">
                <ModalOverlay />
                <ModalContent>
                    <ModalHeader>Erreur</ModalHeader>
                    <ModalCloseButton />
                    <ModalBody p={8} textAlign="center">
                        <Text>Impossible de charger les détails de la facture.</Text>
                    </ModalBody>
                </ModalContent>
            </Modal>
        );
    }

    return (
        <Modal isOpen={isOpen} onClose={onClose} size="6xl" scrollBehavior="inside">
            <ModalOverlay />
            <ModalContent>
                <ModalHeader>
                    <HStack justify="space-between" align="center">
                        <Box>
                            <Text fontSize="2xl" fontWeight="bold">
                                Facture #{invoice.invoice_number}
                            </Text>
                            <Badge colorScheme={statusColors[invoice.status]} mt={1}>
                                {invoice.status.toUpperCase()}
                            </Badge>
                        </Box>
                        <HStack>
                            <Tooltip label="Télécharger le PDF">
                                <IconButton
                                    aria-label="Télécharger le PDF"
                                    icon={<DownloadIcon />}
                                    onClick={handleDownloadPdf}
                                    variant="ghost"
                                />
                            </Tooltip>
                            <Tooltip label="Imprimer">
                                <IconButton
                                    aria-label="Imprimer"
                                    icon={<PrintIcon />}
                                    onClick={() => window.print()}
                                    variant="ghost"
                                />
                            </Tooltip>
                        </HStack>
                    </HStack>
                </ModalHeader>
                <ModalCloseButton />

                <ModalBody p={8}>
                    {/* Header */}
                    <Box display="flex" justifyContent="space-between" mb={8}>
                        <Box>
                            <Text fontWeight="bold" fontSize="lg" mb={2}>
                                {invoice.company.name}
                            </Text>
                            <Text>{invoice.company.address}</Text>
                            <Text>{invoice.company.postal_code} {invoice.company.city}</Text>
                            {invoice.company.tax_identification_number && (
                                <Text>N° TVA: {invoice.company.tax_identification_number}</Text>
                            )}
                        </Box>
                        <Box textAlign="right">
                            <Text>Facture #{invoice.invoice_number}</Text>
                            <Text>Date: {formatDate(invoice.issue_date)}</Text>
                            <Text>Échéance: {formatDate(invoice.due_date)}</Text>
                        </Box>
                    </Box>

                    {/* Customer Info */}
                    <Box mb={8} p={4} bg={useColorModeValue('gray.50', 'gray.700')} borderRadius="md">
                        <Text fontWeight="bold" mb={2}>Client:</Text>
                        <Text>{invoice.customer.name}</Text>
                        <Text>{invoice.customer.address}</Text>
                        <Text>{invoice.customer.postal_code} {invoice.customer.city}</Text>
                        {invoice.customer.email && <Text>Email: {invoice.customer.email}</Text>}
                    </Box>

                    {/* Items */}
                    <Box mb={8} overflowX="auto">
                        <Table variant="simple">
                            <Thead>
                                <Tr>
                                    <Th>Description</Th>
                                    <Th isNumeric>Qté</Th>
                                    <Th isNumeric>Prix unitaire</Th>
                                    <Th isNumeric>TVA</Th>
                                    <Th isNumeric>Total</Th>
                                </Tr>
                            </Thead>
                            <Tbody>
                                {invoice.items.map((item) => (
                                    <Tr key={item.id}>
                                        <Td>{item.description}</Td>
                                        <Td isNumeric>{item.quantity}</Td>
                                        <Td isNumeric>{formatCurrency(item.unit_price)}</Td>
                                        <Td isNumeric>{item.tax_rate}%</Td>
                                        <Td isNumeric fontWeight="medium">
                                            {formatCurrency(item.total)}
                                        </Td>
                                    </Tr>
                                ))}
                            </Tbody>
                        </Table>
                    </Box>

                    {/* Totals */}
                    <Box ml="auto" maxW="md">
                        <VStack spacing={2} align="stretch">
                            <HStack justify="space-between">
                                <Text>Sous-total:</Text>
                                <Text>{formatCurrency(invoice.subtotal)}</Text>
                            </HStack>
                            <HStack justify="space-between">
                                <Text>TVA:</Text>
                                <Text>{formatCurrency(invoice.tax_amount)}</Text>
                            </HStack>
                            <Divider />
                            <HStack justify="space-between" fontSize="lg" fontWeight="bold">
                                <Text>Total:</Text>
                                <Text>{formatCurrency(invoice.total_amount)}</Text>
                            </HStack>
                        </VStack>
                    </Box>
                </ModalBody>

                <ModalFooter>
                    <Button variant="outline" mr={3} onClick={onClose}>
                        Fermer
                    </Button>
                    <Button colorScheme="blue" onClick={() => window.print()} leftIcon={<PrintIcon />}>
                        Imprimer
                    </Button>
                </ModalFooter>
            </ModalContent>
        </Modal>
    );
};

export default InvoiceDetails;
