'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';

export default function SignupPage() {
    const [formData, setFormData] = useState({
        email: '',
        full_name: '',
        password: '',
        confirmPassword: '',
        role: 'user' as 'user' | 'organizer',
    });
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const { signup } = useAuth();
    const router = useRouter();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        if (formData.password !== formData.confirmPassword) {
            setError('Passwords do not match');
            return;
        }

        if (formData.password.length < 8) {
            setError('Password must be at least 8 characters');
            return;
        }

        setIsLoading(true);

        try {
            await signup({
                email: formData.email,
                full_name: formData.full_name,
                password: formData.password,
                role: formData.role,
            });
        } catch (err: any) {
            setError(err.message || 'Signup failed');
        } finally {
            setIsLoading(false);
        }
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    return (
        <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
            {/* Animated background */}
            <div className="absolute inset-0 bg-gradient-to-br from-accent-900 via-dark-900 to-primary-900 opacity-50" />
            <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-10" />

            {/* Floating orbs */}
            <div className="absolute top-20 right-20 w-72 h-72 bg-accent-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob" />
            <div className="absolute bottom-20 left-20 w-72 h-72 bg-primary-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-2000" />
            <div className="absolute top-1/2 left-1/2 w-72 h-72 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-4000" />

            {/* Signup card */}
            <div className="relative z-10 w-full max-w-md">
                <div className="glass-dark rounded-2xl p-8 shadow-glass-lg border border-white/10">
                    {/* Logo */}
                    <div className="flex justify-center mb-8">
                        <div className="text-center">
                            <div className="flex items-center justify-center gap-3 mb-2">
                                <div className="w-10 h-10 bg-gradient-primary rounded-lg flex items-center justify-center">
                                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                                    </svg>
                                </div>
                                <h1 className="text-3xl font-bold text-gradient">Gatherly</h1>
                            </div>
                            <p className="text-dark-400 text-sm">Where great events come to life</p>
                        </div>
                    </div>

                    <h2 className="text-2xl font-bold text-dark-50 mb-2 text-center">Create your account</h2>
                    <p className="text-dark-400 text-center mb-6">Join Gatherly and start organizing events</p>

                    {error && (
                        <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <Input
                            label="Full Name"
                            name="full_name"
                            type="text"
                            placeholder="John Doe"
                            value={formData.full_name}
                            onChange={handleChange}
                            required
                        />

                        <Input
                            label="Email"
                            name="email"
                            type="email"
                            placeholder="you@example.com"
                            value={formData.email}
                            onChange={handleChange}
                            required
                        />

                        <Input
                            label="Password"
                            name="password"
                            type="password"
                            placeholder="••••••••"
                            value={formData.password}
                            onChange={handleChange}
                            helperText="At least 8 characters"
                            required
                        />

                        <Input
                            label="Confirm Password"
                            name="confirmPassword"
                            type="password"
                            placeholder="••••••••"
                            value={formData.confirmPassword}
                            onChange={handleChange}
                            required
                        />

                        <div>
                            <label className="block text-sm font-medium text-dark-200 mb-2">
                                I want to...
                            </label>
                            <div className="grid grid-cols-2 gap-3">
                                <button
                                    type="button"
                                    onClick={() => setFormData({ ...formData, role: 'user' })}
                                    className={`p-4 rounded-lg border-2 transition-all ${formData.role === 'user'
                                            ? 'border-primary-500 bg-primary-500/10'
                                            : 'border-dark-700 bg-dark-800/50 hover:border-dark-600'
                                        }`}
                                >
                                    <div className="text-center">
                                        <div className="text-2xl mb-1">👤</div>
                                        <div className="text-sm font-medium text-dark-100">Attend Events</div>
                                    </div>
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setFormData({ ...formData, role: 'organizer' })}
                                    className={`p-4 rounded-lg border-2 transition-all ${formData.role === 'organizer'
                                            ? 'border-primary-500 bg-primary-500/10'
                                            : 'border-dark-700 bg-dark-800/50 hover:border-dark-600'
                                        }`}
                                >
                                    <div className="text-center">
                                        <div className="text-2xl mb-1">🎯</div>
                                        <div className="text-sm font-medium text-dark-100">Organize Events</div>
                                    </div>
                                </button>
                            </div>
                        </div>

                        <Button type="submit" className="w-full" isLoading={isLoading}>
                            Create account
                        </Button>
                    </form>

                    <div className="mt-6 text-center">
                        <p className="text-dark-400 text-sm">
                            Already have an account?{' '}
                            <Link href="/login" className="text-primary-400 hover:text-primary-300 font-medium transition-colors">
                                Sign in
                            </Link>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
