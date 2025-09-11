import React, { useEffect, useState } from 'react';
import {
    Box,
    SimpleGrid,
    Stat,
    StatLabel,
    StatNumber,
    StatHelpText,
    StatArrow,
    Text,
    useColorModeValue,
    Heading,
    Flex,
    Icon,
    HStack,
    Select,
    VStack,
    Spinner,
} from '@chakra-ui/react';
import { FiDollarSign, FiFileText, FiTrendingUp, FiAlertCircle } from 'react-icons/fi';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { invoiceApi } from '../services/api';
import InvoiceList from './InvoiceList';

interface DashboardStats {
    totalInvoices: number;
    totalRevenue: number;
    pendingInvoices: number;
    overdueInvoices: number;
    revenueTrend: number;
    invoiceTrend: number;
}

interface MonthlyData {
    month: string;
    revenue: number;
    invoices: number;
}

const Dashboard: React.FC = () => {
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [monthlyData, setMonthlyData] = useState<MonthlyData[]>([]);
    const [timeRange, setTimeRange] = useState<string>('month');
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const cardBg = useColorModeValue('white', 'gray.800');
    const borderColor = useColorModeValue('gray.200', 'gray.700');

    useEffect(() => {
        const fetchDashboardData = async () => {
            try {
                setIsLoading(true);
                setError(null);

                // Fetch dashboard statistics
                const [statsRes, monthlyRes] = await Promise.all([
                    invoiceApi.getDashboardStats(),
                    invoiceApi.getMonthlyStats({ months: 6 })
                ]);

                setStats(statsRes.data);
                setMonthlyData(monthlyRes.data);
            } catch (err) {
                console.error('Error fetching dashboard data:', err);
                setError('Failed to load dashboard data. Please try again later.');
            } finally {
                setIsLoading(false);
            }
        };

        fetchDashboardData();
    }, [timeRange]);

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('fr-TN', {
            style: 'currency',
            currency: 'TND',
            minimumFractionDigits: 3,
        }).format(amount);
    };

    const StatCard = ({
        title,
        value,
        icon,
        trend,
        trendValue,
        isCurrency = false
    }: {
        title: string;
        value: number;
        icon: any;
        trend?: 'increase' | 'decrease' | 'neutral';
        trendValue?: number;
        isCurrency?: boolean;
    }) => (
        <Box
            p={5}
            bg={cardBg}
            borderRadius="lg"
            boxShadow="sm"
            borderWidth="1px"
            borderColor={borderColor}
        >
            <HStack justify="space-between" align="flex-start">
                <Box>
                    <Text fontSize="sm" color="gray.500" mb={1}>
                        {title}
                    </Text>
                    <Text fontSize="2xl" fontWeight="bold">
                        {isCurrency ? formatCurrency(value) : value}
                    </Text>
                    {trend && trendValue !== undefined && (
                        <HStack mt={2} spacing={1}>
                            <StatArrow
                                type={trend === 'increase' ? 'increase' : 'decrease'}
                                color={trend === 'increase' ? 'green.500' : 'red.500'}
                            />
                            <Text
                                fontSize="sm"
                                color={trend === 'increase' ? 'green.500' : 'red.500'}
                            >
                                {Math.abs(trendValue)}% {trend === 'increase' ? 'plus' : 'moins'}
                            </Text>
                            <Text fontSize="sm" color="gray.500">
                                vs. période précédente
                            </Text>
                        </HStack>
                    )}
                </Box>
                <Box
                    p={3}
                    bg={useColorModeValue('blue.50', 'blue.900')}
                    borderRadius="full"
                    color={useColorModeValue('blue.500', 'blue.200')}
                >
                    <Icon as={icon} boxSize={5} />
                </Box>
            </HStack>
        </Box>
    );

    if (isLoading) {
        return (
            <Flex justify="center" align="center" minH="50vh">
                <Spinner size="xl" />
            </Flex>
        );
    }

    if (error) {
        return (
            <Box textAlign="center" py={10} px={6}>
                <Icon as={FiAlertCircle} boxSize={12} color="red.500" mb={4} />
                <Heading as="h2" size="lg" mb={2}>
                    Erreur de chargement
                </Heading>
                <Text color="gray.600" mb={4}>
                    {error}
                </Text>
                <Button colorScheme="blue" onClick={() => window.location.reload()}>
                    Réessayer
                </Button>
            </Box>
        );
    }

    if (!stats) return null;

    return (
        <Box p={{ base: 4, md: 6 }}>
            <Flex justify="space-between" align="center" mb={6}>
                <Heading as="h1" size="xl">
                    Tableau de bord
                </Heading>
                <Select
                    value={timeRange}
                    onChange={(e) => setTimeRange(e.target.value)}
                    width="200px"
                    size="sm"
                >
                    <option value="week">7 derniers jours</option>
                    <option value="month">30 derniers jours</option>
                    <option value="quarter">3 derniers mois</option>
                    <option value="year">12 derniers mois</option>
                </Select>
            </Flex>

            {/* Stats Grid */}
            <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={6} mb={8}>
                <StatCard
                    title="Chiffre d'affaires"
                    value={stats.totalRevenue}
                    icon={FiDollarSign}
                    trend={stats.revenueTrend >= 0 ? 'increase' : 'decrease'}
                    trendValue={Math.abs(stats.revenueTrend)}
                    isCurrency
                />
                <StatCard
                    title="Factures totales"
                    value={stats.totalInvoices}
                    icon={FiFileText}
                    trend={stats.invoiceTrend >= 0 ? 'increase' : 'decrease'}
                    trendValue={Math.abs(stats.invoiceTrend)}
                />
                <StatCard
                    title="Factures en attente"
                    value={stats.pendingInvoices}
                    icon={FiAlertCircle}
                />
                <StatCard
                    title="Factures en retard"
                    value={stats.overdueInvoices}
                    icon={FiAlertCircle}
                />
            </SimpleGrid>

            {/* Charts */}
            <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6} mb={8}>
                <Box
                    p={5}
                    bg={cardBg}
                    borderRadius="lg"
                    boxShadow="sm"
                    borderWidth="1px"
                    borderColor={borderColor}
                >
                    <Text fontSize="lg" fontWeight="medium" mb={4}>
                        Revenus mensuels
                    </Text>
                    <Box height={300}>
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={monthlyData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="month" />
                                <YAxis />
                                <Tooltip
                                    formatter={(value: number) => [formatCurrency(Number(value)), 'Revenu']}
                                />
                                <Legend />
                                <Line
                                    type="monotone"
                                    dataKey="revenue"
                                    name="Revenu"
                                    stroke="#4f46e5"
                                    strokeWidth={2}
                                    dot={{ r: 4 }}
                                    activeDot={{ r: 6 }}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </Box>
                </Box>

                <Box
                    p={5}
                    bg={cardBg}
                    borderRadius="lg"
                    boxShadow="sm"
                    borderWidth="1px"
                    borderColor={borderColor}
                >
                    <Text fontSize="lg" fontWeight="medium" mb={4}>
                        Nombre de factures
                    </Text>
                    <Box height={300}>
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={monthlyData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="month" />
                                <YAxis />
                                <Tooltip />
                                <Legend />
                                <Bar dataKey="invoices" name="Factures" fill="#4f46e5" />
                            </BarChart>
                        </ResponsiveContainer>
                    </Box>
                </Box>
            </SimpleGrid>

            {/* Recent Invoices */}
            <Box
                p={5}
                bg={cardBg}
                borderRadius="lg"
                boxShadow="sm"
                borderWidth="1px"
                borderColor={borderColor}
            >
                <Text fontSize="lg" fontWeight="medium" mb={4}>
                    Dernières factures
                </Text>
                <InvoiceList limit={5} showPagination={false} />
            </Box>
        </Box>
    );
};

export default Dashboard;
