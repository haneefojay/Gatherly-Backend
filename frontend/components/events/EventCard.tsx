import Link from 'next/link';
import { Event } from '@/lib/types';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import { formatDateTime } from '@/lib/utils';
import { Calendar, MapPin, Users } from 'lucide-react';

interface EventCardProps {
    event: Event;
}

export default function EventCard({ event }: EventCardProps) {
    const availableSpots = event.capacity - event.current_attendees;
    const capacityPercentage = (event.current_attendees / event.capacity) * 100;

    return (
        <Link href={`/events/${event.id}`}>
            <Card hover className="h-full">
                <div className="flex flex-col h-full">
                    {/* Header */}
                    <div className="flex items-start justify-between mb-3">
                        <h3 className="text-lg font-bold text-white line-clamp-2 flex-1">{event.title}</h3>
                        <Badge variant="status" status={event.status} className="ml-2 flex-shrink-0">
                            {event.status}
                        </Badge>
                    </div>

                    {/* Description */}
                    {event.description && (
                        <p className="text-dark-400 text-sm mb-4 line-clamp-2">{event.description}</p>
                    )}

                    {/* Details */}
                    <div className="space-y-2 mb-4">
                        <div className="flex items-center gap-2 text-dark-300 text-sm">
                            <Calendar className="w-4 h-4 text-primary-400" />
                            <span>{formatDateTime(event.start_date)}</span>
                        </div>
                        {event.location && (
                            <div className="flex items-center gap-2 text-dark-300 text-sm">
                                <MapPin className="w-4 h-4 text-accent-400" />
                                <span className="line-clamp-1">{event.location}</span>
                            </div>
                        )}
                        <div className="flex items-center gap-2 text-dark-300 text-sm">
                            <Users className="w-4 h-4 text-green-400" />
                            <span>
                                {event.current_attendees} / {event.capacity} attendees
                            </span>
                        </div>
                    </div>

                    {/* Capacity Bar */}
                    <div className="mt-auto">
                        <div className="flex items-center justify-between text-xs text-dark-400 mb-1">
                            <span>Capacity</span>
                            <span>{Math.round(capacityPercentage)}%</span>
                        </div>
                        <div className="w-full bg-dark-800 rounded-full h-2 overflow-hidden">
                            <div
                                className={`h-full rounded-full transition-all ${capacityPercentage >= 100
                                        ? 'bg-red-500'
                                        : capacityPercentage >= 80
                                            ? 'bg-yellow-500'
                                            : 'bg-gradient-primary'
                                    }`}
                                style={{ width: `${Math.min(capacityPercentage, 100)}%` }}
                            />
                        </div>
                        {availableSpots > 0 && availableSpots <= 10 && (
                            <p className="text-xs text-yellow-400 mt-1">Only {availableSpots} spots left!</p>
                        )}
                        {availableSpots === 0 && (
                            <p className="text-xs text-red-400 mt-1">Event is full</p>
                        )}
                    </div>
                </div>
            </Card>
        </Link>
    );
}
