#!/bin/bash
cd "$(dirname "$0")"
export NEXT_PUBLIC_API_URL=http://localhost:8001
npm run dev
