'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter, useParams } from 'next/navigation';
import api from '@/lib/api';
import { Event, User } from '@/lib/types';
import Button from '@/components/ui/Button';
import Spinner from '@/components/ui/Spinner';
import Card from '@/components/ui/Card';
import Modal from '@/components/ui/Modal';
import ConfirmationModal from '@/components/ui/ConfirmationModal';
import { ArrowLeft, UserPlus, Trash2, Shield, Mail, ChevronDown } from 'lucide-react';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';

const addOrganizerSchema = z.object({
    email: z.string().email('Invalid email address'),
});

type AddOrganizerData = z.infer<typeof addOrganizerSchema>;

export default function TeamPage() {
    const router = useRouter();
    const { id } = useParams();
    const { user } = useAuth();

    const [loading, setLoading] = useState(true);
    const [event, setEvent] = useState<Event | null>(null);
    const [isAddModalOpen, setIsAddModalOpen] = useState(false);
    const [potentialOrganizers, setPotentialOrganizers] = useState<User[]>([]);

    // Error state
    const [pageError, setPageError] = useState<string | null>(null);
    const [modalError, setModalError] = useState<string | null>(null);

    // Confirmation Modal State
    const [showConfirmRemove, setShowConfirmRemove] = useState(false);
    const [organizerToRemove, setOrganizerToRemove] = useState<string | null>(null);
    const [isRemoving, setIsRemoving] = useState(false);

    // Combobox state
    const [isComboboxOpen, setIsComboboxOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    const { register, handleSubmit, reset, setValue, watch, formState: { errors, isSubmitting } } = useForm<AddOrganizerData>({
        resolver: zodResolver(addOrganizerSchema)
    });

    const emailValue = watch('email');

    useEffect(() => {
        if (id) {
            fetchData();
        }
    }, [id]);

    useEffect(() => {
        if (isAddModalOpen) {
            fetchPotentialOrganizers();
            setModalError(null);
        }
    }, [isAddModalOpen]);

    // Close dropdown when clicking outside
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsComboboxOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);
            const { data } = await api.get<Event>(`/events/${id}`);
            setEvent(data);
            setPageError(null);
        } catch (error: any) {
            console.error('Failed to fetch event data', error);
            const msg = error.response?.data?.detail || 'Failed to load event data';
            setPageError(msg);
        } finally {
            setLoading(false);
        }
    };

    const fetchPotentialOrganizers = async () => {
        try {
            const { data } = await api.get<User[]>('/users?role=organizer');
            const currentIds = event?.organizers?.map(o => o.id) || [];
            const available = data.filter(u => !currentIds.includes(u.id));
            setPotentialOrganizers(available);
        } catch (error) {
            console.error('Failed to fetch potential organizers', error);
        }
    };

    const handleAddOrganizer = async (data: AddOrganizerData) => {
        setModalError(null);
        try {
            await api.post(`/events/${id}/organizers`, { email: data.email });
            setIsAddModalOpen(false);
            reset();
            fetchData();
        } catch (error: any) {
            console.error('Failed to add organizer', error);
            const msg = error.response?.data?.detail || error.response?.data?.message || 'Failed to add organizer';
            setModalError(Array.isArray(msg) ? msg[0].msg : msg);
        }
    };

    const initiateRemoveOrganizer = (organizerId: string) => {
        setOrganizerToRemove(organizerId);
        setShowConfirmRemove(true);
        setPageError(null);
    };

    const handleConfirmRemove = async () => {
        if (!organizerToRemove) return;
        setIsRemoving(true);
        try {
            await api.delete(`/events/${id}/organizers/${organizerToRemove}`);
            setShowConfirmRemove(false);
            setOrganizerToRemove(null);
            fetchData();
        } catch (error: any) {
            console.error('Failed to remove organizer', error);
            const msg = error.response?.data?.detail || error.response?.data?.message || 'Failed to remove organizer';
            setPageError(msg);
            setShowConfirmRemove(false); // Close modal even on error to show page error
        } finally {
            setIsRemoving(false);
        }
    };

    // Filter potential organizers based on input
    const filteredOptions = potentialOrganizers.filter(u =>
        !emailValue ||
        u.email.toLowerCase().includes(emailValue.toLowerCase()) ||
        u.full_name.toLowerCase().includes(emailValue.toLowerCase())
    );

    if (loading) return <div className="min-h-screen flex items-center justify-center"><Spinner size="lg" /></div>;

    const isOrganizer = user && event && (event.organizer_ids.includes(user.id) || user.role === 'admin');

    if (!isOrganizer) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-center">
                    <h1 className="text-xl font-bold text-white mb-2">Access Denied</h1>
                    <p className="text-dark-400 mb-4">Only organizers can manage the team.</p>
                    <Link href={`/events/${id}`}>
                        <Button variant="secondary">Go Back</Button>
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-dark-900 py-12">
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
                <Link href={`/events/${id}`} className="inline-flex items-center text-dark-300 hover:text-white mb-8 transition-colors">
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Back to Event
                </Link>

                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-3xl font-bold text-white mb-2">Manage Team</h1>
                        <p className="text-dark-400">Organizers for <span className="text-primary-400">{event?.title}</span></p>
                    </div>
                    <Button onClick={() => setIsAddModalOpen(true)}>
                        <UserPlus className="w-4 h-4 mr-2" />
                        Add Organizer
                    </Button>
                </div>

                {pageError && (
                    <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm flex items-center gap-2">
                        <span className="font-bold">Error:</span> {pageError}
                    </div>
                )}

                <div className="space-y-4">
                    {event?.organizers?.map(organizer => (
                        <Card key={organizer.id} className="flex items-center justify-between p-4">
                            <div className="flex items-center gap-4">
                                <div className="w-10 h-10 rounded-full bg-dark-800 flex items-center justify-center text-primary-400">
                                    <Shield className="w-5 h-5" />
                                </div>
                                <div>
                                    <h3 className="text-white font-medium">{organizer.full_name}</h3>
                                    <p className="text-dark-400 text-sm flex items-center gap-1">
                                        <Mail className="w-3 h-3" />
                                        {organizer.email}
                                    </p>
                                </div>
                            </div>

                            {organizer.id === event.created_by_id ? (
                                <span className="text-xs font-medium text-primary-400 bg-primary-500/10 px-2 py-1 rounded">
                                    Owner
                                </span>
                            ) : (
                                <button
                                    onClick={() => initiateRemoveOrganizer(organizer.id)}
                                    className="p-2 text-dark-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                                    title="Remove Organizer"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            )}
                        </Card>
                    ))}
                </div>

                <Modal
                    isOpen={isAddModalOpen}
                    onClose={() => setIsAddModalOpen(false)}
                    title="Add Organizer"
                >
                    {modalError && (
                        <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
                            {modalError}
                        </div>
                    )}

                    <form onSubmit={handleSubmit(handleAddOrganizer)} className="space-y-6">
                        <p className="text-sm text-dark-300">
                            Select an organizer or type their email address below.
                        </p>

                        <div className="space-y-1.5 relative" ref={dropdownRef}>
                            <label className="block text-sm font-medium text-dark-200">Email Address</label>
                            <div className="relative">
                                <input
                                    type="text"
                                    className="w-full pl-4 pr-10 py-2.5 rounded-lg bg-dark-900/50 border border-dark-700 text-dark-100 placeholder:text-dark-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                                    placeholder="Start typing name or email..."
                                    autoComplete="off"
                                    {...register('email')}
                                    onFocus={() => setIsComboboxOpen(true)}
                                    onClick={() => setIsComboboxOpen(true)}
                                />
                                <button
                                    type="button"
                                    onClick={() => setIsComboboxOpen(!isComboboxOpen)}
                                    className="absolute right-0 top-0 h-full px-3 text-dark-400 hover:text-white"
                                >
                                    <ChevronDown className="w-4 h-4" />
                                </button>
                            </div>

                            {/* Custom Dropdown List */}
                            {isComboboxOpen && (
                                <div className="absolute z-10 w-full mt-1 bg-dark-800 border border-dark-700 rounded-lg shadow-xl max-h-60 overflow-y-auto animate-in fade-in zoom-in-95 duration-100">
                                    {filteredOptions.length > 0 ? (
                                        <ul className="py-1">
                                            {filteredOptions.map((u) => (
                                                <li
                                                    key={u.id}
                                                    onClick={() => {
                                                        setValue('email', u.email);
                                                        setIsComboboxOpen(false);
                                                    }}
                                                    className="px-4 py-3 hover:bg-dark-700 cursor-pointer flex flex-col gap-0.5 border-b border-dark-700/50 last:border-0"
                                                >
                                                    <span className="text-white font-medium text-sm">{u.full_name}</span>
                                                    <span className="text-dark-400 text-xs">{u.email}</span>
                                                </li>
                                            ))}
                                        </ul>
                                    ) : (
                                        <div className="p-4 text-center text-dark-400 text-sm">
                                            {potentialOrganizers.length === 0 ? "No other organizers found." : "No matches found."}
                                            <br />
                                            <span className="text-xs opacity-70">You can still type any valid email.</span>
                                        </div>
                                    )}
                                </div>
                            )}

                            {errors.email && <p className="text-red-400 text-xs mt-1">{errors.email.message}</p>}
                        </div>

                        <div className="flex justify-end pt-2">
                            <Button type="submit" isLoading={isSubmitting}>
                                Add Organizer
                            </Button>
                        </div>
                    </form>
                </Modal>

                <ConfirmationModal
                    isOpen={showConfirmRemove}
                    onClose={() => setShowConfirmRemove(false)}
                    onConfirm={handleConfirmRemove}
                    title="Remove Organizer"
                    message="Are you sure you want to remove this organizer? They will likely lose access to managing this event."
                    confirmLabel="Remove"
                    isLoading={isRemoving}
                />
            </div>
        </div>
    );
}
