'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import api from '@/lib/api';
import { Event, Attendee } from '@/lib/types';
import Button from '@/components/ui/Button';
import Spinner from '@/components/ui/Spinner';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import ConfirmationModal from '@/components/ui/ConfirmationModal';
import { ArrowLeft, User, Mail, Calendar, Search } from 'lucide-react';
import Link from 'next/link';
import Input from '@/components/ui/Input';
import { useAuth } from '@/contexts/AuthContext';
import { formatDateTime } from '@/lib/utils';

interface AttendeeUser {
    id: string;
    email: string;
    full_name: string;
}

interface AttendeeResponse {
    id: string;
    status: string;
    registered_at: string;
    user: AttendeeUser;
}

export default function AttendeesPage() {
    const router = useRouter();
    const { id } = useParams();
    const { user } = useAuth();
    const [loading, setLoading] = useState(true);
    const [attendees, setAttendees] = useState<AttendeeResponse[]>([]);
    const [waitlist, setWaitlist] = useState<AttendeeResponse[]>([]);
    const [activeTab, setActiveTab] = useState<'attendees' | 'waitlist'>('attendees');
    const [search, setSearch] = useState('');
    const [event, setEvent] = useState<Event | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Confirmation State
    const [showPromoteConfirm, setShowPromoteConfirm] = useState(false);
    const [userToPromote, setUserToPromote] = useState<{ id: string, name: string } | null>(null);
    const [isPromoting, setIsPromoting] = useState(false);

    useEffect(() => {
        if (id) {
            fetchData();
        }
    }, [id]);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [eventRes, attendeesRes, waitlistRes] = await Promise.all([
                api.get<Event>(`/events/${id}`),
                api.get<AttendeeResponse[]>(`/events/${id}/attendees`),
                api.get<AttendeeResponse[]>(`/events/${id}/waitlist`)
            ]);
            setEvent(eventRes.data);
            setAttendees(attendeesRes.data);
            setWaitlist(waitlistRes.data);
            setError(null);
        } catch (error: any) {
            console.error('Failed to fetch data', error);
            setError(error.response?.data?.detail || 'Failed to load attendee data');
        } finally {
            setLoading(false);
        }
    };

    const initiatePromoteUser = (userId: string, userName: string) => {
        setUserToPromote({ id: userId, name: userName });
        setShowPromoteConfirm(true);
        setError(null);
    };

    const handleConfirmPromote = async () => {
        if (!userToPromote) return;
        setIsPromoting(true);
        try {
            await api.post(`/events/${id}/organizers`, { user_id: userToPromote.id });
            setShowPromoteConfirm(false);
            setUserToPromote(null);
            fetchData();
        } catch (err: any) {
            console.error('Failed to promote user', err);
            const msg = err.response?.data?.detail || err.response?.data?.message || 'Failed to promote user';
            setError(Array.isArray(msg) ? msg[0].msg : msg);
            setShowPromoteConfirm(false);
        } finally {
            setIsPromoting(false);
        }
    };

    const filteredList = (activeTab === 'attendees' ? attendees : waitlist).filter(item =>
        item.user?.full_name.toLowerCase().includes(search.toLowerCase()) ||
        item.user?.email.toLowerCase().includes(search.toLowerCase())
    );

    if (loading) {
        return <div className="min-h-screen flex items-center justify-center"><Spinner size="lg" /></div>;
    }

    // Permission check
    const isOrganizer = user && (event?.organizer_ids.includes(user.id) || user.role === 'admin');

    if (!isOrganizer) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-center">
                    <h1 className="text-xl font-bold text-white mb-2">Access Denied</h1>
                    <p className="text-dark-400 mb-4">You do not have permission to view attendees for this event.</p>
                    <Link href={`/events/${id}`}>
                        <Button variant="secondary">Go Back</Button>
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-dark-900 py-12">
            <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between mb-8">
                    <Link href={`/events/${id}`} className="inline-flex items-center text-dark-300 hover:text-white transition-colors">
                        <ArrowLeft className="w-4 h-4 mr-2" />
                        Back to Event
                    </Link>
                </div>

                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-white mb-2">Manage Attendees</h1>
                    <p className="text-dark-400">
                        Manage registrations for <span className="text-primary-400 font-medium">{event?.title}</span>
                    </p>
                </div>

                {error && (
                    <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm font-medium">
                        Error: {error}
                    </div>
                )}

                <Card className="mb-8">
                    <div className="flex flex-col sm:flex-row gap-4 justify-between items-center mb-6">
                        <div className="flex gap-2 p-1 bg-dark-800 rounded-lg">
                            <button
                                onClick={() => setActiveTab('attendees')}
                                className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${activeTab === 'attendees'
                                    ? 'bg-primary-600 text-white shadow-lg'
                                    : 'text-dark-400 hover:text-white'
                                    }`}
                            >
                                Attendees ({attendees.length})
                            </button>
                            <button
                                onClick={() => setActiveTab('waitlist')}
                                className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${activeTab === 'waitlist'
                                    ? 'bg-primary-600 text-white shadow-lg'
                                    : 'text-dark-400 hover:text-white'
                                    }`}
                            >
                                Waitlist ({waitlist.length})
                            </button>
                        </div>

                        <div className="relative w-full sm:w-64">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-500" />
                            <input
                                type="text"
                                placeholder="Search attendees..."
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                                className="w-full pl-9 px-4 py-2 rounded-lg bg-dark-800 border border-dark-700 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
                            />
                        </div>
                    </div>

                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead>
                                <tr className="border-b border-dark-700 text-dark-400 text-sm uppercase">
                                    <th className="pb-3 pl-4">User</th>
                                    <th className="pb-3">Email</th>
                                    <th className="pb-3">Status</th>
                                    <th className="pb-3 text-right pr-4">Registered Date & Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-dark-700">
                                {filteredList.length === 0 ? (
                                    <tr>
                                        <td colSpan={4} className="py-8 text-center text-dark-400">
                                            No attendees found.
                                        </td>
                                    </tr>
                                ) : (
                                    filteredList.map((item) => {
                                        const isUserOrganizer = event?.organizer_ids.includes(item.user.id);
                                        return (
                                            <tr key={item.id} className="text-dark-200 hover:bg-dark-800/50 transition-colors">
                                                <td className="py-4 pl-4">
                                                    <div className="flex items-center gap-3">
                                                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center text-white font-bold text-xs">
                                                            {item.user?.full_name?.charAt(0).toUpperCase()}
                                                        </div>
                                                        <div>
                                                            <span className="font-medium text-white block">{item.user?.full_name}</span>
                                                            {isUserOrganizer && <span className="text-[10px] uppercase tracking-wider text-purple-400 font-bold bg-purple-500/10 px-1.5 py-0.5 rounded ml-[-1px]">Organizer</span>}
                                                        </div>
                                                    </div>
                                                </td>
                                                <td className="py-4 text-sm">{item.user?.email}</td>
                                                <td className="py-4">
                                                    <Badge variant={item.status === 'registered' ? 'success' : 'warning'} className="capitalize">
                                                        {item.status}
                                                    </Badge>
                                                </td>
                                                <td className="py-4 text-sm text-dark-400 text-right pr-4">
                                                    <div className="flex items-center justify-end gap-4">
                                                        <span>{new Date(item.registered_at).toLocaleDateString()}</span>

                                                        {!isUserOrganizer && item.status === 'registered' && (
                                                            <button
                                                                onClick={() => initiatePromoteUser(item.user.id, item.user.full_name)}
                                                                className="text-xs bg-dark-800 hover:bg-primary-600 hover:text-white text-primary-400 px-3 py-1.5 rounded-md border border-dark-600 hover:border-primary-500 transition-all font-medium"
                                                            >
                                                                + Organizer
                                                            </button>
                                                        )}
                                                    </div>
                                                </td>
                                            </tr>
                                        )
                                    })
                                )}
                            </tbody>
                        </table>
                    </div>
                </Card>

                <ConfirmationModal
                    isOpen={showPromoteConfirm}
                    onClose={() => setShowPromoteConfirm(false)}
                    onConfirm={handleConfirmPromote}
                    title="Promote User"
                    message={`Are you sure you want to promote ${userToPromote?.name} to be an organizer? They will have full management access to this event.`}
                    confirmLabel="Promote"
                    variant="info"
                    isLoading={isPromoting}
                />
            </div>
        </div>
    );
}
