'use client';

import Modal from './Modal';
import Button from './Button';
import { AlertTriangle } from 'lucide-react';

interface ConfirmationModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void | Promise<void>;
    title: string;
    message: string;
    confirmLabel?: string;
    cancelLabel?: string;
    variant?: 'danger' | 'warning' | 'info';
    isLoading?: boolean;
}

export default function ConfirmationModal({
    isOpen,
    onClose,
    onConfirm,
    title,
    message,
    confirmLabel = 'Confirm',
    cancelLabel = 'Cancel',
    variant = 'danger',
    isLoading = false
}: ConfirmationModalProps) {

    const handleConfirm = async () => {
        await onConfirm();
        // onClose should be called by the parent or passing auto-close logic here, 
        // but typically parent handles closure on success.
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose} title={title}>
            <div className="space-y-4">
                <div className="flex items-start gap-4 p-4 bg-dark-800/50 rounded-lg">
                    {variant === 'danger' && <AlertTriangle className="w-6 h-6 text-red-500 flex-shrink-0 mt-0.5" />}
                    {variant === 'warning' && <AlertTriangle className="w-6 h-6 text-yellow-500 flex-shrink-0 mt-0.5" />}
                    <p className="text-dark-200 text-sm leading-relaxed">
                        {message}
                    </p>
                </div>

                <div className="flex justify-end gap-3 pt-2">
                    <Button
                        variant="secondary"
                        onClick={onClose}
                        disabled={isLoading}
                    >
                        {cancelLabel}
                    </Button>
                    <Button
                        variant={variant === 'danger' ? 'danger' : 'primary'}
                        onClick={handleConfirm}
                        isLoading={isLoading}
                    >
                        {confirmLabel}
                    </Button>
                </div>
            </div>
        </Modal>
    );
}
