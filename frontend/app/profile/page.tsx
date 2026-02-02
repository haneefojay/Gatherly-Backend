'use client';

import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import api from '@/lib/api';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Spinner from '@/components/ui/Spinner';
import { User as UserIcon, Mail, Shield } from 'lucide-react';
import { User } from '@/lib/types';

export default function ProfilePage() {
    const { user, updateUser } = useAuth();
    const [loading, setLoading] = useState(false);
    const [formData, setFormData] = useState({
        full_name: user?.full_name || '',
        email: user?.email || '',
    });
    const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setMessage(null);

        try {
            const response = await api.put<User>('/users/me', formData);
            updateUser(response.data);
            setMessage({ type: 'success', text: 'Profile updated successfully' });
        } catch (err: any) {
            setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to update profile' });
        } finally {
            setLoading(false);
        }
    };

    if (!user) return null;

    return (
        <div className="min-h-screen bg-dark-900 py-12">
            <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
                <h1 className="text-3xl font-bold text-white mb-8">Your Profile</h1>

                <div className="grid gap-6">
                    <Card>
                        <h2 className="text-xl font-bold text-white mb-6">Personal Information</h2>
                        
                        {message && (
                            <div className={`p-4 rounded-lg mb-6 ${message.type === 'success' ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'}`}>
                                {message.text}
                            </div>
                        )}

                        <form onSubmit={handleSubmit} className="space-y-6">
                             {/* Inputs */}
                             <div>
                                <label className="block text-sm font-medium text-dark-300 mb-2">Full Name</label>
                                <div className="relative">
                                    <UserIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-500" />
                                    <Input 
                                        value={formData.full_name} 
                                        onChange={e => setFormData({...formData, full_name: e.target.value})}
                                        className="pl-10"
                                        required
                                    />
                                </div>
                             </div>

                             <div>
                                <label className="block text-sm font-medium text-dark-300 mb-2">Email Address</label>
                                <div className="relative">
                                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-500" />
                                    <Input 
                                        type="email"
                                        value={formData.email} 
                                        onChange={e => setFormData({...formData, email: e.target.value})}
                                        className="pl-10"
                                        required
                                    />
                                </div>
                             </div>

                             <div className="pt-4 border-t border-dark-700">
                                <label className="block text-sm font-medium text-dark-300 mb-2">Role</label>
                                <div className="flex items-center gap-2 text-dark-400 bg-dark-800 p-3 rounded-lg border border-dark-700">
                                    <Shield className="w-5 h-5" />
                                    <span className="capitalize">{user.role}</span>
                                </div>
                                <p className="text-xs text-dark-500 mt-2">Role cannot be changed directly.</p>
                             </div>

                             <div className="flex justify-end pt-4">
                                <Button type="submit" disabled={loading}>
                                    {loading ? <Spinner size="sm" /> : 'Save Changes'}
                                </Button>
                             </div>
                        </form>
                    </Card>
                </div>
            </div>
        </div>
    );
}
