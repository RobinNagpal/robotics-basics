import { handle } from 'hono/aws-lambda';
import { app } from './app';

// AWS Lambda calls this through the function URL.
export const handler = handle(app);
