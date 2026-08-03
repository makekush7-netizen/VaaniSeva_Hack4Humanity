# Security and responsible-AI boundary

- AWS uses an EC2 instance role; no long-lived AWS key is required in production.
- IAM permits only Nova/Titan invocation and read-only access to one vector table.
- Twilio webhook and Media Stream signatures are validated.
- Provider tokens and the Twilio auth token remain in the server `.env` and are never
  compiled into the Vercel website.
- Callback numbers are validated and requests are rate-limited. Production teams
  should add a shared rate-limit store and abuse monitoring before broad public use.
- Scheme results are guidance, never an approval decision. Health output is general
  navigation, not diagnosis or dosage. Emergencies are escalated to verified channels.
- Live prices fail closed. The model is explicitly prohibited from inventing a value.
- Logs should contain operational event types, not transcripts or credentials.

If any secret was pasted into a development chat or terminal, rotate it before a
public launch even when Git history is clean.
