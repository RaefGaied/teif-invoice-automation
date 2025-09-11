import React from 'react';
import { Outlet } from 'react-router-dom';
import { Box, Flex, Image, useColorModeValue } from '@chakra-ui/react';

const AuthLayout: React.FC = () => {
    const bgColor = useColorModeValue('gray.50', 'gray.900');
    const cardBg = useColorModeValue('white', 'gray.800');
    const borderColor = useColorModeValue('gray.200', 'gray.700');

    return (
        <Flex
            minH="100vh"
            align="center"
            justify="center"
            bg={bgColor}
            p={4}
        >
            <Box
                w="100%"
                maxW="md"
                p={8}
                borderWidth={1}
                borderRadius="lg"
                boxShadow="lg"
                bg={cardBg}
                borderColor={borderColor}
            >
                <Box textAlign="center" mb={8}>
                    <Box display="inline-block" mb={4}>
                        <Image
                            src="/logo.svg"
                            alt="TEIF Invoice"
                            h="40px"
                            w="auto"
                            mx="auto"
                        />
                    </Box>
                    <Box as="h1" fontSize="2xl" fontWeight="bold">
                        TEIF Invoice
                    </Box>
                    <Box color="gray.500" mt={2}>
                        Gestion des factures électroniques
                    </Box>
                </Box>

                <Outlet />

                <Box mt={8} textAlign="center" color="gray.500" fontSize="sm">
                    © {new Date().getFullYear()} TEIF Invoice. Tous droits réservés.
                </Box>
            </Box>
        </Flex>
    );
};

export default AuthLayout;
