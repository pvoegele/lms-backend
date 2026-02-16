"""
Vercel Deployment Entrypoint - Serverless Function Adapter
==========================================================

This module serves as the adapter for deploying the FastAPI application
to Vercel's serverless platform.

Vercel Serverless Requirements:
1. Python ASGI application must be exposed in api/ directory
2. Application must be named 'app' (Vercel convention)
3. Must be compatible with serverless execution model

What This Module Does:
- Imports the main FastAPI application from launch_nexus
- Exposes it with the name 'app' for Vercel's runtime
- Allows deployment without code changes to main application

Serverless Considerations:
- Cold starts: First request may be slower
- Stateless: No in-memory state between requests
- Timeout limits: Requests have time limits (typically 10-60s)
- Connection pooling: Database connections managed by SQLAlchemy pool

Deployment:
1. Configure environment variables in Vercel dashboard
2. Deploy via: vercel --prod
3. Application available at your-project.vercel.app

Local Testing:
The main application can still be run locally via:
  python launch_nexus.py

This file is only used in Vercel deployment context.

For more information:
- Vercel Python documentation: https://vercel.com/docs/functions/serverless-functions/runtimes/python
- FastAPI deployment guide: https://fastapi.tiangolo.com/deployment/
"""
from launch_nexus import nexus_application

# Vercel expects the FastAPI app to be named 'app'
# This is a simple re-export with the required name
app = nexus_application
