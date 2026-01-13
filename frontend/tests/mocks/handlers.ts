import { http, HttpResponse, delay } from 'msw';

// Session type for mock store
interface MockSession {
  session_id: string;
  language: string;
  status: string;
  created_at: string;
  completed_at: string | null;
  photos: string[];
  photo_count: number;
  max_photos: number;
  composite_url: string | null;
}

// Session store for stateful mocking
const sessionStore = new Map<string, MockSession>();
let sessionIdCounter = 0;

export function resetStores() {
  sessionStore.clear();
  sessionIdCounter = 0;
}

export const handlers = [
  // POST /api/session - Create session
  http.post('/api/session', async ({ request }) => {
    await delay(50);
    const body = await request.json() as { language?: string };
    sessionIdCounter++;
    const session = {
      session_id: `session-${sessionIdCounter}`,
      language: body.language || 'ko',
      status: 'active',
      created_at: new Date().toISOString(),
      completed_at: null,
      photos: [],
      photo_count: 0,
      max_photos: 4,
      composite_url: null,
    };
    sessionStore.set(session.session_id, session);
    return HttpResponse.json({
      success: true,
      data: session,
    });
  }),

  // GET /api/session/:id - Get session
  http.get('/api/session/:id', async ({ params }) => {
    await delay(50);
    const { id } = params;
    const session = sessionStore.get(id as string);

    if (!session) {
      return HttpResponse.json(
        {
          success: false,
          error: {
            code: 'SESSION_NOT_FOUND',
            message: 'Session not found',
          },
        },
        { status: 404 }
      );
    }

    return HttpResponse.json({
      success: true,
      data: session,
    });
  }),

  // GET /api/settings/public - Get public settings
  http.get('/api/settings/public', async () => {
    await delay(50);
    return HttpResponse.json({
      success: true,
      data: {
        default_language: 'ko',
        countdown_options: [3, 5, 10],
        default_countdown: 5,
        sound_enabled: true,
        max_copies: 3,
        logo_enabled: true,
        date_format: 'YYYY-MM-DD',
      },
    });
  }),

  // GET /api/health - Health check
  http.get('/api/health', async () => {
    await delay(50);
    return HttpResponse.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
    });
  }),
];
