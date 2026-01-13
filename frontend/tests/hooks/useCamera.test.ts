import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useCamera } from '@/hooks/useCamera';

// Mock MediaStream and tracks
const createMockTrack = () => ({
  stop: vi.fn(),
  kind: 'video' as const,
  label: 'Mock Video Track',
  enabled: true,
  id: `mock-track-id-${Math.random()}`,
  muted: false,
  readyState: 'live' as const,
});

const createMockStream = (track = createMockTrack()) => ({
  getTracks: vi.fn(() => [track]),
  getVideoTracks: vi.fn(() => [track]),
  getAudioTracks: vi.fn(() => []),
  addTrack: vi.fn(),
  removeTrack: vi.fn(),
  active: true,
  id: `mock-stream-id-${Math.random()}`,
});

describe('useCamera hook', () => {
  let getUserMediaMock: ReturnType<typeof vi.fn>;
  let mockStream: ReturnType<typeof createMockStream>;
  let mockTrack: ReturnType<typeof createMockTrack>;

  beforeEach(() => {
    // Reset mocks
    vi.clearAllMocks();

    // Create fresh mock for each test
    mockTrack = createMockTrack();
    mockStream = createMockStream(mockTrack);

    // Setup getUserMedia mock on the existing navigator.mediaDevices
    getUserMediaMock = vi.fn().mockResolvedValue(mockStream);
    (navigator.mediaDevices.getUserMedia as ReturnType<typeof vi.fn>) = getUserMediaMock;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('initial state', () => {
    it('returns initial state with isReady false', () => {
      const { result } = renderHook(() => useCamera());

      expect(result.current.isReady).toBe(false);
      expect(result.current.error).toBeNull();
      expect(result.current.stream).toBeNull();
      expect(result.current.videoRef).toBeDefined();
    });

    it('accepts custom options', () => {
      const options = {
        facingMode: 'environment' as const,
        width: 1920,
        height: 1080,
      };

      const { result } = renderHook(() => useCamera(options));

      expect(result.current.videoRef).toBeDefined();
    });
  });

  describe('start function', () => {
    it('requests camera with correct constraints', async () => {
      const { result } = renderHook(() => useCamera({
        facingMode: 'user',
        width: 1280,
        height: 960,
      }));

      await act(async () => {
        await result.current.start();
      });

      expect(getUserMediaMock).toHaveBeenCalledWith({
        video: {
          facingMode: 'user',
          width: { ideal: 1280 },
          height: { ideal: 960 },
        },
        audio: false,
      });
    });

    it('uses default constraints when no options provided', async () => {
      const { result } = renderHook(() => useCamera());

      await act(async () => {
        await result.current.start();
      });

      expect(getUserMediaMock).toHaveBeenCalledWith({
        video: {
          facingMode: 'user',
          width: { ideal: 1280 },
          height: { ideal: 960 },
        },
        audio: false,
      });
    });

    it('sets stream after successful start', async () => {
      const { result } = renderHook(() => useCamera());

      await act(async () => {
        await result.current.start();
      });

      expect(result.current.stream).toBe(mockStream);
    });

    it('handles NotAllowedError (permission denied)', async () => {
      const permissionError = new Error('Permission denied');
      permissionError.name = 'NotAllowedError';
      getUserMediaMock.mockRejectedValueOnce(permissionError);

      const { result } = renderHook(() => useCamera());

      await act(async () => {
        await result.current.start();
      });

      expect(result.current.error).toBe('Camera permission denied');
      expect(result.current.isReady).toBe(false);
    });

    it('handles NotFoundError (no camera)', async () => {
      const notFoundError = new Error('No camera found');
      notFoundError.name = 'NotFoundError';
      getUserMediaMock.mockRejectedValueOnce(notFoundError);

      const { result } = renderHook(() => useCamera());

      await act(async () => {
        await result.current.start();
      });

      expect(result.current.error).toBe('No camera found');
    });

    it('handles NotSupportedError', async () => {
      const notSupportedError = new Error('Not supported');
      notSupportedError.name = 'NotSupportedError';
      getUserMediaMock.mockRejectedValueOnce(notSupportedError);

      const { result } = renderHook(() => useCamera());

      await act(async () => {
        await result.current.start();
      });

      expect(result.current.error).toBe('Camera not supported');
    });

    it('handles generic errors', async () => {
      const genericError = new Error('Something went wrong');
      genericError.name = 'UnknownError';
      getUserMediaMock.mockRejectedValueOnce(genericError);

      const { result } = renderHook(() => useCamera());

      await act(async () => {
        await result.current.start();
      });

      expect(result.current.error).toBe('Camera error: Something went wrong');
    });

    it('handles non-Error throws', async () => {
      getUserMediaMock.mockRejectedValueOnce('string error');

      const { result } = renderHook(() => useCamera());

      await act(async () => {
        await result.current.start();
      });

      expect(result.current.error).toBe('Unknown camera error');
    });

    it('clears previous error on new start attempt', async () => {
      // First call fails
      const error = new Error('Camera error');
      error.name = 'NotAllowedError';
      getUserMediaMock.mockRejectedValueOnce(error);

      const { result } = renderHook(() => useCamera());

      await act(async () => {
        await result.current.start();
      });

      expect(result.current.error).toBe('Camera permission denied');

      // Second call succeeds - create new mock stream
      const newMockStream = createMockStream();
      getUserMediaMock.mockResolvedValueOnce(newMockStream);

      await act(async () => {
        await result.current.start();
      });

      expect(result.current.error).toBeNull();
    });
  });

  describe('stop function', () => {
    it('stops all tracks when stream exists', async () => {
      const { result } = renderHook(() => useCamera());

      await act(async () => {
        await result.current.start();
      });

      expect(result.current.stream).toBe(mockStream);

      act(() => {
        result.current.stop();
      });

      expect(mockTrack.stop).toHaveBeenCalled();
      expect(result.current.stream).toBeNull();
      expect(result.current.isReady).toBe(false);
    });

    it('handles stop when no stream exists', () => {
      const { result } = renderHook(() => useCamera());

      // Should not throw
      act(() => {
        result.current.stop();
      });

      expect(result.current.stream).toBeNull();
    });
  });

  describe('capture function', () => {
    it('returns null when camera is not ready', async () => {
      const { result } = renderHook(() => useCamera());

      let capturedImage: string | null = null;
      await act(async () => {
        capturedImage = await result.current.capture();
      });

      expect(capturedImage).toBeNull();
    });

    it('returns null when video ref is not available', async () => {
      const { result } = renderHook(() => useCamera());

      // Start camera (sets stream but videoRef.current is null in tests)
      await act(async () => {
        await result.current.start();
      });

      // Since videoRef.current is null in tests, capture should return null
      let capturedImage: string | null = null;
      await act(async () => {
        capturedImage = await result.current.capture();
      });

      // Without a real video element, this will return null
      expect(capturedImage).toBeNull();
    });
  });

  describe('cleanup on unmount', () => {
    it('does not throw when unmounting without starting', () => {
      const { unmount } = renderHook(() => useCamera());

      expect(() => unmount()).not.toThrow();
    });
  });

  describe('different facing modes', () => {
    it('uses environment facing mode when specified', async () => {
      const { result } = renderHook(() => useCamera({ facingMode: 'environment' }));

      await act(async () => {
        await result.current.start();
      });

      expect(getUserMediaMock).toHaveBeenCalledWith(
        expect.objectContaining({
          video: expect.objectContaining({
            facingMode: 'environment',
          }),
        })
      );
    });

    it('uses user facing mode by default', async () => {
      const { result } = renderHook(() => useCamera());

      await act(async () => {
        await result.current.start();
      });

      expect(getUserMediaMock).toHaveBeenCalledWith(
        expect.objectContaining({
          video: expect.objectContaining({
            facingMode: 'user',
          }),
        })
      );
    });
  });

  describe('custom dimensions', () => {
    it('uses provided width and height', async () => {
      const { result } = renderHook(() => useCamera({
        width: 1920,
        height: 1080,
      }));

      await act(async () => {
        await result.current.start();
      });

      expect(getUserMediaMock).toHaveBeenCalledWith(
        expect.objectContaining({
          video: expect.objectContaining({
            width: { ideal: 1920 },
            height: { ideal: 1080 },
          }),
        })
      );
    });
  });
});
