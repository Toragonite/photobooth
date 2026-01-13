/**
 * Vitest test setup file.
 * This file runs before each test file.
 */

import '@testing-library/jest-dom'
import { afterEach, afterAll, beforeAll, vi } from 'vitest'
import { cleanup } from '@testing-library/react'
import { server, resetStores } from './mocks/server'

// Start MSW server before all tests
beforeAll(() => {
  server.listen({ onUnhandledRequest: 'bypass' })
})

// Reset handlers and stores after each test
afterEach(() => {
  cleanup()
  server.resetHandlers()
  resetStores()
})

// Clean up after all tests
afterAll(() => {
  server.close()
})

// Mock window.matchMedia for responsive tests
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(() => false),
  }),
})

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
})

// Mock sessionStorage
const sessionStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
Object.defineProperty(window, 'sessionStorage', {
  value: sessionStorageMock,
})

// Mock navigator.mediaDevices for camera tests
Object.defineProperty(navigator, 'mediaDevices', {
  writable: true,
  value: {
    getUserMedia: vi.fn(),
    enumerateDevices: vi.fn(() => Promise.resolve([])),
  },
})
