import React, { useState, useEffect } from 'react';
import {
    Box,
    Input,
    InputGroup,
    InputLeftElement,
    Select,
    HStack,
    Button,
    useDisclosure,
    useBreakpointValue,
    IconButton,
    Icon,
    Menu,
    MenuButton,
    MenuList,
    MenuItem,
    VStack,
    Text,
    useColorModeValue,
} from '@chakra-ui/react';
import { SearchIcon, FilterIcon, X, Calendar, FileText, User, Tag } from 'lucide-react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { format, subDays, startOfMonth, endOfMonth } from 'date-fns';
import { fr } from 'date-fns/locale';

interface InvoiceFiltersProps {
    onSearch: (query: string) => void;
    onFilterChange: (filters: any) => void;
    onReset: () => void;
    clients: Array<{ id: number; name: string }>;
    statuses: string[];
    defaultFilters?: any;
}

const dateRanges = [
    { label: 'Aujourd\'hui', value: 'today' },
    { label: 'Hier', value: 'yesterday' },
    { label: '7 derniers jours', value: 'last7days' },
    { label: '30 derniers jours', value: 'last30days' },
    { label: 'Ce mois', value: 'thisMonth' },
    { label: 'Mois dernier', value: 'lastMonth' },
    { label: 'Personnalisé', value: 'custom' },
];

