'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { TaskCreateRequest, User } from '@/lib/types';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';

const taskSchema = z.object({
    title: z.string().min(1, 'Title is required'),
    description: z.string().optional(),
    assignee_id: z.string().optional(),
});

type TaskFormData = z.infer<typeof taskSchema>;

interface TaskFormProps {
    assignees: User[];
    onSubmit: (data: TaskCreateRequest) => Promise<void>;
    isLoading: boolean;
    initialValues?: Partial<TaskFormData>;
    submitLabel?: string;
}

export default function TaskForm({ assignees, onSubmit, isLoading, initialValues, submitLabel = 'Create Task' }: TaskFormProps) {
    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<TaskFormData>({
        resolver: zodResolver(taskSchema),
        defaultValues: {
            title: initialValues?.title || '',
            description: initialValues?.description || '',
            assignee_id: initialValues?.assignee_id || '',
        },
    });

    const onFormSubmit = async (data: TaskFormData) => {
        // If assignee_id is empty string, make it undefined
        const cleanData = {
            ...data,
            assignee_id: data.assignee_id === '' ? undefined : data.assignee_id
        };
        await onSubmit(cleanData);
    };

    return (
        <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-6">
            <Input
                label="Task Title"
                placeholder="e.g. Set up projector"
                error={errors.title?.message}
                {...register('title')}
            />

            <div className="space-y-1.5">
                <label className="block text-sm font-medium text-dark-200">Description</label>
                <textarea
                    className="w-full px-4 py-3 rounded-lg bg-dark-900/50 border border-dark-700 text-dark-100 placeholder:text-dark-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all min-h-[100px]"
                    placeholder="Details about the task..."
                    {...register('description')}
                />
            </div>

            <div className="space-y-1.5">
                <label className="block text-sm font-medium text-dark-200">Assign To (Organizers Only)</label>
                <select
                    className="w-full px-4 py-2.5 rounded-lg bg-dark-900/50 border border-dark-700 text-dark-100 placeholder:text-dark-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                    {...register('assignee_id')}
                >
                    <option value="">Unassigned</option>
                    {assignees.map((user) => (
                        <option key={user.id} value={user.id}>
                            {user.full_name} ({user.email})
                        </option>
                    ))}
                </select>
                <p className="text-xs text-dark-500 mt-1">
                    Only event organizers can be assigned tasks. Add organizers in Event Details page.
                </p>
            </div>

            <div className="flex justify-end pt-2">
                <Button type="submit" isLoading={isLoading}>
                    {submitLabel}
                </Button>
            </div>
        </form>
    );
}
