'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import api from '@/lib/api';
import { Event, Attendee } from '@/lib/types';
import { useAuth } from '@/contexts/AuthContext';
import Spinner from '@/components/ui/Spinner';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import { formatDateTime } from '@/lib/utils';
import RegistrationButton from '@/components/attendees/RegistrationButton';
import Button from '@/components/ui/Button';
import { Calendar, MapPin, Users, ArrowLeft, Clock, Shield } from 'lucide-react';
import Link from 'next/link';

export default function EventDetailsPage() {
    const { id } = useParams();
    const router = useRouter();
    const { user } = useAuth();
    const [event, setEvent] = useState<Event | null>(null);
    const [attendee, setAttendee] = useState<Attendee | undefined>(undefined);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    const fetchEventDetails = async () => {
        try {
            // Fetch event data
            const eventRes = await api.get<Event>(`/events/${id}`);
            setEvent(eventRes.data);

            // Check registration status if logged in
            // Check registration status if logged in
            if (user) {
                try {
                    const statusRes = await api.get<Attendee>(`/events/${id}/my-status`);
                    setAttendee(statusRes.data || undefined);
                } catch (e) {
                    // Ignore errors, assume not registered
                    console.log('Failed to fetch validation status', e);
                    setAttendee(undefined);
                }
            }
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to load event');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (id) {
            fetchEventDetails();
        }
    }, [id, user]);

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <Spinner size="lg" />
            </div>
        );
    }

    if (error || !event) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center p-4 text-center">
                <h1 className="text-2xl font-bold text-white mb-2">Event not found</h1>
                <p className="text-dark-400 mb-6">{error || "The event you're looking for doesn't exist."}</p>
                <Link href="/events" className="text-primary-400 hover:text-primary-300 flex items-center gap-2">
                    <ArrowLeft className="w-4 h-4" />
                    Back to Events
                </Link>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-dark-900 pb-20">
            {/* Hero Section */}
            <div className="relative h-64 md:h-80 w-full overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-primary-900/50 to-dark-900 bg-cover bg-center" />
                <div className="absolute inset-0 bg-gradient-to-t from-dark-900 to-transparent" />

                <div className="absolute bottom-0 left-0 right-0 p-4 sm:p-8 max-w-7xl mx-auto">
                    <Link href="/events" className="inline-flex items-center text-dark-300 hover:text-white mb-6 transition-colors">
                        <ArrowLeft className="w-4 h-4 mr-2" />
                        Back to Events
                    </Link>

                    <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                        <div>
                            <div className="flex items-center gap-3 mb-3">
                                <Badge variant="status" status={event.status} className="text-sm px-3 py-1">
                                    {event.status}
                                </Badge>
                                {event.organizer_ids.includes(user?.id || '') && (
                                    <Badge variant="default" className="bg-purple-500/20 text-purple-300 border-purple-500/30">
                                        Organizer
                                    </Badge>
                                )}
                            </div>
                            <h1 className="text-3xl md:text-5xl font-bold text-white mb-4 leading-tight">
                                {event.title}
                            </h1>
                            <div className="flex flex-wrap items-center gap-4 text-dark-200">
                                <div className="flex items-center gap-2">
                                    <Calendar className="w-5 h-5 text-primary-400" />
                                    <span>{formatDateTime(event.start_date)}</span>
                                </div>
                                {event.location && (
                                    <div className="flex items-center gap-2">
                                        <MapPin className="w-5 h-5 text-accent-400" />
                                        <span>{event.location}</span>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Registration Card (Mobile: Bottom, Desktop: Right) */}
                        <div className="hidden md:block">
                            <RegistrationButton event={event} attendee={attendee} onUpdate={fetchEventDetails} />
                        </div>
                    </div>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Main Content */}
                    <div className="lg:col-span-2 space-y-8">
                        <Card>
                            <h2 className="text-xl font-bold text-white mb-4">About the Event</h2>
                            <div className="prose prose-invert max-w-none text-dark-300">
                                <p className="whitespace-pre-wrap">{event.description || 'No description provided.'}</p>
                            </div>
                        </Card>

                        <Card>
                            <h2 className="text-xl font-bold text-white mb-4">Schedule</h2>
                            <div className="space-y-4">
                                <div className="flex items-start gap-4">
                                    <div className="p-3 rounded-lg bg-dark-700/50 text-primary-400">
                                        <Clock className="w-6 h-6" />
                                    </div>
                                    <div>
                                        <h3 className="font-medium text-white">Start Time</h3>
                                        <p className="text-dark-400">{formatDateTime(event.start_date)}</p>
                                    </div>
                                </div>
                                <div className="flex items-start gap-4">
                                    <div className="p-3 rounded-lg bg-dark-700/50 text-accent-400">
                                        <Clock className="w-6 h-6" />
                                    </div>
                                    <div>
                                        <h3 className="font-medium text-white">End Time</h3>
                                        <p className="text-dark-400">{formatDateTime(event.end_date)}</p>
                                    </div>
                                </div>
                            </div>
                        </Card>
                    </div>

                    {/* Sidebar */}
                    <div className="space-y-6">
                        {/* Organizer Actions */}
                        {(user?.role === 'admin' || (event.organizer_ids && event.organizer_ids.includes(user?.id || ''))) && (
                            <Card className="border-purple-500/30 bg-purple-500/5">
                                <h2 className="text-lg font-bold text-white mb-3">Organizer Tools</h2>
                                <div className="grid grid-cols-1 gap-3">
                                    <Link href={`/events/${id}/edit`}>
                                        <Button variant="secondary" className="w-full">
                                            Edit Event Details
                                        </Button>
                                    </Link>
                                    <Link href={`/events/${id}/attendees`}>
                                        <Button variant="secondary" className="w-full">
                                            Manage Attendees
                                        </Button>
                                    </Link>
                                    <Link href={`/events/${id}/tasks`}>
                                        <Button variant="secondary" className="w-full">
                                            Manage Tasks
                                        </Button>
                                    </Link>
                                    <Link href={`/events/${id}/team`}>
                                        <Button variant="secondary" className="w-full">
                                            Manage Team
                                        </Button>
                                    </Link>
                                </div>
                            </Card>
                        )}
                        <Card>
                            <h2 className="text-xl font-bold text-white mb-4">Event Stats</h2>
                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2 text-dark-300">
                                        <Users className="w-5 h-5" />
                                        <span>Attendees</span>
                                    </div>
                                    <span className="font-medium text-white">
                                        {event.current_attendees} / {event.capacity}
                                    </span>
                                </div>

                                {/* Visual Capacity Bar */}
                                <div className="w-full bg-dark-700 rounded-full h-2 overflow-hidden">
                                    <div
                                        className="bg-gradient-primary h-full rounded-full transition-all duration-500"
                                        style={{ width: `${Math.min((event.current_attendees / event.capacity) * 100, 100)}%` }}
                                    />
                                </div>

                                <div className="pt-4 border-t border-dark-700">
                                    <div className="flex items-start gap-3 text-sm text-dark-400">
                                        <Shield className="w-4 h-4 mt-0.5" />
                                        <p>This event is moderated by the organizers.</p>
                                    </div>
                                </div>
                            </div>
                        </Card>

                        {/* Mobile Registration Button (fixed bottom or inline) */}
                        <div className="md:hidden">
                            <RegistrationButton event={event} attendee={attendee} onUpdate={fetchEventDetails} />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
