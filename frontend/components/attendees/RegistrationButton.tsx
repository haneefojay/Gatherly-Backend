'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Event, Attendee } from '@/lib/types';
import { useAuth } from '@/contexts/AuthContext';
import api from '@/lib/api';
import Button from '@/components/ui/Button';
import Badge from '@/components/ui/Badge';
import { UserCheck, UserPlus, AlertCircle } from 'lucide-react';

interface RegistrationButtonProps {
    event: Event;
    attendee?: Attendee;
    onUpdate: () => void;
}

export default function RegistrationButton({ event, attendee, onUpdate }: RegistrationButtonProps) {
    const [loading, setLoading] = useState(false);
    const { user, isAuthenticated } = useAuth();
    const router = useRouter();

    const isFull = event.current_attendees >= event.capacity;
    const isRegistered = attendee?.status === 'registered';
    const isWaitlisted = attendee?.status === 'waitlisted';

    // Check if user is an organizer (for badge display only)
    const isOrganizer = user && (event.organizer_ids.includes(user.id) || user.role === 'admin');

    const handleAction = async (action: 'register' | 'unregister') => {
        if (!isAuthenticated) {
            router.push(`/login?redirect=/events/${event.id}`);
            return;
        }

        setLoading(true);
        try {
            if (action === 'unregister') {
                if (!confirm('Are you sure you want to cancel your registration?')) {
                    setLoading(false);
                    return;
                }
                await api.delete(`/events/${event.id}/unregister`);
            } else {
                await api.post(`/events/${event.id}/register`);
            }
            onUpdate();
        } catch (error: any) {
            console.error(error);
            alert(error.response?.data?.detail || 'Action failed');
        } finally {
            setLoading(false);
        }
    };

    const OrganizerBadge = isOrganizer ? (
        <div className="flex items-center gap-2 text-primary-400 bg-primary-500/10 px-4 py-2 rounded-lg border border-primary-500/20 mb-4 w-fit">
            <UserCheck className="w-5 h-5" />
            <span className="font-medium">You are organizing this event</span>
        </div>
    ) : null;

    if (event.status !== 'upcoming') {
        return (
            <div className="flex flex-col items-start gap-4">
                {OrganizerBadge}
                <Button disabled variant="secondary" className="w-full sm:w-auto">
                    Event is {event.status}
                </Button>
            </div>
        );
    }

    if (isRegistered) {
        return (
            <div className="flex flex-col items-start gap-4">
                {OrganizerBadge}
                <div className="flex flex-wrap items-center gap-4">
                    <Badge className="bg-green-500/20 text-green-400 border-green-500/30 text-sm px-3 py-1">
                        <UserCheck className="w-4 h-4 mr-2" />
                        Registered
                    </Badge>
                    <Button
                        variant="secondary"
                        className="text-red-400 border-red-500/30 hover:bg-red-500/10"
                        onClick={() => handleAction('unregister')}
                        isLoading={loading}
                    >
                        Cancel Registration
                    </Button>
                </div>
            </div>
        );
    }

    if (isWaitlisted) {
        return (
            <div className="flex flex-col items-start gap-4">
                {OrganizerBadge}
                <div className="flex flex-wrap items-center gap-4">
                    <Badge className="bg-yellow-500/20 text-yellow-400 border-yellow-500/30 text-sm px-3 py-1">
                        <AlertCircle className="w-4 h-4 mr-2" />
                        You are on the Waitlist
                    </Badge>
                    <Button
                        variant="secondary"
                        className="text-red-400 border-red-500/30 hover:bg-red-500/10"
                        onClick={() => handleAction('unregister')}
                        isLoading={loading}
                    >
                        Leave Waitlist
                    </Button>
                </div>
            </div>
        );
    }

    return (
        <div className="flex flex-col items-start gap-4">
            {OrganizerBadge}
            <Button
                variant={isFull ? 'secondary' : 'primary'}
                className="w-full sm:w-auto"
                onClick={() => handleAction('register')}
                isLoading={loading}
            >
                <UserPlus className="w-4 h-4 mr-2" />
                {isFull ? 'Join Waitlist' : 'Register Now'}
            </Button>
        </div>
    );
}
