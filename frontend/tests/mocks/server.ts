import { setupServer } from 'msw/node';
import { handlers, resetStores } from './handlers';

export const server = setupServer(...handlers);

export { handlers, resetStores };
