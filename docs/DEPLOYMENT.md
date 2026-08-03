# Deployment

## EC2 voice backend

1. Launch Ubuntu on EC2, attach `VaaniSevaRealtimeRole`, and allow inbound 80/443.
   Restrict SSH 22 to the operator's IP; do not expose port 7860.
2. Attach `backend/deployment/ec2-runtime-policy.json` to the instance role.
3. Point a DNS `A` record at the instance and set `VOICE_DOMAIN` and
   `PUBLIC_BASE_URL` in `backend/.env`.
4. From `backend/deployment`, run `docker compose -f docker-compose.ec2.yml up -d --build`.
5. Set the Twilio number's incoming-call webhook to `https://VOICE_DOMAIN/twiml` (POST).

To enable callbacks, set `TWILIO_PHONE_NUMBER`, `CALLBACK_ENABLED=true`, and
`WEB_ALLOWED_ORIGINS=https://YOUR-VERCEL-DOMAIN`. Redeploy after environment changes.

## Vercel website

Import this repository, select `website` as the root directory, and set
`VITE_VOICE_BASE_URL` to the public voice origin. Vercel will detect Vite. The
included rewrite keeps React Router routes working.

## Cost shutdown

Stop EC2 when the demo is paused; EBS and public IPv4 may still incur charges.
Terminate EC2 and delete residual EBS/Elastic IP resources after the event. Release
the Twilio number separately if it is no longer needed. AWS Budgets alerts do not
automatically stop resources.
