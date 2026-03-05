# TradeNexus AI - Product Requirements Document

## Original Problem Statement
Build a private, invite-only, enterprise-grade AI Trade Matchmaking Engine for a principal trade aggregator. Convert international demand (Africa, Middle East, Europe) into verified, high-probability trade opportunities for Indian exporters, using AI-assisted structuring, scoring, and matchmaking, with mandatory human approval.

## Architecture & Tech Stack
- **Frontend**: React + Tailwind CSS + Shadcn/UI
- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **AI Integration**: OpenAI GPT-5.2 via Emergent LLM Key
- **Authentication**: JWT-based custom auth

## User Personas
1. **Admin (Principal Aggregator)**: Full access to upload demands, run AI matchmaking, approve matches, manage deals, review financing requests, track revenue
2. **Exporter (Paid User)**: View anonymized opportunities, express interest, track own deals, request financing, manage subscription

## Core Requirements (Static)
- 5 Sectors: Agriculture, Marine/Frozen Foods, Pharma, Special Chemicals, Value-Added Agri Products
- 3 Regions: Africa, Middle East, Europe
- 6 Pipeline Stages: Received → Interest → Shortlisted → Introduction → Negotiation → Closed
- Premium enterprise UI (navy/charcoal base, gold accent, Inter font)

## What's Been Implemented ✅

### Phase 1: Core MVP (January 15, 2026)
- [x] JWT Authentication (admin/exporter roles)
- [x] Trade Opportunity CRUD with AI parsing
- [x] Exporter Profile Management
- [x] Deal Pipeline Management (6 stages)
- [x] AI Matchmaking Engine

### Phase 2: Trade Finance & Revenue (March 3, 2026)

#### Trade Finance Engine
- [x] Financing request workflow (requested → under_review → sent_to_nbfc → nbfc_offer_received → accepted/rejected)
- [x] Exporter financing request form (PO value, financing amount, production time, payment method)
- [x] Admin finance requests panel with status management
- [x] NBFC offer recording by admin
- [x] Exporter offer acceptance flow

#### Risk Scoring Engine
- [x] Trade Risk Score (0-100) calculation
- [x] 4-factor scoring: Exporter strength (30%), Buyer country risk (20%), Payment method risk (25%), Deal size vs turnover (25%)
- [x] Risk categories: Low, Medium, High, Very High
- [x] Recommended financing ratio based on risk

#### Revenue Model
- [x] SaaS Subscriptions (Basic ₹9,999, Premium ₹24,999, Enterprise ₹49,999/year)
- [x] Deal Commission (1.5% of closed deal value)
- [x] Financing Commission (3% of approved loan amount)
- [x] Revenue dashboard with summary and records

## Database Collections
- users, opportunities, exporter_profiles, deals, interests
- finance_requests, risk_scores, revenue_records

## API Endpoints Added
- POST /api/finance-requests - Create financing request
- GET /api/finance-requests - List financing requests
- PUT /api/finance-requests/{id}/status - Update status
- PUT /api/finance-requests/{id}/nbfc-offer - Record NBFC offer
- POST /api/finance-requests/{id}/accept - Accept offer
- GET /api/risk-scores/{deal_id} - Get risk score
- POST /api/risk-scores/calculate - Calculate risk score
- GET /api/subscription/me - Get subscription status
- POST /api/subscription/upgrade - Upgrade plan
- GET /api/revenue - Get revenue records
- GET /api/revenue/summary - Get revenue summary
- POST /api/deals/{id}/close - Close deal with commission

## Demo Credentials
- **Admin**: admin@tradenexus.com / admin123
- **Exporter**: agrimax@export.in / exporter123

## Next Tasks
1. Email notification system for financing status changes
2. PDF export for financing requests to send to NBFCs
3. Advanced analytics with charts and trends
4. Bulk NBFC integration via API
