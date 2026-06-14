import React from 'react'
/**
 * Onboarding wizard - 5-step flow for new households.
 * Sprint 6: Guided setup for first-time users.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useOnboardingStore } from '../stores/onboardingStore';
import { useAuthStore } from '../stores/authStore';
import Card from '../components/Card';

const TOTAL_STEPS = 5;

export default function Onboarding() {
  const navigate = useNavigate();
  const {
    currentStep,
    householdName,
    householdDescription,
    profileData,
    emailConnected,
    setStep,
    setHousehold,
    setProfile,
    setEmailConnected,
    setFirstScanTriggered,
    complete,
    reset,
  } = useOnboardingStore();
  const { user } = useAuthStore();

  // Form state
  const [householdNameInput, setHouseholdNameInput] = useState(householdName);
  const [householdDescInput, setHouseholdDescInput] = useState(householdDescription);
  const [profileName, setProfileName] = useState(profileData?.name || '');
  const [dob, setDob] = useState(profileData?.date_of_birth || '');
  const [address, setAddress] = useState(profileData?.address || '');
  const [emailInput, setEmailInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Check if user already has a household - redirect if so
  useState(() => {
    const existing = localStorage.getItem('homeguard_onboarding_complete');
    if (existing === 'true') {
      navigate('/');
    }
  });

  const handleNext = async () => {
    setError('');
    setLoading(true);

    try {
      if (currentStep === 0) {
        // Welcome -> Household
        setStep(1);
      } else if (currentStep === 1) {
        // Household -> Profile
        if (!householdNameInput.trim()) {
          setError('Please enter a household name');
          return;
        }
        setHousehold(householdNameInput.trim(), householdDescInput.trim());
        setStep(2);
      } else if (currentStep === 2) {
        // Profile -> Email
        if (!profileName.trim()) {
          setError('Please enter a profile name');
          return;
        }
        setProfile({ name: profileName.trim(), date_of_birth: dob, address });
        setStep(3);
      } else if (currentStep === 3) {
        // Email -> First Scan
        if (emailInput.trim()) {
          setEmailConnected(true);
        }
        setStep(4);
      } else if (currentStep === 4) {
        // First Scan -> Complete
        complete();
        localStorage.setItem('homeguard_onboarding_complete', 'true');
        navigate('/');
      }
    } catch (err) {
      setError('Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSkip = () => {
    complete();
    localStorage.setItem('homeguard_onboarding_complete', 'true');
    navigate('/');
  };

  const steps = [
    { title: 'Welcome', description: 'Get started with HomeGuard' },
    { title: 'Household', description: 'Name your household' },
    { title: 'Profile', description: 'Add your first profile' },
    { title: 'Email', description: 'Connect your email (optional)' },
    { title: 'First Scan', description: 'Run your first scan' },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-purple-50 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        {/* Progress */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            {steps.map((step, idx) => (
              <button
                key={idx}
                onClick={() => idx < currentStep && setStep(idx)}
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors ${
                  idx <= currentStep
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
                } ${idx < currentStep ? 'cursor-pointer hover:bg-indigo-500' : ''}`}
              >
                {idx < currentStep ? '✓' : idx + 1}
              </button>
            ))}
          </div>
          <div className="h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-indigo-600 rounded-full transition-all duration-300"
              style={{ width: `${((currentStep + 1) / TOTAL_STEPS) * 100}%` }}
            />
          </div>
          <p className="text-center text-sm text-gray-500 dark:text-gray-400 mt-2">
            Step {currentStep + 1} of {TOTAL_STEPS}: {steps[currentStep].title}
          </p>
        </div>

        <Card className="p-8">
          {error && (
            <div className="mb-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg px-4 py-2 text-sm text-red-700 dark:text-red-400">
              {error}
            </div>
          )}

          {/* Step 0: Welcome */}
          {currentStep === 0 && (
            <div className="text-center space-y-4">
              <div className="text-5xl mb-4">🛡️</div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Welcome to HomeGuard</h2>
              <p className="text-gray-500 dark:text-gray-400">
                Protect your personal data across 50+ data broker sites.
                We'll scan for your information, submit removal requests, and monitor for relistings.
              </p>
              <div className="flex flex-col gap-2 text-sm text-gray-600 dark:text-gray-400">
                <p>✓ Automatic PII scanning across broker sites</p>
                <p>✓ Automated removal requests (web forms, emails, legal letters)</p>
                <p>✓ Continuous monitoring for relistings</p>
                <p>✓ Real-time dashboard with exposure scores</p>
              </div>
            </div>
          )}

          {/* Step 1: Household */}
          {currentStep === 1 && (
            <div className="space-y-4">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">Create Your Household</h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                A household groups related profiles (e.g., family members) for shared monitoring.
              </p>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Household Name *</label>
                <input
                  type="text"
                  value={householdNameInput}
                  onChange={(e) => setHouseholdNameInput(e.target.value)}
                  placeholder="e.g., The Johnson Family"
                  className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Description (optional)</label>
                <textarea
                  value={householdDescInput}
                  onChange={(e) => setHouseholdDescInput(e.target.value)}
                  placeholder="What is this household for?"
                  rows={3}
                  className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                />
              </div>
            </div>
          )}

          {/* Step 2: Profile */}
          {currentStep === 2 && (
            <div className="space-y-4">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">Add Your First Profile</h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Profiles represent individuals. We'll scan for their PII across broker sites.
              </p>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Name *</label>
                <input
                  type="text"
                  value={profileName}
                  onChange={(e) => setProfileName(e.target.value)}
                  placeholder="e.g., John Johnson"
                  className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Date of Birth</label>
                <input
                  type="date"
                  value={dob}
                  onChange={(e) => setDob(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Address</label>
                <input
                  type="text"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  placeholder="e.g., 123 Main St, Anytown, CA 90210"
                  className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                />
              </div>
            </div>
          )}

          {/* Step 3: Email */}
          {currentStep === 3 && (
            <div className="space-y-4">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">Connect Your Email</h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Connecting your email lets us monitor broker responses (opt-out confirmations, removal notices).
                This is optional - you can skip and connect later.
              </p>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email Address</label>
                <input
                  type="email"
                  value={emailInput}
                  onChange={(e) => setEmailInput(e.target.value)}
                  placeholder="your@email.com"
                  className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                />
              </div>
              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3 text-sm text-blue-700 dark:text-blue-400">
                Your email will be used to poll for broker responses via IMAP. We never store your email credentials.
              </div>
            </div>
          )}

          {/* Step 4: First Scan */}
          {currentStep === 4 && (
            <div className="text-center space-y-4">
              <div className="text-5xl mb-4">🔍</div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">Ready for Your First Scan?</h2>
              <p className="text-gray-500 dark:text-gray-400">
                We'll scan {householdName || 'your household'} across all registered data brokers.
                This may take a few minutes.
              </p>
              <div className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                <p>Profiles: {profileName || 'Not added'}</p>
                <p>Brokers: 50+ sites</p>
                <p>Estimated time: 5-10 minutes</p>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-between mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
            {currentStep > 0 ? (
              <button
                onClick={() => setStep(currentStep - 1)}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                Back
              </button>
            ) : (
              <div />
            )}
            <div className="flex gap-3">
              {currentStep > 2 && (
                <button
                  onClick={handleSkip}
                  className="px-4 py-2 text-sm font-medium text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
                >
                  Skip for now
                </button>
              )}
              <button
                onClick={handleNext}
                disabled={loading}
                className="px-6 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
              >
                {loading ? 'Processing...' : currentStep === TOTAL_STEPS - 1 ? 'Start Scan' : 'Continue'}
              </button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
