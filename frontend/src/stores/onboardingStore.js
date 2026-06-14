/**
 * Onboarding store - tracks wizard state across steps.
 */

import { create } from 'zustand';

export const useOnboardingStore = create((set) => ({
  currentStep: 0,
  householdName: '',
  householdDescription: '',
  profileData: null,
  emailConnected: false,
  firstScanTriggered: false,
  isComplete: false,

  setStep: (step) => set({ currentStep: step }),

  setHousehold: (householdName, householdDescription = '') =>
    set({ householdName, householdDescription }),

  setProfile: (profileData) => set({ profileData }),

  setEmailConnected: (connected) => set({ emailConnected: connected }),

  setFirstScanTriggered: (triggered) => set({ firstScanTriggered: triggered }),

  complete: () => set({ isComplete: true }),

  reset: () => set({
    currentStep: 0,
    householdName: '',
    householdDescription: '',
    profileData: null,
    emailConnected: false,
    firstScanTriggered: false,
    isComplete: false,
  }),
}));
