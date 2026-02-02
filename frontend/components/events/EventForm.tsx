'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Event } from '@/lib/types';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Card from '@/components/ui/Card';
import { MapPin, Users } from 'lucide-react';
import Link from 'next/link';

const eventSchema = z.object({
    title: z.string().min(3, 'Title must be at least 3 characters'),
    description: z.string().optional(),
    start_date: z.string().min(1, 'Start date is required'),
    end_date: z.string().min(1, 'End date is required'),
    location: z.string().min(1, 'Location is required'),
    capacity: z.preprocess((val) => Number(val), z.number().min(1, 'Capacity must be at least 1')),
});

type EventFormData = z.infer<typeof eventSchema>;

interface EventFormProps {
    initialValues?: Partial<Event>;
    onSubmit: (data: EventFormData) => Promise<void>;
    isLoading: boolean;
    submitLabel: string;
}

export default function EventForm({ initialValues, onSubmit, isLoading, submitLabel }: EventFormProps) {
    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<EventFormData>({
        resolver: zodResolver(eventSchema),
        defaultValues: {
            title: initialValues?.title || '',
            description: initialValues?.description || '',
            start_date: initialValues?.start_date ? new Date(initialValues.start_date).toISOString().slice(0, 16) : '',
            end_date: initialValues?.end_date ? new Date(initialValues.end_date).toISOString().slice(0, 16) : '',
            location: initialValues?.location || '',
            capacity: initialValues?.capacity || 100,
        },
    });

    const handleFormSubmit = async (data: EventFormData) => {
        // Validate dates again just in case
        if (new Date(data.end_date) <= new Date(data.start_date)) {
            alert('End date must be after start date');
            return;
        }
        await onSubmit(data);
    };

    return (
        <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
            <Card>
                <div className="space-y-6">
                    <Input
                        label="Event Title"
                        placeholder="e.g. Annual Tech Conference 2024"
                        error={errors.title?.message}
                        {...register('title')}
                    />

                    <div className="space-y-1.5">
                        <label className="block text-sm font-medium text-dark-200">Description</label>
                        <textarea
                            className="w-full px-4 py-3 rounded-lg bg-dark-800/50 border border-dark-700 text-dark-100 placeholder:text-dark-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all min-h-[120px]"
                            placeholder="Tell people what your event is about..."
                            {...register('description')}
                        />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <Input
                            label="Start Date & Time"
                            type="datetime-local"
                            error={errors.start_date?.message}
                            {...register('start_date')}
                        />
                        <Input
                            label="End Date & Time"
                            type="datetime-local"
                            error={errors.end_date?.message}
                            {...register('end_date')}
                        />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <label className="block text-sm font-medium text-dark-200 mb-1.5">
                                Location
                            </label>
                            <div className="relative">
                                <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-500" />
                                <input
                                    type="text"
                                    className="w-full pl-10 px-4 py-2.5 rounded-lg bg-dark-800/50 border border-dark-700 text-dark-100 placeholder:text-dark-500 focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all"
                                    placeholder="e.g. San Francisco Center"
                                    {...register('location')}
                                />
                            </div>
                            {errors.location && <p className="mt-1.5 text-sm text-red-400">{errors.location.message}</p>}
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-dark-200 mb-1.5">
                                Capacity
                            </label>
                            <div className="relative">
                                <Users className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-500" />
                                <input
                                    type="number"
                                    className="w-full pl-10 px-4 py-2.5 rounded-lg bg-dark-800/50 border border-dark-700 text-dark-100 placeholder:text-dark-500 focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all"
                                    placeholder="e.g. 100"
                                    {...register('capacity')}
                                />
                            </div>
                            {errors.capacity && <p className="mt-1.5 text-sm text-red-400">{errors.capacity.message}</p>}
                        </div>
                    </div>

                </div>
            </Card>

            <div className="flex items-center justify-end gap-4">
                <Link href="/events">
                    <Button type="button" variant="ghost">Cancel</Button>
                </Link>
                <Button type="submit" isLoading={isLoading} size="lg">
                    {submitLabel}
                </Button>
            </div>
        </form>
    );
}
