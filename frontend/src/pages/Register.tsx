import React, { useState } from 'react';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import {
    Box,
    Button,
    FormControl,
    FormLabel,
    Input,
    InputGroup,
    InputRightElement,
    VStack,
    Text,
    Link,
    useToast,
    FormErrorMessage,
    useColorModeValue,
    Icon,
    Divider,
    Checkbox,
} from '@chakra-ui/react';
import { ViewIcon, ViewOffIcon, LockIcon, EmailIcon, ArrowForwardIcon } from '@chakra-ui/icons';
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { useAuth } from '../contexts/AuthContext';

interface RegisterFormData {
    name: string;
    email: string;
    password: string;
    confirmPassword: string;
    termsAccepted: boolean;
}

const schema = yup.object().shape({
    name: yup.string().required('Le nom est requis'),
    email: yup.string().email('Email invalide').required('Email est requis'),
    password: yup
        .string()
        .required('Mot de passe est requis')
        .min(8, 'Le mot de passe doit contenir au moins 8 caractères')
        .matches(
            /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]+$/,
            'Le mot de passe doit contenir au moins une majuscule, une minuscule, un chiffre et un caractère spécial'
        ),
    confirmPassword: yup
        .string()
        .oneOf([yup.ref('password'), null], 'Les mots de passe ne correspondent pas')
        .required('La confirmation du mot de passe est requise'),
    termsAccepted: yup
        .bool()
        .oneOf([true], 'Vous devez accepter les conditions d\'utilisation')
        .required('Vous devez accepter les conditions d\'utilisation'),
});

const Register: React.FC = () => {
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const { register: registerUser } = useAuth();
    const navigate = useNavigate();
    const toast = useToast();

    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<RegisterFormData>({
        resolver: yupResolver(schema),
    });

    const onSubmit = async (data: RegisterFormData) => {
        try {
            setIsLoading(true);
            await registerUser({
                name: data.name,
                email: data.email,
                password: data.password,
            });

            toast({
                title: 'Inscription réussie',
                description: 'Votre compte a été créé avec succès',
                status: 'success',
                duration: 5000,
                isClosable: true,
            });

            navigate('/login');
        } catch (error) {
            console.error('Registration error:', error);
            toast({
                title: 'Erreur lors de l\'inscription',
                description: 'Une erreur est survenue lors de la création de votre compte',
                status: 'error',
                duration: 5000,
                isClosable: true,
            });
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Box>
            <Text fontSize="2xl" fontWeight="bold" mb={6} textAlign="center">
                Créer un compte
            </Text>

            <form onSubmit={handleSubmit(onSubmit)}>
                <VStack spacing={4}>
                    <FormControl id="name" isInvalid={!!errors.name}>
                        <FormLabel>Nom complet</FormLabel>
                        <Input
                            type="text"
                            placeholder="Votre nom complet"
                            {...register('name')}
                            autoComplete="name"
                        />
                        <FormErrorMessage>
                            {errors.name && errors.name.message}
                        </FormErrorMessage>
                    </FormControl>

                    <FormControl id="email" isInvalid={!!errors.email}>
                        <FormLabel>Email</FormLabel>
                        <InputGroup>
                            <Input
                                type="email"
                                placeholder="votre@email.com"
                                {...register('email')}
                                autoComplete="email"
                            />
                        </InputGroup>
                        <FormErrorMessage>
                            {errors.email && errors.email.message}
                        </FormErrorMessage>
                    </FormControl>

                    <FormControl id="password" isInvalid={!!errors.password}>
                        <FormLabel>Mot de passe</FormLabel>
                        <InputGroup>
                            <Input
                                type={showPassword ? 'text' : 'password'}
                                placeholder="••••••••"
                                {...register('password')}
                                autoComplete="new-password"
                            />
                            <InputRightElement h="full">
                                <Button
                                    variant="ghost"
                                    onClick={() => setShowPassword(!showPassword)}
                                >
                                    {showPassword ? <ViewOffIcon /> : <ViewIcon />}
                                </Button>
                            </InputRightElement>
                        </InputGroup>
                        <FormErrorMessage>
                            {errors.password && errors.password.message}
                        </FormErrorMessage>
                    </FormControl>

                    <FormControl id="confirmPassword" isInvalid={!!errors.confirmPassword}>
                        <FormLabel>Confirmer le mot de passe</FormLabel>
                        <InputGroup>
                            <Input
                                type={showConfirmPassword ? 'text' : 'password'}
                                placeholder="••••••••"
                                {...register('confirmPassword')}
                                autoComplete="new-password"
                            />
                            <InputRightElement h="full">
                                <Button
                                    variant="ghost"
                                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                >
                                    {showConfirmPassword ? <ViewOffIcon /> : <ViewIcon />}
                                </Button>
                            </InputRightElement>
                        </InputGroup>
                        <FormErrorMessage>
                            {errors.confirmPassword && errors.confirmPassword.message}
                        </FormErrorMessage>
                    </FormControl>

                    <FormControl id="termsAccepted" isInvalid={!!errors.termsAccepted}>
                        <Checkbox
                            {...register('termsAccepted')}
                            colorScheme="blue"
                            size="md"
                        >
                            J'accepte les{' '}
                            <Link as={RouterLink} to="/terms" color="blue.500" _hover={{ textDecoration: 'underline' }}>
                                conditions d'utilisation
                            </Link>
                        </Checkbox>
                        <FormErrorMessage mt={1}>
                            {errors.termsAccepted && errors.termsAccepted.message}
                        </FormErrorMessage>
                    </FormControl>

                    <Button
                        type="submit"
                        colorScheme="blue"
                        width="100%"
                        size="lg"
                        mt={4}
                        isLoading={isLoading}
                        loadingText="Inscription en cours..."
                        rightIcon={<ArrowForwardIcon />}
                    >
                        S'inscrire
                    </Button>
                </VStack>
            </form>

            <Divider my={8} />

            <Text textAlign="center" color={useColorModeValue('gray.600', 'gray.400')}>
                Vous avez déjà un compte ?{' '}
                <Link
                    as={RouterLink}
                    to="/login"
                    color="blue.500"
                    _hover={{ textDecoration: 'underline' }}
                    fontWeight="medium"
                >
                    Se connecter
                </Link>
            </Text>
        </Box>
    );
};

export default Register;
