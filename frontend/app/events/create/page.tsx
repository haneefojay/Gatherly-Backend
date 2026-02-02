'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import { EventCreateRequest } from '@/lib/types';
import Button from '@/components/ui/Button';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import EventForm from '@/components/events/EventForm';

export default function CreateEventPage() {
    const router = useRouter();
    const { user } = useAuth();
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    const onSubmit = async (data: any) => {
        setIsLoading(true);
        setError('');

        try {
            await api.post<EventCreateRequest>('/events', data);
            router.push('/events');
        } catch (err: any) {
            setError(err.message || err.response?.data?.detail || 'Failed to create event');
        } finally {
            setIsLoading(false);
        }
    };

    if (!user || (user.role !== 'organizer' && user.role !== 'admin')) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-center">
                    <h1 className="text-xl font-bold text-white mb-2">Access Denied</h1>
                    <p className="text-dark-400 mb-4">You need to be an organizer to look at this page.</p>
                    <Link href="/dashboard">
                        <Button variant="secondary">Go Home</Button>
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-dark-900 py-12">
            <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
                <Link href="/events" className="inline-flex items-center text-dark-300 hover:text-white mb-8 transition-colors">
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Back to Events
                </Link>

                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-white mb-2">Create New Event</h1>
                    <p className="text-dark-400">Fill in the details to host your next amazing gathering.</p>
                </div>

                {error && (
                    <div className="mb-6 p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400">
                        {error}
                    </div>
                )}

                <EventForm onSubmit={onSubmit} isLoading={isLoading} submitLabel="Create Event" />
            </div>
        </div>
    );
}
