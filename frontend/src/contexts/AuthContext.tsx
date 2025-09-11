import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { authApi } from '../services/api';

interface User {
    id: number;
    email: string;
    name: string;
    role: string;
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    login: (email: string, password: string) => Promise<void>;
    logout: () => void;
    isAuthenticated: boolean;
    loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(localStorage.getItem('auth_token'));
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        const loadUser = async () => {
            if (token) {
                try {
                    const response = await authApi.getMe();
                    setUser(response.data);
                } catch (error) {
                    console.error('Failed to load user', error);
                    logout();
                }
            }
            setLoading(false);
        };

        loadUser();
    }, [token]);

    const login = async (email: string, password: string) => {
        try {
            const response = await authApi.login({ email, password });
            const { token, user } = response.data;

            localStorage.setItem('auth_token', token);
            setToken(token);
            setUser(user);

            navigate('/dashboard');
        } catch (error) {
            console.error('Login failed', error);
            throw error;
        }
    };

    const logout = () => {
        localStorage.removeItem('auth_token');
        setToken(null);
        setUser(null);
        navigate('/login');
    };

    return (
        <AuthContext.Provider
            value={{
                user,
                token,
                login,
                logout,
                isAuthenticated: !!user,
                loading,
            }}
        >
            {!loading && children}
        </AuthContext.Provider>
    );
};

export const useAuth = (): AuthContextType => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
