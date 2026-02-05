"""
Vercel deployment entrypoint
This module exposes the FastAPI application for Vercel's serverless deployment
"""
from launch_nexus import nexus_application

# Vercel expects the FastAPI app to be named 'app'
app = nexus_application
