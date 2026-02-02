'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import api from '@/lib/api';
import { Event, Task, TaskCreateRequest } from '@/lib/types';
import Button from '@/components/ui/Button';
import Spinner from '@/components/ui/Spinner';
import Card from '@/components/ui/Card';
import Modal from '@/components/ui/Modal';
import Badge from '@/components/ui/Badge';
import ConfirmationModal from '@/components/ui/ConfirmationModal';
import { ArrowLeft, CheckCircle2, Circle, Trash2, Plus, Edit2 } from 'lucide-react';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import TaskForm from '@/components/tasks/TaskForm';

export default function TasksPage() {
    const router = useRouter();
    const { id } = useParams();
    const { user } = useAuth();

    const [loading, setLoading] = useState(true);
    const [event, setEvent] = useState<Event | null>(null);
    const [tasks, setTasks] = useState<Task[]>([]);

    // Error states
    const [pageError, setPageError] = useState<string | null>(null);
    const [modalError, setModalError] = useState<string | null>(null);

    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [creating, setCreating] = useState(false);

    // Edit state
    const [editingTask, setEditingTask] = useState<Task | null>(null);
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [updating, setUpdating] = useState(false);

    // Confirmation State
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
    const [taskToDelete, setTaskToDelete] = useState<string | null>(null);
    const [isDeleting, setIsDeleting] = useState(false);

    // Filter state
    const [activeFilter, setActiveFilter] = useState<'all' | 'mine'>('all');

    useEffect(() => {
        if (id) {
            fetchData();
        }
    }, [id]);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [eventRes, tasksRes] = await Promise.all([
                api.get<Event>(`/events/${id}`),
                api.get<Task[]>(`/events/${id}/tasks`)
            ]);
            setEvent(eventRes.data);
            setTasks(tasksRes.data);
            setPageError(null);
        } catch (error: any) {
            console.error('Failed to fetch task data', error);
            setPageError(error.response?.data?.detail || 'Failed to load data');
        } finally {
            setLoading(false);
        }
    };

    const handleCreateTask = async (data: TaskCreateRequest) => {
        setCreating(true);
        setModalError(null);
        try {
            await api.post(`/events/${id}/tasks`, data);
            setIsCreateModalOpen(false);
            fetchData();
        } catch (error: any) {
            console.error('Failed to create task', error);
            const msg = error.response?.data?.detail || error.response?.data?.message || 'Failed to create task';
            setModalError(Array.isArray(msg) ? msg[0].msg : msg);
        } finally {
            setCreating(false);
        }
    };

    const handleUpdateTask = async (data: any) => {
        if (!editingTask) return;
        setUpdating(true);
        setModalError(null);
        try {
            await api.put(`/tasks/${editingTask.id}`, data);
            setIsEditModalOpen(false);
            setEditingTask(null);
            fetchData();
        } catch (error: any) {
            console.error('Failed to update task', error);
            const msg = error.response?.data?.detail || error.response?.data?.message || 'Failed to update task';
            setModalError(Array.isArray(msg) ? msg[0].msg : msg);
        } finally {
            setUpdating(false);
        }
    };

    const handleToggleComplete = async (task: Task) => {
        try {
            setPageError(null);
            await api.put(`/tasks/${task.id}`, {
                completed: !task.completed
            });
            setTasks(prev => prev.map(t => t.id === task.id ? { ...t, completed: !t.completed } : t));
        } catch (error: any) {
            console.error('Failed to toggle task', error);
            const msg = error.response?.data?.detail || error.response?.data?.message || 'Failed to update task status';
            setPageError(msg);
        }
    };

    const initiateDeleteTask = (taskId: string) => {
        setTaskToDelete(taskId);
        setShowDeleteConfirm(true);
        setPageError(null);
    };

    const handleConfirmDelete = async () => {
        if (!taskToDelete) return;
        setIsDeleting(true);
        try {
            await api.delete(`/tasks/${taskToDelete}`);
            setTasks(prev => prev.filter(t => t.id !== taskToDelete));
            setShowDeleteConfirm(false);
            setTaskToDelete(null);
        } catch (error: any) {
            console.error('Failed to delete task', error);
            setPageError(error.response?.data?.detail || 'Failed to delete task');
            setShowDeleteConfirm(false);
        } finally {
            setIsDeleting(false);
        }
    };

    const openEditModal = (task: Task) => {
        setEditingTask(task);
        setIsEditModalOpen(true);
        setModalError(null);
    };

    if (loading) return <div className="min-h-screen flex items-center justify-center"><Spinner size="lg" /></div>;

    // Permissions
    const isOrganizer = user && event && (event.organizer_ids.includes(user.id) || user.role === 'admin');

    if (!isOrganizer) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-center">
                    <h1 className="text-xl font-bold text-white mb-2">Access Denied</h1>
                    <p className="text-dark-400 mb-4">Only organizers can manage tasks.</p>
                    <Link href={`/events/${id}`}>
                        <Button variant="secondary">Go Back</Button>
                    </Link>
                </div>
            </div>
        );
    }

    const assignedTasks = tasks.map(task => {
        const assignee = event?.organizers?.find(org => org.id === task.assignee_id);
        return {
            ...task,
            assigneeName: assignee ? assignee.full_name : null
        };
    });

    const filteredTasks = assignedTasks.filter(task => {
        if (activeFilter === 'mine') {
            return task.assignee_id === user?.id;
        }
        return true;
    });

    return (
        <div className="min-h-screen bg-dark-900 py-12">
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
                <Link href={`/events/${id}`} className="inline-flex items-center text-dark-300 hover:text-white mb-8 transition-colors">
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Back to Event
                </Link>

                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-3xl font-bold text-white mb-2">Event Tasks</h1>
                        <p className="text-dark-400">Manage to-dos for <span className="text-primary-400">{event?.title}</span></p>
                    </div>
                    <Button onClick={() => {
                        setIsCreateModalOpen(true);
                        setModalError(null);
                    }}>
                        <Plus className="w-4 h-4 mr-2" />
                        New Task
                    </Button>
                </div>

                {pageError && (
                    <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm font-medium">
                        Error: {pageError}
                    </div>
                )}

                <div className="flex gap-2 mb-6 p-1 bg-dark-800 rounded-lg w-fit">
                    <button
                        onClick={() => setActiveFilter('all')}
                        className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${activeFilter === 'all'
                            ? 'bg-dark-700 text-white shadow-sm'
                            : 'text-dark-400 hover:text-white'
                            }`}
                    >
                        All Tasks ({tasks.length})
                    </button>
                    <button
                        onClick={() => setActiveFilter('mine')}
                        className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${activeFilter === 'mine'
                            ? 'bg-dark-700 text-white shadow-sm'
                            : 'text-dark-400 hover:text-white'
                            }`}
                    >
                        My Tasks ({tasks.filter(t => t.assignee_id === user?.id).length})
                    </button>
                </div>

                <div className="space-y-4">
                    {filteredTasks.length === 0 ? (
                        <div className="text-center py-12 border-2 border-dashed border-dark-700 rounded-xl">
                            <div className="w-12 h-12 rounded-full bg-dark-800 flex items-center justify-center mx-auto mb-4 text-dark-400">
                                <CheckCircle2 className="w-6 h-6" />
                            </div>
                            <h3 className="text-lg font-medium text-white mb-1">No tasks found</h3>
                            <p className="text-dark-400">
                                {activeFilter === 'mine' ? "You have no tasks assigned." : "Create a task to get started."}
                            </p>
                        </div>
                    ) : (
                        filteredTasks.map(task => {
                            const canComplete = user && (user.role === 'admin' || event?.created_by_id === user.id || task.assignee_id === user.id);

                            return (
                                <Card key={task.id} className="group hover:border-dark-600 transition-colors">
                                    <div className="flex items-start gap-4">
                                        <button
                                            onClick={() => canComplete && handleToggleComplete(task)}
                                            disabled={!canComplete}
                                            className={`mt-1 flex-shrink-0 transition-colors ${task.completed
                                                ? 'text-green-500'
                                                : canComplete
                                                    ? 'text-dark-500 hover:text-dark-300'
                                                    : 'text-dark-700 cursor-not-allowed'
                                                }`}
                                            title={!canComplete ? "Only assignee or admin can complete this task" : ""}
                                        >
                                            {task.completed ? <CheckCircle2 className="w-6 h-6" /> : <Circle className="w-6 h-6" />}
                                        </button>

                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-start justify-between gap-4">
                                                <h3 className={`font-medium text-lg ${task.completed ? 'text-dark-400 line-through' : 'text-white'}`}>
                                                    {task.title}
                                                </h3>
                                                <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                    <button
                                                        onClick={() => openEditModal(task)}
                                                        className="p-2 text-dark-400 hover:text-white hover:bg-dark-700/50 rounded-lg transition-colors"
                                                    >
                                                        <Edit2 className="w-4 h-4" />
                                                    </button>
                                                    <button
                                                        onClick={() => initiateDeleteTask(task.id)}
                                                        className="p-2 text-dark-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                                                    >
                                                        <Trash2 className="w-4 h-4" />
                                                    </button>
                                                </div>
                                            </div>

                                            {task.description && (
                                                <p className={`mt-1 text-sm ${task.completed ? 'text-dark-500' : 'text-dark-300'}`}>
                                                    {task.description}
                                                </p>
                                            )}

                                            <div className="mt-4 flex items-center gap-3">
                                                {task.assigneeName ? (
                                                    <Badge variant="default" className="bg-blue-500/10 text-blue-400 border-blue-500/20 text-xs">
                                                        Assigned to {task.assigneeName}
                                                    </Badge>
                                                ) : (
                                                    <Badge variant="outline" className="text-xs text-dark-500 border-dashed">
                                                        Unassigned
                                                    </Badge>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                </Card>
                            );
                        })
                    )}
                </div>

                <Modal
                    isOpen={isCreateModalOpen}
                    onClose={() => setIsCreateModalOpen(false)}
                    title="Create New Task"
                >
                    {modalError && (
                        <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
                            {modalError}
                        </div>
                    )}
                    <TaskForm
                        assignees={event?.organizers || []}
                        onSubmit={handleCreateTask}
                        isLoading={creating}
                    />
                </Modal>

                <Modal
                    isOpen={isEditModalOpen}
                    onClose={() => {
                        setIsEditModalOpen(false);
                        setEditingTask(null);
                    }}
                    title="Edit Task"
                >
                    {modalError && (
                        <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
                            {modalError}
                        </div>
                    )}
                    {editingTask && (
                        <TaskForm
                            initialValues={editingTask}
                            assignees={event?.organizers || []}
                            onSubmit={handleUpdateTask}
                            isLoading={updating}
                            submitLabel="Save Changes"
                        />
                    )}
                </Modal>

                <ConfirmationModal
                    isOpen={showDeleteConfirm}
                    onClose={() => setShowDeleteConfirm(false)}
                    onConfirm={handleConfirmDelete}
                    title="Delete Task"
                    message="Are you sure you want to delete this task? This action cannot be undone."
                    confirmLabel="Delete"
                    isLoading={isDeleting}
                />
            </div>
        </div>
    );
}
