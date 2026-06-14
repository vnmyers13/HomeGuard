import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { useOnboardingStore } from '../../../src/stores/onboardingStore'

describe('onboardingStore', () => {
  beforeEach(() => {
    useOnboardingStore.getState().reset()
  })

  it('has correct initial state', () => {
    const state = useOnboardingStore.getState()
    expect(state.currentStep).toBe(0)
    expect(state.householdName).toBe('')
    expect(state.isComplete).toBe(false)
  })

  it('updates current step', () => {
    const { setStep } = useOnboardingStore.getState()
    setStep(3)
    expect(useOnboardingStore.getState().currentStep).toBe(3)
  })

  it('sets household data', () => {
    const { setHousehold } = useOnboardingStore.getState()
    setHousehold('Test Family', 'A test household')
    expect(useOnboardingStore.getState().householdName).toBe('Test Family')
    expect(useOnboardingStore.getState().householdDescription).toBe('A test household')
  })

  it('sets profile data', () => {
    const { setProfile } = useOnboardingStore.getState()
    setProfile({ name: 'John', dob: '1990-01-01' })
    expect(useOnboardingStore.getState().profileData).toEqual({ name: 'John', dob: '1990-01-01' })
  })

  it('marks as complete', () => {
    const { complete } = useOnboardingStore.getState()
    complete()
    expect(useOnboardingStore.getState().isComplete).toBe(true)
  })

  it('resets to initial state', () => {
    const { setStep, complete } = useOnboardingStore.getState()
    setStep(4)
    complete()
    expect(useOnboardingStore.getState().currentStep).toBe(4)
    expect(useOnboardingStore.getState().isComplete).toBe(true)

    useOnboardingStore.getState().reset()
    expect(useOnboardingStore.getState().currentStep).toBe(0)
    expect(useOnboardingStore.getState().isComplete).toBe(false)
  })
})