const InvoiceFilters: React.FC<InvoiceFiltersProps> = ({
    onSearch,
    onFilterChange,
    onReset,
    clients = [],
    statuses = [],
    defaultFilters = {},
}) => {
    const [searchQuery, setSearchQuery] = useState('');
    const [filters, setFilters] = useState({
        status: '',
        clientId: '',
        dateRange: '',
        startDate: null as Date | null,
        endDate: null as Date | null,
        amountMin: '',
        amountMax: '',
        ...defaultFilters,
    });

    const { isOpen, onToggle } = useDisclosure();
    const isMobile = useBreakpointValue({ base: true, md: false });
    const bgColor = useColorModeValue('white', 'gray.800');
    const borderColor = useColorModeValue('gray.200', 'gray.700');

    useEffect(() => {
        const timer = setTimeout(() => {
            onSearch(searchQuery);
        }, 500);

        return () => clearTimeout(timer);
    }, [searchQuery, onSearch]);

    const handleFilterChange = (name: string, value: any) => {
        const newFilters = { ...filters, [name]: value };
        setFilters(newFilters);

        // Handle date range presets
        if (name === 'dateRange') {
            const today = new Date();
            let startDate = null;
            let endDate = null;

            switch (value) {
                case 'today':
                    startDate = today;
                    endDate = today;
                    break;
                case 'yesterday':
                    const yesterday = subDays(today, 1);
                    startDate = yesterday;
                    endDate = yesterday;
                    break;
                case 'last7days':
                    startDate = subDays(today, 7);
                    endDate = today;
                    break;
                case 'last30days':
                    startDate = subDays(today, 30);
                    endDate = today;
                    break;
                case 'thisMonth':
                    startDate = startOfMonth(today);
                    endDate = endOfMonth(today);
                    break;
                case 'lastMonth':
                    const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1);
                    startDate = startOfMonth(firstDayOfMonth);
                    endDate = endOfMonth(firstDayOfMonth);
                    break;
            }

            newFilters.startDate = startDate;
            newFilters.endDate = endDate;
            setFilters(newFilters);
        }

        onFilterChange(newFilters);
    };

    const handleReset = () => {
        setSearchQuery('');
        const resetFilters = {
            status: '',
            clientId: '',
            dateRange: '',
            startDate: null,
            endDate: null,
            amountMin: '',
            amountMax: '',
        };
        setFilters(resetFilters);
        onReset();
    };

    const hasActiveFilters = Object.values(filters).some(
        (value) => value !== '' && value !== null
    ) || searchQuery !== '';

    const FilterMenu = () => (
        <Menu closeOnSelect={false}>
            <MenuButton
                as={Button}
                leftIcon={<Icon as={FilterIcon} />}
                variant="outline"
                size={isMobile ? 'sm' : 'md'}
            >
                Filtres
            </MenuButton>
            <MenuList p={4} minW="300px">
                <VStack spacing={4} align="stretch">
                    <Box>
                        <Text fontSize="sm" fontWeight="medium" mb={2}>
                            Statut
                        </Text>
                        <Select
                            size="sm"
                            value={filters.status}
                            onChange={(e) => handleFilterChange('status', e.target.value)}
                            placeholder="Tous les statuts"
                        >
                            {statuses.map((status) => (
                                <option key={status} value={status}>
                                    {status}
                                </option>
                            ))}
                        </Select>
                    </Box>

                    <Box>
                        <Text fontSize="sm" fontWeight="medium" mb={2}>
                            Client
                        </Text>
                        <Select
                            size="sm"
                            value={filters.clientId}
                            onChange={(e) => handleFilterChange('clientId', e.target.value)}
                            placeholder="Tous les clients"
                        >
                            {clients.map((client) => (
                                <option key={client.id} value={client.id}>
                                    {client.name}
                                </option>
                            ))}
                        </Select>
                    </Box>

                    <Box>
                        <Text fontSize="sm" fontWeight="medium" mb={2}>
                            Période
                        </Text>
                        <Select
                            size="sm"
                            value={filters.dateRange}
                            onChange={(e) => handleFilterChange('dateRange', e.target.value)}
                            placeholder="Toutes les dates"
                            mb={filters.dateRange === 'custom' ? 2 : 0}
                        >
                            {dateRanges.map((range) => (
                                <option key={range.value} value={range.value}>
                                    {range.label}
                                </option>
                            ))}
                        </Select>

                        {filters.dateRange === 'custom' && (
                            <HStack mt={2} spacing={2}>
                                <Box flex={1}>
                                    <DatePicker
                                        selected={filters.startDate}
                                        onChange={(date: Date) => handleFilterChange('startDate', date)}
                                        selectsStart
                                        startDate={filters.startDate}
                                        endDate={filters.endDate}
                                        locale={fr}
                                        dateFormat="dd/MM/yyyy"
                                        placeholderText="Du..."
                                        className="chakra-input"
                                        customInput={
                                            <Input
                                                size="sm"
                                                placeholder="Du..."
                                                leftElement={<Icon as={Calendar} boxSize={4} color="gray.500" />}
                                            />
                                        }
                                    />
                                </Box>
                                <Box flex={1}>
                                    <DatePicker
                                        selected={filters.endDate}
                                        onChange={(date: Date) => handleFilterChange('endDate', date)}
                                        selectsEnd
                                        startDate={filters.startDate}
                                        endDate={filters.endDate}
                                        minDate={filters.startDate}
                                        locale={fr}
                                        dateFormat="dd/MM/yyyy"
                                        placeholderText="Au..."
                                        className="chakra-input"
                                        customInput={
                                            <Input
                                                size="sm"
                                                placeholder="Au..."
                                                leftElement={<Icon as={Calendar} boxSize={4} color="gray.500" />}
                                            />
                                        }
                                    />
                                </Box>
                            </HStack>
                        )}
                    </Box>

                    <Box>
                        <Text fontSize="sm" fontWeight="medium" mb={2}>
                            Montant
                        </Text>
                        <HStack spacing={2}>
                            <Input
                                size="sm"
                                placeholder="Min"
                                value={filters.amountMin}
                                onChange={(e) => handleFilterChange('amountMin', e.target.value)}
                                type="number"
                                leftElement={<Text color="gray.500" fontSize="sm" px={2}>€</Text>}
                            />
                            <Text>à</Text>
                            <Input
                                size="sm"
                                placeholder="Max"
                                value={filters.amountMax}
                                onChange={(e) => handleFilterChange('amountMax', e.target.value)}
                                type="number"
                                leftElement={<Text color="gray.500" fontSize="sm" px={2}>€</Text>}
                            />
                        </HStack>
                    </Box>
                </VStack>
            </MenuList>
        </Menu>
    );

    return (
        <Box mb={6}>
            <Box
                bg={bgColor}
                p={4}
                borderRadius="lg"
                borderWidth="1px"
                borderColor={borderColor}
            >
                <VStack spacing={4} align="stretch">
                    <InputGroup size="md">
                        <InputLeftElement pointerEvents="none">
                            <Icon as={SearchIcon} color="gray.400" />
                        </InputLeftElement>
                        <Input
                            placeholder="Rechercher des factures..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            pr="4.5rem"
                        />
                    </InputGroup>

                    <HStack spacing={2} flexWrap="wrap">
                        {isMobile ? (
                            <FilterMenu />
                        ) : (
                            <>
                                <Select
                                    size="sm"
                                    value={filters.status}
                                    onChange={(e) => handleFilterChange('status', e.target.value)}
                                    placeholder="Statut"
                                    width="150px"
                                >
                                    {statuses.map((status) => (
                                        <option key={status} value={status}>
                                            {status}
                                        </option>
                                    ))}
                                </Select>

                                <Select
                                    size="sm"
                                    value={filters.clientId}
                                    onChange={(e) => handleFilterChange('clientId', e.target.value)}
                                    placeholder="Client"
                                    width="180px"
                                >
                                    {clients.map((client) => (
                                        <option key={client.id} value={client.id}>
                                            {client.name}
                                        </option>
                                    ))}
                                </Select>

                                <Select
                                    size="sm"
                                    value={filters.dateRange}
                                    onChange={(e) => handleFilterChange('dateRange', e.target.value)}
                                    placeholder="Période"
                                    width="180px"
                                >
                                    {dateRanges.map((range) => (
                                        <option key={range.value} value={range.value}>
                                            {range.label}
                                        </option>
                                    ))}
                                </Select>

                                {filters.dateRange === 'custom' && (
                                    <HStack spacing={2}>
                                        <DatePicker
                                            selected={filters.startDate}
                                            onChange={(date: Date) => handleFilterChange('startDate', date)}
                                            selectsStart
                                            startDate={filters.startDate}
                                            endDate={filters.endDate}
                                            locale={fr}
                                            dateFormat="dd/MM/yyyy"
                                            placeholderText="Du..."
                                            className="chakra-input"
                                            customInput={
                                                <Input
                                                    size="sm"
                                                    width="120px"
                                                    placeholder="Du..."
                                                    leftElement={<Icon as={Calendar} boxSize={4} color="gray.500" />}
                                                />
                                            }
                                        />
                                        <DatePicker
                                            selected={filters.endDate}
                                            onChange={(date: Date) => handleFilterChange('endDate', date)}
                                            selectsEnd
                                            startDate={filters.startDate}
                                            endDate={filters.endDate}
                                            minDate={filters.startDate}
                                            locale={fr}
                                            dateFormat="dd/MM/yyyy"
                                            placeholderText="Au..."
                                            className="chakra-input"
                                            customInput={
                                                <Input
                                                    size="sm"
                                                    width="120px"
                                                    placeholder="Au..."
                                                    leftElement={<Icon as={Calendar} boxSize={4} color="gray.500" />}
                                                />
                                            }
                                        />
                                    </HStack>
                                )}
                            </>
                        )}

                        {hasActiveFilters && (
                            <Button
                                size={isMobile ? 'sm' : 'md'}
                                variant="ghost"
                                leftIcon={<Icon as={X} />}
                                onClick={handleReset}
                            >
                                {isMobile ? 'Réinitialiser' : 'Réinitialiser les filtres'}
                            </Button>
                        )}
                    </HStack>
                </VStack>
            </Box>

            {/* Active filters chips */}
            {hasActiveFilters && (
                <HStack mt={3} spacing={2} flexWrap="wrap">
                    {filters.status && (
                        <Box
                            bg={useColorModeValue('blue.50', 'blue.900')}
                            color={useColorModeValue('blue.700', 'blue.200')}
                            px={3}
                            py={1}
                            borderRadius="full"
                            fontSize="sm"
                            display="flex"
                            alignItems="center"
                        >
                            <Icon as={Tag} boxSize={3} mr={1} />
                            {filters.status}
                            <Icon
                                as={X}
                                boxSize={3}
                                ml={1}
                                cursor="pointer"
                                onClick={() => handleFilterChange('status', '')}
                            />
                        </Box>
                    )}

                    {filters.clientId && (
                        <Box
                            bg={useColorModeValue('purple.50', 'purple.900')}
                            color={useColorModeValue('purple.700', 'purple.200')}
                            px={3}
                            py={1}
                            borderRadius="full"
                            fontSize="sm"
                            display="flex"
                            alignItems="center"
                        >
                            <Icon as={User} boxSize={3} mr={1} />
                            {clients.find((c) => c.id === parseInt(filters.clientId))?.name}
                            <Icon
                                as={X}
                                boxSize={3}
                                ml={1}
                                cursor="pointer"
                                onClick={() => handleFilterChange('clientId', '')}
                            />
                        </Box>
                    )}

                    {(filters.startDate || filters.endDate) && (
                        <Box
                            bg={useColorModeValue('green.50', 'green.900')}
                            color={useColorModeValue('green.700', 'green.200')}
                            px={3}
                            py={1}
                            borderRadius="full"
                            fontSize="sm"
                            display="flex"
                            alignItems="center"
                        >
                            <Icon as={Calendar} boxSize={3} mr={1} />
                            {filters.startDate && format(new Date(filters.startDate), 'dd MMM yyyy', { locale: fr })}
                            {filters.endDate && ` - ${format(new Date(filters.endDate), 'dd MMM yyyy', { locale: fr })}`}
                            <Icon
                                as={X}
                                boxSize={3}
                                ml={1}
                                cursor="pointer"
                                onClick={() => {
                                    handleFilterChange('dateRange', '');
                                    handleFilterChange('startDate', null);
                                    handleFilterChange('endDate', null);
                                }}
                            />
                        </Box>
                    )}

                    {(filters.amountMin || filters.amountMax) && (
                        <Box
                            bg={useColorModeValue('orange.50', 'orange.900')}
                            color={useColorModeValue('orange.700', 'orange.200')}
                            px={3}
                            py={1}
                            borderRadius="full"
                            fontSize="sm"
                            display="flex"
                            alignItems="center"
                        >
                            <Icon as={FileText} boxSize={3} mr={1} />
                            {filters.amountMin && `${filters.amountMin}€`}
                            {filters.amountMin && filters.amountMax && ' - '}
                            {filters.amountMax && `${filters.amountMax}€`}
                            <Icon
                                as={X}
                                boxSize={3}
                                ml={1}
                                cursor="pointer"
                                onClick={() => {
                                    handleFilterChange('amountMin', '');
                                    handleFilterChange('amountMax', '');
                                }}
                            />
                        </Box>
                    )}
                </HStack>
            )}
        </Box>
    );
};

export default InvoiceFilters;
