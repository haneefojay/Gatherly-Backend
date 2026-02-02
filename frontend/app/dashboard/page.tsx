'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import api from '@/lib/api';
import { Event } from '@/lib/types';
import Card from '@/components/ui/Card';
import { Calendar, Users, CheckSquare, TrendingUp, ArrowRight, MapPin } from 'lucide-react';
import Link from 'next/link';
import Button from '@/components/ui/Button';
import Spinner from '@/components/ui/Spinner';
import { formatDateTime } from '@/lib/utils';
import Badge from '@/components/ui/Badge';

interface DashboardStats {
    upcoming_events_count: number;
    registered_events: number;
    organized_events: number;
    total_attendees: number;
    pending_tasks: number;
    total_users?: number;
    admin_events_upcoming?: number;
    admin_events_ongoing?: number;
    admin_events_completed?: number;
    admin_events_cancelled?: number;
    admin_events_draft?: number;
    admin_tasks_pending?: number;
    admin_tasks_completed?: number;
}

interface DashboardData {
    stats: DashboardStats;
    upcoming_events: Event[];
}

export default function DashboardPage() {
    const { user } = useAuth();
    const [loading, setLoading] = useState(true);
    const [data, setData] = useState<DashboardData | null>(null);

    useEffect(() => {
        const fetchDashboardData = async () => {
            try {
                const response = await api.get<DashboardData>('/dashboard');
                setData(response.data);
            } catch (error) {
                console.error('Failed to fetch dashboard data:', error);
            } finally {
                setLoading(false);
            }
        };

        if (user) {
            fetchDashboardData();
        }
    }, [user]);

    if (loading) {
        return (
            <div className="min-h-screen bg-dark-900 flex items-center justify-center">
                <Spinner size="lg" />
            </div>
        );
    }

    const isAdmin = user?.role === 'admin';
    const isOrganizer = user?.role === 'organizer' || isAdmin;

    const stats = [
        {
            label: isAdmin ? 'Total Upcoming Events' : 'My Upcoming Events',
            value: (isAdmin ? data?.stats.admin_events_upcoming : data?.stats.registered_events)?.toString() || '0',
            icon: Calendar,
            color: 'from-blue-500 to-cyan-500',
        },
        {
            label: 'Ongoing Events',
            value: data?.stats.admin_events_ongoing?.toString() || '0',
            icon: TrendingUp,
            color: 'from-emerald-500 to-green-500',
            visible: isAdmin
        },
        {
            label: 'Draft Events',
            value: data?.stats.admin_events_draft?.toString() || '0',
            icon: CheckSquare,
            color: 'from-gray-500 to-slate-500',
            visible: isAdmin
        },
        {
            label: 'Completed Events',
            value: data?.stats.admin_events_completed?.toString() || '0',
            icon: CheckSquare,
            color: 'from-purple-500 to-violet-500',
            visible: isAdmin
        },
        {
            label: 'Cancelled Events',
            value: data?.stats.admin_events_cancelled?.toString() || '0',
            icon: CheckSquare,
            color: 'from-red-500 to-rose-500',
            visible: isAdmin
        },
        {
            label: 'My Organized Events',
            value: data?.stats.organized_events.toString() || '0',
            icon: Users,
            color: 'from-purple-500 to-pink-500',
            visible: isOrganizer && !isAdmin // Hide for admin as they see everything
        },
        {
            label: isAdmin ? 'Total Pending Tasks' : 'My Pending Tasks',
            value: (isAdmin ? data?.stats.admin_tasks_pending : data?.stats.pending_tasks)?.toString() || '0',
            icon: CheckSquare,
            color: 'from-orange-500 to-amber-500',
            visible: isOrganizer
        },
        {
            label: 'Completed Tasks',
            value: data?.stats.admin_tasks_completed?.toString() || '0',
            icon: CheckSquare,
            color: 'from-teal-500 to-cyan-500',
            visible: isAdmin
        },
        {
            label: 'Total Attendees',
            value: data?.stats.total_attendees.toString() || '0',
            icon: TrendingUp,
            color: 'from-orange-500 to-red-500',
            visible: isOrganizer && !isAdmin // Admin sees specific breakdown or total users
        },
        {
            label: 'Total Users',
            value: data?.stats.total_users?.toString() || '0',
            icon: Users,
            color: 'from-pink-500 to-rose-500',
            visible: isAdmin
        }
    ].filter(stat => stat.visible !== false);

    return (
        <div className="min-h-screen bg-dark-900">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Welcome Section */}
                <div className="mb-8">
                    <h1 className="text-4xl font-bold text-white mb-2">
                        Welcome back, <span className="text-gradient">{user?.full_name}</span>! 👋
                    </h1>
                    <p className="text-dark-400 text-lg">
                        {user?.role === 'organizer' || user?.role === 'admin'
                            ? 'Manage your events and engage with your community'
                            : 'Discover and join amazing events'}
                    </p>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    {stats.map((stat) => (
                        <Card key={stat.label} className="relative overflow-hidden group" hover>
                            <div className={`absolute inset-0 bg-gradient-to-br ${stat.color} opacity-0 group-hover:opacity-10 transition-opacity`} />
                            <div className="relative">
                                <div className="flex items-center justify-between mb-4">
                                    <div className={`p-3 rounded-lg bg-gradient-to-br ${stat.color}`}>
                                        <stat.icon className="w-6 h-6 text-white" />
                                    </div>
                                </div>
                                <p className="text-3xl font-bold text-white mb-1">{stat.value}</p>
                                <p className="text-dark-400 text-sm">{stat.label}</p>
                            </div>
                        </Card>
                    ))}
                </div>

                {/* Quick Actions */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                    <Card>
                        <h2 className="text-xl font-bold text-white mb-4">Quick Actions</h2>
                        <div className="space-y-3">
                            <Link href="/events">
                                <Button variant="secondary" className="w-full justify-start">
                                    <Calendar className="w-4 h-4 mr-2" />
                                    Browse All Events
                                </Button>
                            </Link>
                            {(user?.role === 'organizer' || user?.role === 'admin') && (
                                <Link href="/events/create">
                                    <Button variant="primary" className="w-full justify-start">
                                        <CheckSquare className="w-4 h-4 mr-2" />
                                        Create New Event
                                    </Button>
                                </Link>
                            )}
                        </div>
                    </Card>

                    <Card>
                        <h2 className="text-xl font-bold text-white mb-4">Getting Started</h2>
                        <div className="space-y-3 text-dark-300">
                            {/* Getting started content remains same but just placeholder for now */}
                            <div className="flex items-start gap-3">
                                <div className="w-6 h-6 rounded-full bg-primary-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                                    <span className="text-primary-400 text-sm font-bold">1</span>
                                </div>
                                <div>
                                    <p className="text-dark-100 font-medium">Explore Events</p>
                                    <p className="text-sm text-dark-400">Browse upcoming events in your area</p>
                                </div>
                            </div>
                            <div className="flex items-start gap-3">
                                <div className="w-6 h-6 rounded-full bg-primary-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                                    <span className="text-primary-400 text-sm font-bold">2</span>
                                </div>
                                <div>
                                    <p className="text-dark-100 font-medium">Register</p>
                                    <p className="text-sm text-dark-400">Sign up for events that interest you</p>
                                </div>
                            </div>
                            <div className="flex items-start gap-3">
                                <div className="w-6 h-6 rounded-full bg-primary-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                                    <span className="text-primary-400 text-sm font-bold">3</span>
                                </div>
                                <div>
                                    <p className="text-dark-100 font-medium">Connect</p>
                                    <p className="text-sm text-dark-400">Meet people and build your network</p>
                                </div>
                            </div>
                        </div>
                    </Card>
                </div>

                {/* Upcoming Events Section */}
                <Card>
                    <div className="flex items-center justify-between mb-6">
                        <h2 className="text-xl font-bold text-white">Your Upcoming Events</h2>
                        <Link href="/events">
                            <Button variant="ghost" size="sm">
                                View All
                            </Button>
                        </Link>
                    </div>

                    {data?.upcoming_events && data.upcoming_events.length > 0 ? (
                        <div className="space-y-4">
                            {data.upcoming_events.map(event => (
                                <div key={event.id} className="flex items-center justify-between p-4 bg-dark-800 rounded-lg border border-dark-700 hover:border-dark-600 transition-colors">
                                    <div className="flex items-center gap-4">
                                        <div className="flex flex-col items-center justify-center w-12 h-12 bg-dark-700 rounded-lg text-dark-300">
                                            <span className="text-xs font-bold uppercase">{new Date(event.start_date).toLocaleString('default', { month: 'short' })}</span>
                                            <span className="text-lg font-bold text-white">{new Date(event.start_date).getDate()}</span>
                                        </div>
                                        <div>
                                            <h3 className="font-medium text-white mb-1">{event.title}</h3>
                                            <div className="flex items-center gap-4 text-sm text-dark-400">
                                                <div className="flex items-center gap-1">
                                                    <Calendar className="w-3 h-3" />
                                                    {formatDateTime(event.start_date)}
                                                </div>
                                                {event.location && (
                                                    <div className="flex items-center gap-1">
                                                        <MapPin className="w-3 h-3" />
                                                        {event.location}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                    <Link href={`/events/${event.id}`}>
                                        <Button variant="secondary" size="sm">
                                            View Details
                                            <ArrowRight className="w-3 h-3 ml-2" />
                                        </Button>
                                    </Link>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-12">
                            <Calendar className="w-16 h-16 text-dark-600 mx-auto mb-4" />
                            <p className="text-dark-400 mb-4">You are not registered for any upcoming events.</p>
                            <Link href="/events">
                                <Button variant="primary">Explore Events</Button>
                            </Link>
                        </div>
                    )}
                </Card>
            </div>
        </div>
    );
}
