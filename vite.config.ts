import path from 'path';
import { defineConfig, loadEnv, type Plugin, type ViteDevServer } from 'vite';
import react from '@vitejs/plugin-react';

/**
 * Dev-only bridge for the serverless functions in ./api.
 *
 * In production these files are run by Vercel. The plain Vite dev server knows
 * nothing about them, so without this plugin every POST to /api/analyze 404s.
 * Here we load the handler through Vite (which transpiles the TypeScript),
 * parse the JSON body, and shim the few Express-style response helpers that
 * Vercel's runtime provides.
 */
function devApiRoutes(): Plugin {
  return {
    name: 'dev-api-routes',
    apply: 'serve',
    configureServer(server: ViteDevServer) {
      server.middlewares.use('/api/analyze', async (req, res) => {
        const sendError = (code: number, body: unknown) => {
          res.statusCode = code;
          res.setHeader('Content-Type', 'application/json');
          res.end(JSON.stringify(body));
        };

        try {
          // Read and parse the request body (Vercel does this for us in prod).
          const chunks: Buffer[] = [];
          for await (const chunk of req) chunks.push(chunk as Buffer);
          const raw = Buffer.concat(chunks).toString('utf8');
          (req as any).body = raw ? JSON.parse(raw) : {};

          // Shim res.status(...).json(...) onto the raw Node response.
          const shim = res as any;
          shim.status = (code: number) => {
            res.statusCode = code;
            return shim;
          };
          shim.json = (payload: unknown) => {
            res.setHeader('Content-Type', 'application/json');
            res.end(JSON.stringify(payload));
            return shim;
          };

          const mod = await server.ssrLoadModule('/api/analyze.ts');
          await mod.default(req, res);
        } catch (err) {
          server.config.logger.error(`[dev-api] /api/analyze failed: ${err}`);
          if (!res.writableEnded) {
            sendError(500, {
              error: 'Dev API route failed.',
              details: err instanceof Error ? err.message : String(err),
            });
          }
        }
      });
    },
  };
}

export default defineConfig(({ mode }) => {
  // Load .env.local into the dev server process so api/analyze.ts can read the
  // key. Accepts either API_KEY or GEMINI_API_KEY.
  const env = loadEnv(mode, __dirname, '');
  const apiKey = env.API_KEY || env.GEMINI_API_KEY;
  if (apiKey) process.env.API_KEY = apiKey;

  return {
    root: __dirname,
    server: {
      port: 3000,
      host: '0.0.0.0',
    },
    plugins: [react(), devApiRoutes()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, '.'),
      },
    },
  };
});
