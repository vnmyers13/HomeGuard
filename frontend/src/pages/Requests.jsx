/**
 * Requests - Removal request tracking page
 * Sprint 5: Track and manage removal requests
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getRequests, getRequest, createRequest, updateRequest, deleteRequest, getFollowups, createFollowup, getVerificationScans, downloadLegalLetter } from '../lib/api';
import { useState } from 'react';

export default function Requests() {
    const queryClient = useQueryClient();
    const [selectedRequest, setSelectedRequest] = useState(null);
    const [filterStatus, setFilterStatus] = useState('all');
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [newRequest, setNewRequest] = useState({
        profile_id: '',
        broker_id: '',
        removal_method: 'web_form',
    });

    // Fetch requests
    const { data: requestsData, isLoading } = useQuery({
        queryKey: ['requests', filterStatus],
        queryFn: () => getRequests({ status: filterStatus === 'all' ? undefined : filterStatus }),
    });

    // Fetch selected request details
    const { data: requestData } = useQuery({
        queryKey: ['request', selectedRequest],
        queryFn: () => getRequest(selectedRequest),
        enabled: !!selectedRequest,
    });

    // Fetch followups
    const { data: followupsData } = useQuery({
        queryKey: ['followups', selectedRequest],
        queryFn: () => getFollowups(selectedRequest),
        enabled: !!selectedRequest,
    });

    // Fetch verification scans
    const { data: verificationData } = useQuery({
        queryKey: ['verification-scans', selectedRequest],
        queryFn: () => getVerificationScans(selectedRequest),
        enabled: !!selectedRequest,
    });

    // Create request mutation
    const createMutation = useMutation({
        mutationFn: (data) => createRequest(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['requests'] });
            setShowCreateModal(false);
            setNewRequest({ profile_id: '', broker_id: '', removal_method: 'web_form' });
        },
    });

    // Update request mutation
    const updateMutation = useMutation({
        mutationFn: ({ id, data }) => updateRequest(id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['requests'] });
            if (selectedRequest) queryClient.invalidateQueries({ queryKey: ['request', selectedRequest] });
        },
    });

    // Delete request mutation
    const deleteMutation = useMutation({
        mutationFn: (id) => deleteRequest(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['requests'] });
            setSelectedRequest(null);
        },
    });

    // Create followup mutation
    const followupMutation = useMutation({
        mutationFn: ({ id, data }) => createFollowup(id, data),
        onSuccess: () => {
            if (selectedRequest) queryClient.invalidateQueries({ queryKey: ['followups', selectedRequest] });
        },
    });

    const handleStatusUpdate = (requestId, newStatus) => {
        updateMutation.mutate({ id: requestId, data: { status: newStatus } });
    };

    const handleDelete = (requestId) => {
        if (confirm('Are you sure you want to delete this removal request?')) {
            deleteMutation.mutate(requestId);
        }
    };

    const handleCreateFollowup = (method) => {
        if (selectedRequest) {
            followupMutation.mutate({
                id: selectedRequest,
                data: { method_used: method },
            });
        }
    };

    const handleDownloadPdf = (requestId) => {
        downloadLegalLetter(requestId, 'ccpa').then(response => {
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `ccpa_letter_${requestId}.pdf`);
            document.body.appendChild(link);
            link.click();
            link.remove();
        });
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'pending': return 'bg-yellow-100 text-yellow-800';
            case 'submitted': return 'bg-blue-100 text-blue-800';
            case 'confirmed_removed': return 'bg-green-100 text-green-800';
            case 'still_listed': return 'bg-red-100 text-red-800';
            case 'failed': return 'bg-gray-100 text-gray-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    const getRequestIcon = (method) => {
        switch (method) {
            case 'web_form': return '🌐';
            case 'email': return '📧';
            case 'legal_letter': return '📄';
            default: return '📋';
        }
    };

    if (selectedRequest) {
        const request = requestData?.data;
        const followups = followupsData?.data || [];
        const verifications = verificationData?.data || [];

        return (
            <div className="space-y-6">
                {/* Back button */}
                <button
                    onClick={() => setSelectedRequest(null)}
                    className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
                >
                    ← Back to Requests
                </button>

                {/* Request Detail */}
                {request && (
                    <div className="card">
                        <div className="flex justify-between items-start mb-4">
                            <div>
                                <h2 className="text-xl font-bold text-gray-900">Removal Request</h2>
                                <p className="text-sm text-gray-500 mt-1">{request.id}</p>
                            </div>
                            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(request.status)}`}>
                                {request.status}
                            </span>
                        </div>

                        <div className="grid grid-cols-2 gap-4 mb-6">
                            <div>
                                <label className="text-sm font-medium text-gray-700">Method</label>
                                <p className="text-gray-900">{getRequestIcon(request.removal_method)} {request.removal_method.replace('_', ' ')}</p>
                            </div>
                            <div>
                                <label className="text-sm font-medium text-gray-700">Created</label>
                                <p className="text-gray-900">{new Date(request.created_at).toLocaleDateString()}</p>
                            </div>
                            <div>
                                <label className="text-sm font-medium text-gray-700">Follow-ups</label>
                                <p className="text-gray-900">{request.followup_count}</p>
                            </div>
                            <div>
                                <label className="text-sm font-medium text-gray-700">Confirmation</label>
                                <p className="text-gray-900">{request.confirmation_message || 'N/A'}</p>
                            </div>
                        </div>

                        {/* Status Actions */}
                        <div className="border-t pt-4 mb-4">
                            <h3 className="text-sm font-medium text-gray-700 mb-2">Update Status</h3>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => handleStatusUpdate(request.id, 'submitted')}
                                    className="px-3 py-1.5 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
                                >
                                    Mark Submitted
                                </button>
                                <button
                                    onClick={() => handleStatusUpdate(request.id, 'confirmed_removed')}
                                    className="px-3 py-1.5 bg-green-500 text-white rounded text-sm hover:bg-green-600"
                                >
                                    Confirm Removed
                                </button>
                                <button
                                    onClick={() => handleStatusUpdate(request.id, 'still_listed')}
                                    className="px-3 py-1.5 bg-red-500 text-white rounded text-sm hover:bg-red-600"
                                >
                                    Still Listed
                                </button>
                                <button
                                    onClick={() => handleStatusUpdate(request.id, 'failed')}
                                    className="px-3 py-1.5 bg-gray-500 text-white rounded text-sm hover:bg-gray-600"
                                >
                                    Mark Failed
                                </button>
                            </div>
                        </div>

                        {/* Actions */}
                        <div className="border-t pt-4 mb-4">
                            <h3 className="text-sm font-medium text-gray-700 mb-2">Actions</h3>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => handleDownloadPdf(request.id)}
                                    className="px-3 py-1.5 bg-purple-500 text-white rounded text-sm hover:bg-purple-600"
                                >
                                    Download Legal Letter (PDF)
                                </button>
                                <button
                                    onClick={() => handleCreateFollowup('email')}
                                    className="px-3 py-1.5 bg-indigo-500 text-white rounded text-sm hover:bg-indigo-600"
                                >
                                    Add Email Follow-up
                                </button>
                                <button
                                    onClick={() => handleCreateFollowup('legal')}
                                    className="px-3 py-1.5 bg-indigo-500 text-white rounded text-sm hover:bg-indigo-600"
                                >
                                    Add Legal Follow-up
                                </button>
                                <button
                                    onClick={() => handleDelete(request.id)}
                                    className="px-3 py-1.5 bg-red-500 text-white rounded text-sm hover:bg-red-600"
                                >
                                    Delete
                                </button>
                            </div>
                        </div>

                        {/* Followups */}
                        {followups.length > 0 && (
                            <div className="border-t pt-4">
                                <h3 className="text-sm font-medium text-gray-700 mb-2">Follow-ups ({followups.length})</h3>
                                <div className="space-y-2">
                                    {followups.map((f) => (
                                        <div key={f.id} className="flex items-center gap-3 p-3 bg-gray-50 rounded">
                                            <span className="text-sm font-medium">{f.followup_number}.</span>
                                            <span className="text-sm text-gray-900">{f.method_used}</span>
                                            <span className="text-xs text-gray-500 ml-auto">
                                                {new Date(f.scheduled_at).toLocaleDateString()}
                                            </span>
                                            {f.response_received && <span className="text-green-600 text-xs">✓ Received</span>}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Verification Scans */}
                        {verifications.length > 0 && (
                            <div className="border-t pt-4 mt-4">
                                <h3 className="text-sm font-medium text-gray-700 mb-2">Verification Scans ({verifications.length})</h3>
                                <div className="space-y-2">
                                    {verifications.map((v) => (
                                        <div key={v.id} className="flex items-center gap-3 p-3 bg-gray-50 rounded">
                                            <span className="text-sm text-gray-900">{v.result || 'Pending'}</span>
                                            <span className="text-xs text-gray-500 ml-auto">
                                                Scheduled: {new Date(v.scheduled_at).toLocaleDateString()}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>
        );
    }

    // List view
    const requests = requestsData?.data || [];
    const total = requestsData?.total || 0;

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Removal Requests</h1>
                    <p className="text-gray-600 mt-1">Track and manage your data broker removal requests</p>
                </div>
                <button
                    onClick={() => setShowCreateModal(true)}
                    className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 text-sm"
                >
                    + New Request
                </button>
            </div>

            {/* Filters */}
            <div className="flex gap-2">
                {['all', 'pending', 'submitted', 'confirmed_removed', 'still_listed', 'failed'].map(status => (
                    <button
                        key={status}
                        onClick={() => setFilterStatus(status)}
                        className={`px-3 py-1.5 rounded text-sm ${filterStatus === status ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
                    >
                        {status === 'all' ? 'All' : status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </button>
                ))}
            </div>

            {/* Requests Table */}
            <div className="card">
                {isLoading ? (
                    <div className="text-center py-8 text-gray-500">Loading...</div>
                ) : requests.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                        No removal requests found. Click "New Request" to create one.
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b">
                                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">ID</th>
                                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Method</th>
                                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Status</th>
                                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Follow-ups</th>
                                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Created</th>
                                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {requests.map((r) => (
                                    <tr key={r.id} className="border-b hover:bg-gray-50">
                                        <td className="py-3 px-4 text-sm text-gray-900">{r.id.slice(0, 8)}...</td>
                                        <td className="py-3 px-4 text-sm text-gray-900">{getRequestIcon(r.removal_method)} {r.removal_method.replace('_', ' ')}</td>
                                        <td className="py-3 px-4">
                                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(r.status)}`}>
                                                {r.status}
                                            </span>
                                        </td>
                                        <td className="py-3 px-4 text-sm text-gray-900">{r.followup_count}</td>
                                        <td className="py-3 px-4 text-sm text-gray-900">{new Date(r.created_at).toLocaleDateString()}</td>
                                        <td className="py-3 px-4">
                                            <button
                                                onClick={() => setSelectedRequest(r.id)}
                                                className="text-blue-500 hover:text-blue-600 text-sm"
                                            >
                                                View
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
                {total > 0 && (
                    <div className="py-3 px-4 text-sm text-gray-500 border-t">
                        Showing {requests.length} of {total} requests
                    </div>
                )}
            </div>

            {/* Create Modal */}
            {showCreateModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 w-full max-w-md">
                        <h2 className="text-lg font-bold text-gray-900 mb-4">New Removal Request</h2>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Profile</label>
                                <select
                                    value={newRequest.profile_id}
                                    onChange={(e) => setNewRequest({ ...newRequest, profile_id: e.target.value })}
                                    className="input"
                                >
                                    <option value="">Select profile...</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Broker</label>
                                <select
                                    value={newRequest.broker_id}
                                    onChange={(e) => setNewRequest({ ...newRequest, broker_id: e.target.value })}
                                    className="input"
                                >
                                    <option value="">Select broker...</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Method</label>
                                <select
                                    value={newRequest.removal_method}
                                    onChange={(e) => setNewRequest({ ...newRequest, removal_method: e.target.value })}
                                    className="input"
                                >
                                    <option value="web_form">Web Form</option>
                                    <option value="email">Email</option>
                                    <option value="legal_letter">Legal Letter</option>
                                </select>
                            </div>
                        </div>
                        <div className="flex gap-2 mt-6">
                            <button
                                onClick={() => createMutation.mutate(newRequest)}
                                disabled={!newRequest.profile_id || !newRequest.broker_id}
                                className="flex-1 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
                            >
                                Create Request
                            </button>
                            <button
                                onClick={() => setShowCreateModal(false)}
                                className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
