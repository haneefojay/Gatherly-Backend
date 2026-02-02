'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import api from '@/lib/api';
import { Event } from '@/lib/types';
import Button from '@/components/ui/Button';
import Spinner from '@/components/ui/Spinner';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import EventForm from '@/components/events/EventForm';

export default function EditEventPage() {
    const router = useRouter();
    const { id } = useParams();
    const { user } = useAuth();
    const [event, setEvent] = useState<Event | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        if (id) {
            fetchEvent();
        }
    }, [id]);

    const fetchEvent = async () => {
        try {
            const response = await api.get<Event>(`/events/${id}`);
            setEvent(response.data);
        } catch (err: any) {
            setError(err.message || err.response?.data?.message || 'Failed to load event');
        } finally {
            setLoading(false);
        }
    };

    const onSubmit = async (data: any) => {
        setSaving(true);
        setError('');

        try {
            await api.put(`/events/${id}`, data);
            router.push(`/events/${id}`);
        } catch (err: any) {
            setError(err.message || err.response?.data?.message || 'Failed to update event');
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <Spinner size="lg" />
            </div>
        );
    }

    if (!event) {
        return (
            <div className="min-h-screen flex items-center justify-center text-white">
                Event not found
            </div>
        );
    }

    // Check permissions
    const isOrganizer = user && (event.organizer_ids.includes(user.id) || user.role === 'admin');

    if (!isOrganizer) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-center">
                    <h1 className="text-xl font-bold text-white mb-2">Access Denied</h1>
                    <p className="text-dark-400 mb-4">You do not have permission to edit this event.</p>
                    <Link href={`/events/${id}`}>
                        <Button variant="secondary">Go Back</Button>
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-dark-900 py-12">
            <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
                <Link href={`/events/${id}`} className="inline-flex items-center text-dark-300 hover:text-white mb-8 transition-colors">
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Back to Event
                </Link>

                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-white mb-2">Edit Event</h1>
                    <p className="text-dark-400">Update the details of your event.</p>
                </div>

                {error && (
                    <div className="mb-6 p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400">
                        {error}
                    </div>
                )}

                <EventForm
                    initialValues={event}
                    onSubmit={onSubmit}
                    isLoading={saving}
                    submitLabel="Save Changes"
                />
            </div>
        </div>
    );
}
