from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'tradenexus')]

# JWT Config
JWT_SECRET = os.environ.get('JWT_SECRET', 'tradenexus-secret-key')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Create the main app
app = FastAPI(title="TradeNexus AI")
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ===================== MODELS =====================

SECTORS = ["Agriculture", "Marine / Frozen Foods", "Pharma", "Special Chemicals", "Value-Added Agri Products"]
REGIONS = ["Africa", "Middle East", "Europe"]
ENGAGEMENT_MODES = ["Introduction-only", "Introduction + Negotiation Support"]
PIPELINE_STAGES = ["Received", "Interest", "Shortlisted", "Introduction", "Negotiation", "Closed"]
CERTIFICATIONS = {
    "Agriculture": ["FSSAI", "ISO 22000", "HACCP", "BRC", "Halal"],
    "Marine / Frozen Foods": ["FSSAI", "ISO 22000", "HACCP", "BRC", "Halal"],
    "Pharma": ["WHO-GMP", "USFDA", "EU-GMP", "ISO 9001"],
    "Special Chemicals": ["ISO 9001", "ISO 14001", "REACH", "MSDS"],
    "Value-Added Agri Products": ["FSSAI", "ISO 22000", "HACCP", "BRC", "Halal"]
}

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    company_name: str
    role: str = "exporter"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    company_name: str
    role: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class OpportunityCreate(BaseModel):
    sector: str
    source_country: str
    region: str
    product_name: str
    hs_code: Optional[str] = None
    quantity: str
    delivery_timeline: str
    compliance_requirements: List[str] = []
    engagement_mode: str = "Introduction-only"
    raw_text: Optional[str] = None

class OpportunityResponse(BaseModel):
    id: str
    sector: str
    source_country: str
    region: str
    product_name: str
    hs_code: Optional[str]
    quantity: str
    delivery_timeline: str
    compliance_requirements: List[str]
    engagement_mode: str
    opportunity_score: float
    risk_score: float
    status: str
    created_at: str
    matched_exporters: List[dict] = []

class ExporterProfileCreate(BaseModel):
    sectors: List[str]
    products: List[str]
    capacity: str
    certifications: List[str]
    country_experience: List[str]

class ExporterProfileResponse(BaseModel):
    id: str
    user_id: str
    company_name: str
    sectors: List[str]
    products: List[str]
    capacity: str
    certifications: List[str]
    country_experience: List[str]
    reliability_score: Optional[float] = None

class DealCreate(BaseModel):
    opportunity_id: str
    exporter_id: str

class DealResponse(BaseModel):
    id: str
    opportunity_id: str
    exporter_id: str
    exporter_company: str
    opportunity_product: str
    stage: str
    created_at: str
    updated_at: str

class ExpressInterestRequest(BaseModel):
    opportunity_id: str
    indicative_terms: Optional[str] = None

class AIParseRequest(BaseModel):
    raw_text: str

# ===================== TRADE FINANCE MODELS =====================

FINANCING_STATUSES = ["requested", "under_review", "sent_to_nbfc", "nbfc_offer_received", "accepted_by_exporter", "rejected"]
PAYMENT_METHODS = ["LC", "open_account", "advance"]
SUBSCRIPTION_PLANS = ["Basic", "Premium", "Enterprise"]
SUBSCRIPTION_PRICES = {"Basic": 9999, "Premium": 24999, "Enterprise": 49999}

class FinanceRequestCreate(BaseModel):
    deal_id: str
    purchase_order_value: float
    financing_amount_requested: float
    production_time_days: int
    shipment_date: str
    buyer_country: str
    payment_method: str
    exporter_bank_details: str
    past_export_turnover: float

class FinanceRequestResponse(BaseModel):
    id: str
    exporter_id: str
    exporter_company: str
    deal_id: str
    opportunity_product: str
    purchase_order_value: float
    financing_amount_requested: float
    production_time_days: int
    shipment_date: str
    buyer_country: str
    payment_method: str
    financing_status: str
    risk_score: Optional[int] = None
    risk_category: Optional[str] = None
    nbfc_partner: Optional[str] = None
    nbfc_offer_amount: Optional[float] = None
    nbfc_interest_rate: Optional[float] = None
    admin_notes: Optional[str] = None
    created_at: str

class NBFCOfferUpdate(BaseModel):
    nbfc_partner: str
    offer_amount: float
    interest_rate: float
    admin_notes: Optional[str] = None

class RiskScoreResponse(BaseModel):
    deal_id: str
    exporter_id: str
    risk_score: int
    risk_category: str
    scoring_breakdown: dict
    recommended_financing_ratio: float
    created_at: str

class SubscriptionUpdate(BaseModel):
    plan: str

class RevenueRecordResponse(BaseModel):
    id: str
    revenue_type: str
    exporter_id: Optional[str]
    deal_id: Optional[str]
    amount: float
    status: str
    description: str
    created_at: str

class ExporterFinanceProfile(BaseModel):
    years_in_business: int = 5
    export_turnover: float = 1000000
    past_shipments: int = 50

# ===================== BUYER DISCOVERY MODELS =====================

class BuyerDiscoverRequest(BaseModel):
    hs_code: str
    country: Optional[str] = None
    product_name: Optional[str] = None
    max_results: int = 10

class BuyerContact(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    source: Optional[str] = None

class BuyerResponse(BaseModel):
    id: str
    company_name: str
    country: Optional[str] = None
    hs_code: str
    domain: Optional[str] = None
    industry: Optional[str] = None
    headcount: Optional[str] = None
    hq_city: Optional[str] = None
    evidence_url: Optional[str] = None
    evidence_snippet: Optional[str] = None
    contacts: List[BuyerContact] = []
    enrichment_status: str = "pending"
    verified: bool = False
    discovered_at: str
    last_enriched_at: Optional[str] = None

class BuyerVerifyUpdate(BaseModel):
    verified: bool

# ===================== AUTH HELPERS =====================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def require_admin(user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

# ===================== AI SERVICE =====================

OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

def _get_openai_client():
    """Lazy-init the OpenAI async client. Returns None if no key configured."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import AsyncOpenAI
        return AsyncOpenAI(api_key=api_key)
    except Exception as e:
        logger.error(f"OpenAI client init failed: {e}")
        return None

async def openai_chat_json(system: str, user: str, model: Optional[str] = None):
    """Call OpenAI in JSON mode and return parsed JSON (dict or list). Returns None on failure."""
    client = _get_openai_client()
    if client is None:
        return None
    try:
        resp = await client.chat.completions.create(
            model=model or OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        content = resp.choices[0].message.content or ""
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"OpenAI JSON parse error: {e}")
        return None
    except Exception as e:
        logger.error(f"OpenAI chat error: {e}")
        return None

async def ai_parse_opportunity(raw_text: str) -> dict:
    """Parse raw embassy/brief text into structured opportunity via OpenAI."""
    system = (
        "You are a trade opportunity parser. Extract structured data from trade briefs. "
        "Return a JSON object with fields: "
        "sector (one of: Agriculture, Marine / Frozen Foods, Pharma, Special Chemicals, Value-Added Agri Products), "
        "source_country (string), "
        "region (one of: Africa, Middle East, Europe), "
        "product_name (string), "
        "hs_code (string or null), "
        "quantity (string with unit), "
        "delivery_timeline (string), "
        "compliance_requirements (array of certification strings), "
        "opportunity_score (0.0 to 1.0 — feasibility), "
        "risk_score (0.0 to 1.0 — complexity)."
    )
    parsed = await openai_chat_json(system, f"Parse this trade brief:\n\n{raw_text}")
    if isinstance(parsed, dict):
        return parsed
    return mock_parse_opportunity(raw_text)

def mock_parse_opportunity(raw_text: str) -> dict:
    """Fallback mock parser"""
    text_lower = raw_text.lower()
    
    sector = "Agriculture"
    if "pharma" in text_lower or "medicine" in text_lower:
        sector = "Pharma"
    elif "marine" in text_lower or "fish" in text_lower or "seafood" in text_lower:
        sector = "Marine / Frozen Foods"
    elif "chemical" in text_lower:
        sector = "Special Chemicals"
    elif "dried" in text_lower or "processed" in text_lower:
        sector = "Value-Added Agri Products"
    
    region = "Africa"
    if any(c in text_lower for c in ["dubai", "saudi", "uae", "qatar", "oman"]):
        region = "Middle East"
    elif any(c in text_lower for c in ["germany", "france", "uk", "spain", "italy"]):
        region = "Europe"
    
    return {
        "sector": sector,
        "source_country": "Nigeria" if region == "Africa" else ("UAE" if region == "Middle East" else "Germany"),
        "region": region,
        "product_name": "Agricultural Products",
        "hs_code": None,
        "quantity": "1000 MT",
        "delivery_timeline": "Q1 2025",
        "compliance_requirements": CERTIFICATIONS.get(sector, [])[:3],
        "opportunity_score": 0.75,
        "risk_score": 0.25
    }

async def ai_score_opportunity(opportunity: dict) -> tuple:
    """Calculate opportunity and risk scores via OpenAI. Falls back to (0.75, 0.25)."""
    user_msg = (
        f"Score this opportunity:\n"
        f"Sector: {opportunity.get('sector')}\n"
        f"Country: {opportunity.get('source_country')}\n"
        f"Quantity: {opportunity.get('quantity')}\n"
        f"Compliance: {opportunity.get('compliance_requirements')}"
    )
    parsed = await openai_chat_json(
        "Score trade opportunities. Return JSON: {opportunity_score: 0.0-1.0, risk_score: 0.0-1.0}.",
        user_msg,
    )
    if isinstance(parsed, dict):
        return (parsed.get("opportunity_score", 0.75), parsed.get("risk_score", 0.25))
    return (0.75, 0.25)

async def ai_rank_exporters(opportunity: dict, exporters: list) -> list:
    """Rank exporters for an opportunity using deterministic feature-match scoring."""
    try:
        # Calculate base scores
        scored_exporters = []
        for exp in exporters:
            score = 0
            # Sector match
            if opportunity.get("sector") in exp.get("sectors", []):
                score += 30
            # Product match (fuzzy)
            opp_product = opportunity.get("product_name", "").lower()
            for prod in exp.get("products", []):
                if any(word in opp_product for word in prod.lower().split()):
                    score += 20
                    break
            # Country experience
            if opportunity.get("source_country") in exp.get("country_experience", []):
                score += 20
            # Certification match
            required_certs = set(opportunity.get("compliance_requirements", []))
            exporter_certs = set(exp.get("certifications", []))
            if required_certs and exporter_certs:
                cert_match = len(required_certs & exporter_certs) / len(required_certs)
                score += int(cert_match * 30)
            
            scored_exporters.append({**exp, "match_score": min(score, 100)})
        
        # Sort and return top 5
        scored_exporters.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        return scored_exporters[:5]
    except Exception as e:
        logger.error(f"AI ranking error: {e}")
        return exporters[:5]

# ===================== BUYER DISCOVERY AGENT =====================
#
# Pipeline:
#   1. Tavily web search → public trade-data snippets (importers/buyers per HS code)
#   2. OpenAI (gpt-4o-mini, JSON mode) extracts structured rows: [{company, country, domain, evidence}]
#   3. Apollo /organizations/enrich → domain, industry, headcount, hq
#   4. Apollo /people/search filtered by procurement-style titles
#   5. Hunter /domain-search fallback for emails when Apollo has no people
#
# Each enrichment step gracefully skips if its API key is missing — V1 with
# only TAVILY_API_KEY still returns real, sourced buyer rows.

async def tavily_search(query: str, max_results: int = 8) -> list:
    """Web search via Tavily. Returns [{url, title, content}]."""
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        logger.warning("No TAVILY_API_KEY — buyer discovery cannot run")
        return []
    try:
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": api_key,
                    "query": query,
                    "search_depth": "advanced",
                    "max_results": max_results,
                    "include_answer": False,
                },
            )
            res.raise_for_status()
            data = res.json()
            return [
                {
                    "url": r.get("url"),
                    "title": r.get("title"),
                    "content": r.get("content", "")[:1500],
                }
                for r in data.get("results", [])
            ]
    except Exception as e:
        logger.error(f"Tavily search error: {e}")
        return []

async def llm_extract_buyers(snippets: list, hs_code: str, product_name: Optional[str], country: Optional[str]) -> list:
    """Extract structured buyer rows from web snippets via OpenAI JSON mode."""
    if not snippets:
        return []
    if not os.environ.get("OPENAI_API_KEY"):
        logger.warning("No OPENAI_API_KEY — falling back to naive snippet parse")
        return _naive_extract_buyers(snippets, country)

    snippets_text = "\n\n".join(
        f"[{i}] URL: {s['url']}\nTITLE: {s['title']}\nCONTENT: {s['content']}"
        for i, s in enumerate(snippets)
    )
    country_clause = f" in {country}" if country else ""
    product_clause = f" ({product_name})" if product_name else ""

    system = (
        "You extract real importer/buyer companies from trade-data web snippets. "
        "Only include companies that the snippets actually name. Do NOT invent names. "
        "Return a JSON object with a single key 'buyers' whose value is an array of objects with fields: "
        "company_name (string), country (string or null), "
        "company_domain (string — best-guess primary website domain like 'olamgroup.com', or null if unknown — never guess a generic domain), "
        "evidence_url (string — the source URL from the snippet that names this company), "
        "evidence_snippet (short quote, <=200 chars, justifying inclusion). "
        "Skip entries where you cannot identify a specific company name."
    )
    user = (
        f"Find buyers/importers of HS code {hs_code}{product_clause}{country_clause}.\n\n"
        f"Snippets:\n\n{snippets_text}"
    )
    parsed = await openai_chat_json(system, user)
    rows = []
    if isinstance(parsed, dict):
        rows = parsed.get("buyers") or parsed.get("results") or parsed.get("data") or []
    elif isinstance(parsed, list):
        rows = parsed
    if not isinstance(rows, list) or not rows:
        return _naive_extract_buyers(snippets, country)

    return [
        {
            "company_name": (r.get("company_name") or "").strip(),
            "country": (r.get("country") or country),
            "company_domain": _clean_domain(r.get("company_domain")),
            "evidence_url": r.get("evidence_url"),
            "evidence_snippet": (r.get("evidence_snippet") or "")[:200],
        }
        for r in rows
        if isinstance(r, dict) and (r.get("company_name") or "").strip()
    ]

def _naive_extract_buyers(snippets: list, country: Optional[str]) -> list:
    """Last-resort: surface snippets as raw evidence rows so admin still sees something."""
    out = []
    for s in snippets[:5]:
        title = (s.get("title") or "").strip()
        if not title:
            continue
        out.append({
            "company_name": title[:120],
            "country": country,
            "company_domain": None,
            "evidence_url": s.get("url"),
            "evidence_snippet": (s.get("content") or "")[:200],
        })
    return out

# Trade-data hosts whose URLs are NOT a buyer's own website
_TRADE_DATA_HOSTS = {
    "volza.com", "panjiva.com", "importgenius.com", "trademap.org",
    "exportgenius.in", "tradedata.pro", "exim.gov.in", "spgglobal.com",
    "thetradedesk.com", "marketresearch.com", "datawheel.us", "ibef.org",
    "linkedin.com", "wikipedia.org", "facebook.com", "twitter.com", "x.com",
    "youtube.com", "google.com", "amazon.com", "alibaba.com",
}

def _clean_domain(value) -> Optional[str]:
    """Normalize 'https://www.foo.com/path' → 'foo.com'. Reject trade-data hosts."""
    if not value or not isinstance(value, str):
        return None
    v = value.strip().lower()
    if not v:
        return None
    # strip scheme
    for prefix in ("https://", "http://"):
        if v.startswith(prefix):
            v = v[len(prefix):]
    # strip path/query/fragment
    for sep in ("/", "?", "#"):
        idx = v.find(sep)
        if idx != -1:
            v = v[:idx]
    if v.startswith("www."):
        v = v[4:]
    if not v or "." not in v:
        return None
    if v in _TRADE_DATA_HOSTS:
        return None
    return v

def _domain_from_evidence_url(url: Optional[str]) -> Optional[str]:
    """Pull a candidate company domain from an evidence URL, skipping trade-data hosts."""
    return _clean_domain(url)

async def apollo_enrich_organization(domain: Optional[str]) -> Optional[dict]:
    """Apollo organization enrichment by domain. Returns {domain, industry, headcount, hq_city, apollo_id} or None."""
    api_key = os.environ.get("APOLLO_API_KEY")
    if not api_key or not domain:
        return None
    try:
        import httpx
        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.get(
                "https://api.apollo.io/api/v1/organizations/enrich",
                params={"domain": domain},
                headers={
                    "Cache-Control": "no-cache",
                    "Content-Type": "application/json",
                    "X-Api-Key": api_key,
                },
            )
            if res.status_code != 200:
                return None
            org = (res.json() or {}).get("organization") or {}
            if not org:
                return None
            return {
                "apollo_id": org.get("id"),
                "domain": org.get("primary_domain") or _clean_domain(org.get("website_url")) or domain,
                "industry": org.get("industry"),
                "headcount": str(org.get("estimated_num_employees") or "") or None,
                "hq_city": org.get("city"),
            }
    except Exception as e:
        logger.error(f"Apollo enrich error for {domain}: {e}")
        return None

async def apollo_search_people(apollo_org_id: str) -> list:
    """Search Apollo people filtered by procurement-style titles. Returns list of contacts."""
    api_key = os.environ.get("APOLLO_API_KEY")
    if not api_key or not apollo_org_id:
        return []
    try:
        import httpx
        titles = ["procurement", "imports", "sourcing", "buyer", "purchasing", "supply chain"]
        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.post(
                "https://api.apollo.io/api/v1/mixed_people/search",
                headers={
                    "Cache-Control": "no-cache",
                    "Content-Type": "application/json",
                    "X-Api-Key": api_key,
                },
                json={
                    "organization_ids": [apollo_org_id],
                    "person_titles": titles,
                    "page": 1,
                    "per_page": 5,
                },
            )
            if res.status_code != 200:
                return []
            people = (res.json() or {}).get("people", [])
            return [
                {
                    "name": p.get("name"),
                    "title": p.get("title"),
                    "email": p.get("email"),
                    "linkedin_url": p.get("linkedin_url"),
                    "source": "apollo",
                }
                for p in people
                if p.get("name")
            ]
    except Exception as e:
        logger.error(f"Apollo people search error: {e}")
        return []

async def hunter_domain_search(domain: str) -> list:
    """Hunter.io domain search → emails by role. Fallback when Apollo has no people."""
    api_key = os.environ.get("HUNTER_API_KEY")
    if not api_key or not domain:
        return []
    try:
        import httpx
        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.get(
                "https://api.hunter.io/v2/domain-search",
                params={
                    "domain": domain,
                    "api_key": api_key,
                    "limit": 10,
                },
            )
            if res.status_code != 200:
                return []
            emails = (res.json() or {}).get("data", {}).get("emails", [])
            return [
                {
                    "name": (
                        " ".join(filter(None, [e.get("first_name"), e.get("last_name")])).strip()
                        or None
                    ),
                    "title": e.get("position"),
                    "email": e.get("value"),
                    "linkedin_url": e.get("linkedin"),
                    "source": "hunter",
                }
                for e in emails
                if e.get("value")
            ]
    except Exception as e:
        logger.error(f"Hunter domain search error: {e}")
        return []

async def discover_buyers_for_hs(
    hs_code: str,
    country: Optional[str] = None,
    product_name: Optional[str] = None,
    max_results: int = 10,
) -> list:
    """
    Orchestrator. Returns list of buyer dicts (already upserted into Mongo).
    Steps degrade gracefully if Apollo/Hunter keys are missing.
    """
    # Build search queries — multiple angles improve recall
    base = f"importers buyers HS code {hs_code}"
    if product_name:
        base += f" {product_name}"
    queries = [
        f"{base}{(' in ' + country) if country else ''}",
        f"{(product_name or 'HS ' + hs_code)} importers list{(' ' + country) if country else ''} site:volza.com OR site:panjiva.com OR site:importgenius.com OR site:trademap.org",
        f"top importers of {(product_name or hs_code)}{(' ' + country) if country else ''}",
    ]

    # 1. Tavily searches (parallel-ish via sequential awaits — small N)
    all_snippets = []
    seen_urls = set()
    for q in queries:
        results = await tavily_search(q, max_results=8)
        for r in results:
            if r["url"] and r["url"] not in seen_urls:
                seen_urls.add(r["url"])
                all_snippets.append(r)

    if not all_snippets:
        return []

    # 2. LLM extraction
    candidates = await llm_extract_buyers(all_snippets, hs_code, product_name, country)

    # Dedup within this batch on (company_name lowercased, country)
    deduped = {}
    for c in candidates:
        key = (c["company_name"].lower().strip(), (c.get("country") or "").lower().strip())
        if key not in deduped:
            deduped[key] = c
    candidates = list(deduped.values())[:max_results]

    # 3 + 4 + 5. Enrichment loop
    now_iso = datetime.now(timezone.utc).isoformat()
    saved = []
    for cand in candidates:
        company_name = cand["company_name"]
        cand_country = cand.get("country")

        # Resolve a domain: LLM-extracted first, then evidence-URL host (skipping trade-data hosts)
        domain = _clean_domain(cand.get("company_domain")) or _domain_from_evidence_url(cand.get("evidence_url"))

        contacts: list = []
        enrichment_status = "pending"

        org = await apollo_enrich_organization(domain) if domain else None
        if org:
            enrichment_status = "partial"
            # Apollo people search is paid-only on the Free plan — call returns [] silently if blocked.
            people = await apollo_search_people(org.get("apollo_id"))
            if people:
                contacts.extend(people)
                enrichment_status = "enriched"

        # Hunter is the primary email source when Apollo people-search is unavailable
        if domain and not contacts:
            hunter_contacts = await hunter_domain_search(domain)
            if hunter_contacts:
                contacts.extend(hunter_contacts)
                enrichment_status = "enriched" if org else "partial"

        # Upsert (dedup on company+country+hs_code)
        existing = await db.buyers.find_one(
            {
                "company_name_lower": company_name.lower(),
                "country_lower": (cand_country or "").lower(),
                "hs_code": hs_code,
            },
            {"_id": 0},
        )

        doc = {
            "company_name": company_name,
            "company_name_lower": company_name.lower(),
            "country": cand_country,
            "country_lower": (cand_country or "").lower(),
            "hs_code": hs_code,
            "domain": (org or {}).get("domain") or domain,
            "industry": (org or {}).get("industry"),
            "headcount": (org or {}).get("headcount"),
            "hq_city": (org or {}).get("hq_city"),
            "evidence_url": cand.get("evidence_url"),
            "evidence_snippet": cand.get("evidence_snippet"),
            "contacts": contacts,
            "enrichment_status": enrichment_status,
            "last_enriched_at": now_iso if org or contacts else None,
        }

        if existing:
            await db.buyers.update_one({"id": existing["id"]}, {"$set": doc})
            buyer_id = existing["id"]
            verified = existing.get("verified", False)
            discovered_at = existing.get("discovered_at", now_iso)
        else:
            buyer_id = str(uuid.uuid4())
            doc.update({"id": buyer_id, "verified": False, "discovered_at": now_iso})
            await db.buyers.insert_one(doc)
            verified = False
            discovered_at = now_iso

        saved.append({
            "id": buyer_id,
            "company_name": company_name,
            "country": cand_country,
            "hs_code": hs_code,
            "domain": doc["domain"],
            "industry": doc["industry"],
            "headcount": doc["headcount"],
            "hq_city": doc["hq_city"],
            "evidence_url": doc["evidence_url"],
            "evidence_snippet": doc["evidence_snippet"],
            "contacts": contacts,
            "enrichment_status": enrichment_status,
            "verified": verified,
            "discovered_at": discovered_at,
            "last_enriched_at": doc["last_enriched_at"],
        })

    return saved

# ===================== RISK SCORING ENGINE =====================

COUNTRY_RISK_SCORES = {
    # Low risk (Europe)
    "Germany": 10, "France": 12, "UK": 15, "Netherlands": 10, "Spain": 18, "Italy": 20,
    # Medium risk (Middle East)
    "UAE": 25, "Saudi Arabia": 28, "Qatar": 22, "Oman": 30,
    # Higher risk (Africa)
    "Nigeria": 45, "Kenya": 40, "South Africa": 35, "Morocco": 32, "Egypt": 38
}

PAYMENT_METHOD_RISK = {
    "LC": 10,  # Letter of Credit - Low risk
    "advance": 5,  # Advance payment - Very low risk
    "open_account": 40  # Open account - Higher risk
}

def calculate_trade_risk_score(
    exporter_profile: dict,
    deal_data: dict,
    finance_data: Optional[dict] = None
) -> dict:
    """
    Calculate Trade Risk Score (0-100)
    
    Inputs:
    - Exporter profile (years_in_business, export_turnover, certifications, past_shipments)
    - Deal data (deal_value, buyer_country, payment_method, delivery_terms)
    
    Scoring weights:
    - Exporter strength: 30%
    - Buyer country risk: 20%
    - Payment method risk: 25%
    - Deal size vs turnover: 25%
    """
    
    # Extract values with defaults
    years_in_business = exporter_profile.get("years_in_business", 5)
    export_turnover = exporter_profile.get("export_turnover", 1000000)
    certifications = exporter_profile.get("certifications", [])
    past_shipments = exporter_profile.get("past_shipments", 50)
    reliability_score = exporter_profile.get("reliability_score", 0.8)
    
    deal_value = deal_data.get("deal_value", 100000)
    buyer_country = deal_data.get("buyer_country", "Nigeria")
    payment_method = deal_data.get("payment_method", "open_account")
    
    scoring_breakdown = {}
    
    # 1. Exporter Strength Score (30%) - Higher is better, invert for risk
    exporter_score = 0
    if years_in_business >= 10:
        exporter_score += 30
    elif years_in_business >= 5:
        exporter_score += 20
    elif years_in_business >= 2:
        exporter_score += 10
    
    if len(certifications) >= 4:
        exporter_score += 30
    elif len(certifications) >= 2:
        exporter_score += 20
    else:
        exporter_score += 10
    
    if past_shipments >= 100:
        exporter_score += 25
    elif past_shipments >= 50:
        exporter_score += 15
    else:
        exporter_score += 5
    
    exporter_score += int(reliability_score * 15)
    
    # Invert: high exporter score = low risk contribution
    exporter_risk = max(0, 100 - exporter_score)
    scoring_breakdown["exporter_strength"] = {"score": exporter_score, "risk_contribution": int(exporter_risk * 0.30)}
    
    # 2. Buyer Country Risk (20%)
    country_risk = COUNTRY_RISK_SCORES.get(buyer_country, 35)
    scoring_breakdown["buyer_country_risk"] = {"country": buyer_country, "risk_contribution": int(country_risk * 0.20)}
    
    # 3. Payment Method Risk (25%)
    payment_risk = PAYMENT_METHOD_RISK.get(payment_method, 30)
    scoring_breakdown["payment_method_risk"] = {"method": payment_method, "risk_contribution": int(payment_risk * 0.25)}
    
    # 4. Deal Size vs Turnover Risk (25%)
    if export_turnover > 0:
        deal_ratio = deal_value / export_turnover
        if deal_ratio <= 0.1:  # Deal is <10% of turnover - low risk
            size_risk = 10
        elif deal_ratio <= 0.25:  # 10-25% - medium risk
            size_risk = 25
        elif deal_ratio <= 0.5:  # 25-50% - higher risk
            size_risk = 45
        else:  # >50% - high risk
            size_risk = 70
    else:
        size_risk = 50
    
    scoring_breakdown["deal_size_risk"] = {"deal_value": deal_value, "turnover": export_turnover, "risk_contribution": int(size_risk * 0.25)}
    
    # Calculate total risk score
    total_risk = (
        int(exporter_risk * 0.30) +
        int(country_risk * 0.20) +
        int(payment_risk * 0.25) +
        int(size_risk * 0.25)
    )
    
    # Clamp to 0-100
    total_risk = max(0, min(100, total_risk))
    
    # Determine risk category
    if total_risk <= 25:
        risk_category = "Low"
    elif total_risk <= 50:
        risk_category = "Medium"
    elif total_risk <= 75:
        risk_category = "High"
    else:
        risk_category = "Very High"
    
    # Calculate recommended financing ratio based on risk
    if total_risk <= 25:
        recommended_financing = 0.80  # 80% of order value
    elif total_risk <= 50:
        recommended_financing = 0.65  # 65%
    elif total_risk <= 75:
        recommended_financing = 0.50  # 50%
    else:
        recommended_financing = 0.35  # 35%
    
    return {
        "risk_score": total_risk,
        "risk_category": risk_category,
        "scoring_breakdown": scoring_breakdown,
        "recommended_financing_ratio": recommended_financing
    }

async def check_subscription_valid(user_id: str) -> bool:
    """Check if exporter has valid subscription"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        return False
    
    # Admin always has access
    if user.get("role") == "admin":
        return True
    
    subscription_status = user.get("subscription_status", "active")
    subscription_expiry = user.get("subscription_expiry")
    
    if subscription_status != "active":
        return False
    
    if subscription_expiry:
        expiry_date = datetime.fromisoformat(subscription_expiry.replace('Z', '+00:00'))
        if expiry_date < datetime.now(timezone.utc):
            return False
    
    return True

# ===================== AUTH ROUTES =====================

@api_router.post("/auth/register", response_model=TokenResponse, status_code=201)
async def register(data: UserCreate):
    existing = await db.users.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if data.role not in ["admin", "exporter"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": data.email,
        "password_hash": hash_password(data.password),
        "company_name": data.company_name,
        "role": data.role,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    
    token = create_token(user_id, data.role)
    return TokenResponse(
        access_token=token,
        user=UserResponse(id=user_id, email=data.email, company_name=data.company_name, role=data.role)
    )

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(data: UserLogin):
    user = await db.users.find_one({"email": data.email}, {"_id": 0})
    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user["id"], user["role"])
    return TokenResponse(
        access_token=token,
        user=UserResponse(id=user["id"], email=user["email"], company_name=user["company_name"], role=user["role"])
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    return UserResponse(id=user["id"], email=user["email"], company_name=user["company_name"], role=user["role"])

# ===================== OPPORTUNITY ROUTES =====================

@api_router.post("/opportunities", response_model=OpportunityResponse, status_code=201)
async def create_opportunity(data: OpportunityCreate, user: dict = Depends(require_admin)):
    opp_id = str(uuid.uuid4())
    
    # Score the opportunity
    opp_score, risk_score = await ai_score_opportunity(data.model_dump())
    
    opp_doc = {
        "id": opp_id,
        "sector": data.sector,
        "source_country": data.source_country,
        "region": data.region,
        "product_name": data.product_name,
        "hs_code": data.hs_code,
        "quantity": data.quantity,
        "delivery_timeline": data.delivery_timeline,
        "compliance_requirements": data.compliance_requirements,
        "engagement_mode": data.engagement_mode,
        "opportunity_score": opp_score,
        "risk_score": risk_score,
        "status": "Active",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user["id"],
        "matched_exporters": []
    }
    await db.opportunities.insert_one(opp_doc)
    
    return OpportunityResponse(**{k: v for k, v in opp_doc.items() if k != "_id"})

@api_router.post("/opportunities/parse", response_model=dict)
async def parse_opportunity(data: AIParseRequest, user: dict = Depends(require_admin)):
    """Parse raw text/document into structured opportunity data using AI"""
    parsed = await ai_parse_opportunity(data.raw_text)
    return parsed

@api_router.get("/opportunities", response_model=List[OpportunityResponse])
async def get_opportunities(
    sector: Optional[str] = None,
    region: Optional[str] = None,
    status: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    query = {}
    if sector:
        query["sector"] = sector
    if region:
        query["region"] = region
    if status:
        query["status"] = status
    
    opportunities = await db.opportunities.find(query, {"_id": 0}).to_list(100)
    
    # For exporters, filter out internal data
    if user["role"] == "exporter":
        for opp in opportunities:
            opp.pop("created_by", None)
            opp.pop("matched_exporters", None)
            opp["matched_exporters"] = []
    
    return [OpportunityResponse(**opp) for opp in opportunities]

@api_router.get("/opportunities/{opp_id}", response_model=OpportunityResponse)
async def get_opportunity(opp_id: str, user: dict = Depends(get_current_user)):
    opp = await db.opportunities.find_one({"id": opp_id}, {"_id": 0})
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    if user["role"] == "exporter":
        opp.pop("created_by", None)
        opp["matched_exporters"] = []
    
    return OpportunityResponse(**opp)

@api_router.put("/opportunities/{opp_id}/status")
async def update_opportunity_status(opp_id: str, status: str, user: dict = Depends(require_admin)):
    if status not in ["Draft", "Active", "Matched", "Closed"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    result = await db.opportunities.update_one({"id": opp_id}, {"$set": {"status": status}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    return {"message": "Status updated"}

@api_router.post("/opportunities/{opp_id}/match")
async def match_exporters(opp_id: str, user: dict = Depends(require_admin)):
    """Run AI matchmaking for an opportunity"""
    opp = await db.opportunities.find_one({"id": opp_id}, {"_id": 0})
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    # Get all exporter profiles
    profiles = await db.exporter_profiles.find({}, {"_id": 0}).to_list(100)
    
    # Enrich with company names
    for profile in profiles:
        user_doc = await db.users.find_one({"id": profile["user_id"]}, {"_id": 0})
        if user_doc:
            profile["company_name"] = user_doc.get("company_name", "Unknown")
    
    # Rank exporters
    ranked = await ai_rank_exporters(opp, profiles)
    
    # Update opportunity with matched exporters
    matched = [{"exporter_id": e["id"], "company_name": e.get("company_name"), "match_score": e.get("match_score", 0)} for e in ranked]
    await db.opportunities.update_one({"id": opp_id}, {"$set": {"matched_exporters": matched}})
    
    return {"matched_exporters": matched}

# ===================== EXPORTER PROFILE ROUTES =====================

@api_router.post("/exporter-profiles", response_model=ExporterProfileResponse, status_code=201)
async def create_exporter_profile(data: ExporterProfileCreate, user: dict = Depends(get_current_user)):
    if user["role"] != "exporter":
        raise HTTPException(status_code=403, detail="Only exporters can create profiles")
    
    existing = await db.exporter_profiles.find_one({"user_id": user["id"]})
    if existing:
        raise HTTPException(status_code=400, detail="Profile already exists")
    
    profile_id = str(uuid.uuid4())
    profile_doc = {
        "id": profile_id,
        "user_id": user["id"],
        "sectors": data.sectors,
        "products": data.products,
        "capacity": data.capacity,
        "certifications": data.certifications,
        "country_experience": data.country_experience,
        "reliability_score": 0.8,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.exporter_profiles.insert_one(profile_doc)
    
    return ExporterProfileResponse(**{k: v for k, v in profile_doc.items() if k != "_id"}, company_name=user["company_name"])

@api_router.get("/exporter-profiles/me", response_model=ExporterProfileResponse)
async def get_my_profile(user: dict = Depends(get_current_user)):
    profile = await db.exporter_profiles.find_one({"user_id": user["id"]}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return ExporterProfileResponse(**profile, company_name=user["company_name"])

@api_router.put("/exporter-profiles/me", response_model=ExporterProfileResponse)
async def update_my_profile(data: ExporterProfileCreate, user: dict = Depends(get_current_user)):
    result = await db.exporter_profiles.update_one(
        {"user_id": user["id"]},
        {"$set": data.model_dump()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    profile = await db.exporter_profiles.find_one({"user_id": user["id"]}, {"_id": 0})
    return ExporterProfileResponse(**profile, company_name=user["company_name"])

@api_router.get("/exporter-profiles", response_model=List[ExporterProfileResponse])
async def get_all_profiles(user: dict = Depends(require_admin)):
    profiles = await db.exporter_profiles.find({}, {"_id": 0}).to_list(100)
    result = []
    for p in profiles:
        user_doc = await db.users.find_one({"id": p["user_id"]}, {"_id": 0})
        company_name = user_doc.get("company_name", "Unknown") if user_doc else "Unknown"
        result.append(ExporterProfileResponse(**p, company_name=company_name))
    return result

# ===================== DEAL ROUTES =====================

@api_router.post("/deals", response_model=DealResponse, status_code=201)
async def create_deal(data: DealCreate, user: dict = Depends(require_admin)):
    opp = await db.opportunities.find_one({"id": data.opportunity_id}, {"_id": 0})
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    exporter_profile = await db.exporter_profiles.find_one({"id": data.exporter_id}, {"_id": 0})
    if not exporter_profile:
        raise HTTPException(status_code=404, detail="Exporter not found")
    
    exporter_user = await db.users.find_one({"id": exporter_profile["user_id"]}, {"_id": 0})
    
    deal_id = str(uuid.uuid4())
    deal_doc = {
        "id": deal_id,
        "opportunity_id": data.opportunity_id,
        "exporter_id": data.exporter_id,
        "exporter_user_id": exporter_profile["user_id"],
        "stage": "Received",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.deals.insert_one(deal_doc)
    
    return DealResponse(
        id=deal_id,
        opportunity_id=data.opportunity_id,
        exporter_id=data.exporter_id,
        exporter_company=exporter_user.get("company_name", "Unknown") if exporter_user else "Unknown",
        opportunity_product=opp.get("product_name", "Unknown"),
        stage="Received",
        created_at=deal_doc["created_at"],
        updated_at=deal_doc["updated_at"]
    )

@api_router.post("/deals/express-interest")
async def express_interest(data: ExpressInterestRequest, user: dict = Depends(get_current_user)):
    """Exporter expresses interest in an opportunity"""
    if user["role"] != "exporter":
        raise HTTPException(status_code=403, detail="Only exporters can express interest")
    
    opp = await db.opportunities.find_one({"id": data.opportunity_id}, {"_id": 0})
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    profile = await db.exporter_profiles.find_one({"user_id": user["id"]}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=400, detail="Please create your profile first")
    
    # Check if already expressed interest
    existing = await db.interests.find_one({"opportunity_id": data.opportunity_id, "exporter_id": profile["id"]})
    if existing:
        raise HTTPException(status_code=400, detail="Already expressed interest")
    
    interest_doc = {
        "id": str(uuid.uuid4()),
        "opportunity_id": data.opportunity_id,
        "exporter_id": profile["id"],
        "exporter_user_id": user["id"],
        "indicative_terms": data.indicative_terms,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.interests.insert_one(interest_doc)
    
    return {"message": "Interest expressed successfully"}

@api_router.get("/deals", response_model=List[DealResponse])
async def get_deals(stage: Optional[str] = None, user: dict = Depends(get_current_user)):
    query = {}
    if stage:
        query["stage"] = stage
    
    if user["role"] == "exporter":
        query["exporter_user_id"] = user["id"]
    
    deals = await db.deals.find(query, {"_id": 0}).to_list(100)
    
    result = []
    for d in deals:
        opp = await db.opportunities.find_one({"id": d["opportunity_id"]}, {"_id": 0})
        exporter_profile = await db.exporter_profiles.find_one({"id": d["exporter_id"]}, {"_id": 0})
        exporter_user = await db.users.find_one({"id": d["exporter_user_id"]}, {"_id": 0}) if exporter_profile else None
        
        result.append(DealResponse(
            id=d["id"],
            opportunity_id=d["opportunity_id"],
            exporter_id=d["exporter_id"],
            exporter_company=exporter_user.get("company_name", "Unknown") if exporter_user else "Unknown",
            opportunity_product=opp.get("product_name", "Unknown") if opp else "Unknown",
            stage=d["stage"],
            created_at=d["created_at"],
            updated_at=d["updated_at"]
        ))
    
    return result

@api_router.put("/deals/{deal_id}/stage")
async def update_deal_stage(deal_id: str, stage: str, user: dict = Depends(require_admin)):
    if stage not in PIPELINE_STAGES:
        raise HTTPException(status_code=400, detail=f"Invalid stage. Must be one of: {PIPELINE_STAGES}")
    
    result = await db.deals.update_one(
        {"id": deal_id},
        {"$set": {"stage": stage, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    return {"message": "Stage updated"}

@api_router.get("/interests")
async def get_interests(user: dict = Depends(require_admin)):
    """Get all expressed interests (admin only)"""
    interests = await db.interests.find({}, {"_id": 0}).to_list(100)
    
    result = []
    for i in interests:
        opp = await db.opportunities.find_one({"id": i["opportunity_id"]}, {"_id": 0})
        exporter_profile = await db.exporter_profiles.find_one({"id": i["exporter_id"]}, {"_id": 0})
        exporter_user = await db.users.find_one({"id": i["exporter_user_id"]}, {"_id": 0})
        
        result.append({
            "id": i["id"],
            "opportunity_id": i["opportunity_id"],
            "opportunity_product": opp.get("product_name") if opp else "Unknown",
            "exporter_id": i["exporter_id"],
            "exporter_company": exporter_user.get("company_name") if exporter_user else "Unknown",
            "indicative_terms": i.get("indicative_terms"),
            "created_at": i["created_at"]
        })
    
    return result

@api_router.get("/my-interests")
async def get_my_interests(user: dict = Depends(get_current_user)):
    """Get interests expressed by current exporter"""
    if user["role"] != "exporter":
        raise HTTPException(status_code=403, detail="Only exporters can view their interests")
    
    interests = await db.interests.find({"exporter_user_id": user["id"]}, {"_id": 0}).to_list(100)
    return interests

# ===================== TRADE FINANCE ROUTES =====================

@api_router.post("/finance-requests", response_model=FinanceRequestResponse, status_code=201)
async def create_finance_request(data: FinanceRequestCreate, user: dict = Depends(get_current_user)):
    """Exporter requests financing for a deal"""
    if user["role"] != "exporter":
        raise HTTPException(status_code=403, detail="Only exporters can request financing")
    
    # Check subscription
    if not await check_subscription_valid(user["id"]):
        raise HTTPException(status_code=403, detail="Active subscription required to request financing")
    
    # Verify deal exists and belongs to exporter
    deal = await db.deals.find_one({"id": data.deal_id, "exporter_user_id": user["id"]}, {"_id": 0})
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found or access denied")
    
    # Check if financing already requested
    existing = await db.finance_requests.find_one({"deal_id": data.deal_id})
    if existing:
        raise HTTPException(status_code=400, detail="Financing already requested for this deal")
    
    # Get exporter profile for risk scoring
    profile = await db.exporter_profiles.find_one({"user_id": user["id"]}, {"_id": 0})
    opp = await db.opportunities.find_one({"id": deal["opportunity_id"]}, {"_id": 0})
    
    # Calculate risk score
    exporter_data = {
        "years_in_business": profile.get("years_in_business", 5) if profile else 5,
        "export_turnover": data.past_export_turnover,
        "certifications": profile.get("certifications", []) if profile else [],
        "past_shipments": profile.get("past_shipments", 50) if profile else 50,
        "reliability_score": profile.get("reliability_score", 0.8) if profile else 0.8
    }
    
    deal_data = {
        "deal_value": data.purchase_order_value,
        "buyer_country": data.buyer_country,
        "payment_method": data.payment_method
    }
    
    risk_result = calculate_trade_risk_score(exporter_data, deal_data)
    
    # Store risk score
    risk_id = str(uuid.uuid4())
    risk_doc = {
        "id": risk_id,
        "deal_id": data.deal_id,
        "exporter_id": profile["id"] if profile else user["id"],
        "risk_score": risk_result["risk_score"],
        "risk_category": risk_result["risk_category"],
        "scoring_breakdown": risk_result["scoring_breakdown"],
        "recommended_financing_ratio": risk_result["recommended_financing_ratio"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.risk_scores.insert_one(risk_doc)
    
    # Create finance request
    request_id = str(uuid.uuid4())
    finance_doc = {
        "id": request_id,
        "exporter_id": profile["id"] if profile else user["id"],
        "exporter_user_id": user["id"],
        "deal_id": data.deal_id,
        "purchase_order_value": data.purchase_order_value,
        "financing_amount_requested": data.financing_amount_requested,
        "production_time_days": data.production_time_days,
        "shipment_date": data.shipment_date,
        "buyer_country": data.buyer_country,
        "payment_method": data.payment_method,
        "exporter_bank_details": data.exporter_bank_details,
        "past_export_turnover": data.past_export_turnover,
        "financing_status": "requested",
        "risk_score_id": risk_id,
        "risk_score": risk_result["risk_score"],
        "risk_category": risk_result["risk_category"],
        "nbfc_partner": None,
        "nbfc_offer_amount": None,
        "nbfc_interest_rate": None,
        "admin_notes": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.finance_requests.insert_one(finance_doc)
    
    return FinanceRequestResponse(
        id=request_id,
        exporter_id=finance_doc["exporter_id"],
        exporter_company=user["company_name"],
        deal_id=data.deal_id,
        opportunity_product=opp.get("product_name", "Unknown") if opp else "Unknown",
        purchase_order_value=data.purchase_order_value,
        financing_amount_requested=data.financing_amount_requested,
        production_time_days=data.production_time_days,
        shipment_date=data.shipment_date,
        buyer_country=data.buyer_country,
        payment_method=data.payment_method,
        financing_status="requested",
        risk_score=risk_result["risk_score"],
        risk_category=risk_result["risk_category"],
        created_at=finance_doc["created_at"]
    )

@api_router.get("/finance-requests", response_model=List[FinanceRequestResponse])
async def get_finance_requests(status: Optional[str] = None, user: dict = Depends(get_current_user)):
    """Get financing requests (admin sees all, exporter sees own)"""
    query = {}
    if status:
        query["financing_status"] = status
    
    if user["role"] == "exporter":
        query["exporter_user_id"] = user["id"]
    
    requests = await db.finance_requests.find(query, {"_id": 0}).to_list(100)
    
    result = []
    for req in requests:
        exporter_user = await db.users.find_one({"id": req["exporter_user_id"]}, {"_id": 0})
        deal = await db.deals.find_one({"id": req["deal_id"]}, {"_id": 0})
        opp = await db.opportunities.find_one({"id": deal["opportunity_id"]}, {"_id": 0}) if deal else None
        
        result.append(FinanceRequestResponse(
            id=req["id"],
            exporter_id=req["exporter_id"],
            exporter_company=exporter_user.get("company_name", "Unknown") if exporter_user else "Unknown",
            deal_id=req["deal_id"],
            opportunity_product=opp.get("product_name", "Unknown") if opp else "Unknown",
            purchase_order_value=req["purchase_order_value"],
            financing_amount_requested=req["financing_amount_requested"],
            production_time_days=req["production_time_days"],
            shipment_date=req["shipment_date"],
            buyer_country=req["buyer_country"],
            payment_method=req["payment_method"],
            financing_status=req["financing_status"],
            risk_score=req.get("risk_score"),
            risk_category=req.get("risk_category"),
            nbfc_partner=req.get("nbfc_partner"),
            nbfc_offer_amount=req.get("nbfc_offer_amount"),
            nbfc_interest_rate=req.get("nbfc_interest_rate"),
            admin_notes=req.get("admin_notes"),
            created_at=req["created_at"]
        ))
    
    return result

@api_router.get("/finance-requests/{request_id}", response_model=FinanceRequestResponse)
async def get_finance_request(request_id: str, user: dict = Depends(get_current_user)):
    """Get single financing request"""
    req = await db.finance_requests.find_one({"id": request_id}, {"_id": 0})
    if not req:
        raise HTTPException(status_code=404, detail="Finance request not found")
    
    if user["role"] == "exporter" and req["exporter_user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    exporter_user = await db.users.find_one({"id": req["exporter_user_id"]}, {"_id": 0})
    deal = await db.deals.find_one({"id": req["deal_id"]}, {"_id": 0})
    opp = await db.opportunities.find_one({"id": deal["opportunity_id"]}, {"_id": 0}) if deal else None
    
    return FinanceRequestResponse(
        id=req["id"],
        exporter_id=req["exporter_id"],
        exporter_company=exporter_user.get("company_name", "Unknown") if exporter_user else "Unknown",
        deal_id=req["deal_id"],
        opportunity_product=opp.get("product_name", "Unknown") if opp else "Unknown",
        purchase_order_value=req["purchase_order_value"],
        financing_amount_requested=req["financing_amount_requested"],
        production_time_days=req["production_time_days"],
        shipment_date=req["shipment_date"],
        buyer_country=req["buyer_country"],
        payment_method=req["payment_method"],
        financing_status=req["financing_status"],
        risk_score=req.get("risk_score"),
        risk_category=req.get("risk_category"),
        nbfc_partner=req.get("nbfc_partner"),
        nbfc_offer_amount=req.get("nbfc_offer_amount"),
        nbfc_interest_rate=req.get("nbfc_interest_rate"),
        admin_notes=req.get("admin_notes"),
        created_at=req["created_at"]
    )

@api_router.put("/finance-requests/{request_id}/status")
async def update_finance_status(request_id: str, status: str, user: dict = Depends(require_admin)):
    """Admin updates financing request status"""
    if status not in FINANCING_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {FINANCING_STATUSES}")
    
    result = await db.finance_requests.update_one(
        {"id": request_id},
        {"$set": {"financing_status": status}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Finance request not found")
    
    return {"message": "Status updated"}

@api_router.put("/finance-requests/{request_id}/nbfc-offer")
async def record_nbfc_offer(request_id: str, data: NBFCOfferUpdate, user: dict = Depends(require_admin)):
    """Admin records NBFC offer for a financing request"""
    result = await db.finance_requests.update_one(
        {"id": request_id},
        {"$set": {
            "financing_status": "nbfc_offer_received",
            "nbfc_partner": data.nbfc_partner,
            "nbfc_offer_amount": data.offer_amount,
            "nbfc_interest_rate": data.interest_rate,
            "admin_notes": data.admin_notes
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Finance request not found")
    
    return {"message": "NBFC offer recorded"}

@api_router.post("/finance-requests/{request_id}/accept")
async def accept_nbfc_offer(request_id: str, user: dict = Depends(get_current_user)):
    """Exporter accepts NBFC offer"""
    if user["role"] != "exporter":
        raise HTTPException(status_code=403, detail="Only exporters can accept offers")
    
    req = await db.finance_requests.find_one({"id": request_id, "exporter_user_id": user["id"]}, {"_id": 0})
    if not req:
        raise HTTPException(status_code=404, detail="Finance request not found")
    
    if req["financing_status"] != "nbfc_offer_received":
        raise HTTPException(status_code=400, detail="No NBFC offer to accept")
    
    await db.finance_requests.update_one(
        {"id": request_id},
        {"$set": {"financing_status": "accepted_by_exporter"}}
    )
    
    # Record financing commission (2-4% of loan amount)
    commission_rate = 0.03  # 3%
    commission_amount = req["nbfc_offer_amount"] * commission_rate
    
    revenue_id = str(uuid.uuid4())
    await db.revenue_records.insert_one({
        "id": revenue_id,
        "revenue_type": "financing",
        "exporter_id": req["exporter_id"],
        "deal_id": req["deal_id"],
        "finance_request_id": request_id,
        "amount": commission_amount,
        "loan_amount": req["nbfc_offer_amount"],
        "nbfc_partner": req["nbfc_partner"],
        "status": "pending",
        "description": f"Financing commission ({commission_rate*100}% of ₹{req['nbfc_offer_amount']})",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": "Offer accepted", "financing_commission": commission_amount}

# ===================== RISK SCORING ROUTES =====================

@api_router.get("/risk-scores/{deal_id}", response_model=RiskScoreResponse)
async def get_risk_score(deal_id: str, user: dict = Depends(get_current_user)):
    """Get risk score for a deal"""
    risk = await db.risk_scores.find_one({"deal_id": deal_id}, {"_id": 0})
    if not risk:
        raise HTTPException(status_code=404, detail="Risk score not found")
    
    # Verify access
    if user["role"] == "exporter":
        deal = await db.deals.find_one({"id": deal_id, "exporter_user_id": user["id"]})
        if not deal:
            raise HTTPException(status_code=403, detail="Access denied")
    
    return RiskScoreResponse(**risk)

@api_router.post("/risk-scores/calculate")
async def calculate_risk_score_endpoint(
    deal_id: str,
    finance_profile: ExporterFinanceProfile,
    user: dict = Depends(get_current_user)
):
    """Calculate risk score for a deal"""
    deal = await db.deals.find_one({"id": deal_id}, {"_id": 0})
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    opp = await db.opportunities.find_one({"id": deal["opportunity_id"]}, {"_id": 0})
    profile = await db.exporter_profiles.find_one({"user_id": deal["exporter_user_id"]}, {"_id": 0})
    
    # Parse quantity to get deal value estimate
    qty_str = opp.get("quantity", "1000 MT") if opp else "1000 MT"
    try:
        qty_num = float(''.join(filter(lambda x: x.isdigit() or x == '.', qty_str.split()[0])))
    except:
        qty_num = 1000
    
    deal_value = qty_num * 50000  # Rough estimate per MT
    
    exporter_data = {
        "years_in_business": finance_profile.years_in_business,
        "export_turnover": finance_profile.export_turnover,
        "certifications": profile.get("certifications", []) if profile else [],
        "past_shipments": finance_profile.past_shipments,
        "reliability_score": profile.get("reliability_score", 0.8) if profile else 0.8
    }
    
    deal_data = {
        "deal_value": deal_value,
        "buyer_country": opp.get("source_country", "Nigeria") if opp else "Nigeria",
        "payment_method": "open_account"
    }
    
    result = calculate_trade_risk_score(exporter_data, deal_data)
    return result

# ===================== SUBSCRIPTION ROUTES =====================

@api_router.get("/subscription/me")
async def get_my_subscription(user: dict = Depends(get_current_user)):
    """Get current subscription status"""
    user_doc = await db.users.find_one({"id": user["id"]}, {"_id": 0})
    
    return {
        "plan": user_doc.get("subscription_plan", "Basic"),
        "status": user_doc.get("subscription_status", "active"),
        "expiry": user_doc.get("subscription_expiry"),
        "is_valid": await check_subscription_valid(user["id"])
    }

@api_router.post("/subscription/upgrade")
async def upgrade_subscription(data: SubscriptionUpdate, user: dict = Depends(get_current_user)):
    """Upgrade subscription plan"""
    if data.plan not in SUBSCRIPTION_PLANS:
        raise HTTPException(status_code=400, detail=f"Invalid plan. Must be one of: {SUBSCRIPTION_PLANS}")
    
    expiry_date = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
    
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {
            "subscription_plan": data.plan,
            "subscription_status": "active",
            "subscription_expiry": expiry_date
        }}
    )
    
    # Record subscription revenue
    revenue_id = str(uuid.uuid4())
    await db.revenue_records.insert_one({
        "id": revenue_id,
        "revenue_type": "subscription",
        "exporter_id": user["id"],
        "deal_id": None,
        "amount": SUBSCRIPTION_PRICES.get(data.plan, 9999),
        "status": "completed",
        "description": f"{data.plan} subscription - 1 year",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": f"Upgraded to {data.plan} plan", "expiry": expiry_date}

# ===================== REVENUE ROUTES =====================

@api_router.get("/revenue", response_model=List[RevenueRecordResponse])
async def get_revenue_records(revenue_type: Optional[str] = None, user: dict = Depends(require_admin)):
    """Get all revenue records (admin only)"""
    query = {}
    if revenue_type:
        query["revenue_type"] = revenue_type
    
    records = await db.revenue_records.find(query, {"_id": 0}).to_list(1000)
    return [RevenueRecordResponse(**r) for r in records]

@api_router.get("/revenue/summary")
async def get_revenue_summary(user: dict = Depends(require_admin)):
    """Get revenue summary by type"""
    subscription_total = 0
    deal_total = 0
    financing_total = 0
    
    records = await db.revenue_records.find({}, {"_id": 0}).to_list(1000)
    for r in records:
        if r["revenue_type"] == "subscription":
            subscription_total += r["amount"]
        elif r["revenue_type"] == "deal":
            deal_total += r["amount"]
        elif r["revenue_type"] == "financing":
            financing_total += r["amount"]
    
    return {
        "subscription_revenue": subscription_total,
        "deal_commission_revenue": deal_total,
        "financing_commission_revenue": financing_total,
        "total_revenue": subscription_total + deal_total + financing_total,
        "record_count": len(records)
    }

@api_router.post("/deals/{deal_id}/close")
async def close_deal(deal_id: str, deal_value: float, user: dict = Depends(require_admin)):
    """Close a deal and record commission"""
    deal = await db.deals.find_one({"id": deal_id}, {"_id": 0})
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    # Update deal stage
    await db.deals.update_one(
        {"id": deal_id},
        {"$set": {
            "stage": "Closed",
            "deal_value": deal_value,
            "closed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Record deal commission (1.5% of deal value)
    commission_rate = 0.015
    commission_amount = deal_value * commission_rate
    
    revenue_id = str(uuid.uuid4())
    await db.revenue_records.insert_one({
        "id": revenue_id,
        "revenue_type": "deal",
        "exporter_id": deal["exporter_id"],
        "deal_id": deal_id,
        "amount": commission_amount,
        "deal_value": deal_value,
        "status": "pending",
        "description": f"Deal commission ({commission_rate*100}% of ₹{deal_value})",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": "Deal closed", "commission": commission_amount}

# ===================== STATS ROUTES =====================

@api_router.get("/stats")
async def get_stats(user: dict = Depends(require_admin)):
    total_opportunities = await db.opportunities.count_documents({})
    active_opportunities = await db.opportunities.count_documents({"status": "Active"})
    total_deals = await db.deals.count_documents({})
    total_exporters = await db.exporter_profiles.count_documents({})
    total_interests = await db.interests.count_documents({})
    
    # Stage distribution
    stage_counts = {}
    for stage in PIPELINE_STAGES:
        stage_counts[stage] = await db.deals.count_documents({"stage": stage})
    
    # Sector distribution
    sector_counts = {}
    for sector in SECTORS:
        sector_counts[sector] = await db.opportunities.count_documents({"sector": sector})
    
    return {
        "total_opportunities": total_opportunities,
        "active_opportunities": active_opportunities,
        "total_deals": total_deals,
        "total_exporters": total_exporters,
        "total_interests": total_interests,
        "stage_distribution": stage_counts,
        "sector_distribution": sector_counts
    }

# ===================== SEED DATA =====================

@api_router.post("/seed")
async def seed_data():
    """Seed demo data"""
    # Check if already seeded
    existing = await db.users.find_one({"email": "admin@tradenexus.com"})
    if existing:
        return {"message": "Data already seeded"}
    
    # Create admin
    admin_id = str(uuid.uuid4())
    await db.users.insert_one({
        "id": admin_id,
        "email": "admin@tradenexus.com",
        "password_hash": hash_password("admin123"),
        "company_name": "TradeNexus Principal",
        "role": "admin",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Create exporters
    exporters_data = [
        {"email": "agrimax@export.in", "company": "AgriMax Exports Pvt Ltd", "sectors": ["Agriculture", "Value-Added Agri Products"], "products": ["Basmati Rice", "Wheat", "Dehydrated Onion"], "certs": ["FSSAI", "ISO 22000", "HACCP", "BRC"], "countries": ["Nigeria", "UAE", "Germany"]},
        {"email": "seafresh@export.in", "company": "SeaFresh Marine Ltd", "sectors": ["Marine / Frozen Foods"], "products": ["Frozen Shrimp", "Fish Fillets", "Crab Meat"], "certs": ["FSSAI", "ISO 22000", "HACCP", "Halal"], "countries": ["UAE", "Saudi Arabia", "France"]},
        {"email": "pharmaglobe@export.in", "company": "PharmaGlobe India", "sectors": ["Pharma"], "products": ["Generic Medicines", "APIs", "Formulations"], "certs": ["WHO-GMP", "USFDA", "EU-GMP", "ISO 9001"], "countries": ["Nigeria", "Kenya", "Germany", "UK"]},
        {"email": "chemspec@export.in", "company": "ChemSpec Industries", "sectors": ["Special Chemicals"], "products": ["Agrochemicals", "Industrial Chemicals", "Fertilizers"], "certs": ["ISO 9001", "ISO 14001", "REACH", "MSDS"], "countries": ["Morocco", "Egypt", "Spain"]},
        {"email": "valuefarms@export.in", "company": "Value Farms Agro", "sectors": ["Agriculture", "Value-Added Agri Products"], "products": ["Dried Mango Slices", "Dehydrated Garlic", "Spice Powders"], "certs": ["FSSAI", "ISO 22000", "Halal", "BRC"], "countries": ["UAE", "Qatar", "Netherlands"]}
    ]
    
    for exp in exporters_data:
        exp_id = str(uuid.uuid4())
        expiry_date = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
        await db.users.insert_one({
            "id": exp_id,
            "email": exp["email"],
            "password_hash": hash_password("exporter123"),
            "company_name": exp["company"],
            "role": "exporter",
            "subscription_plan": "Premium",
            "subscription_status": "active",
            "subscription_expiry": expiry_date,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        profile_id = str(uuid.uuid4())
        await db.exporter_profiles.insert_one({
            "id": profile_id,
            "user_id": exp_id,
            "sectors": exp["sectors"],
            "products": exp["products"],
            "capacity": "5000 MT/year",
            "certifications": exp["certs"],
            "country_experience": exp["countries"],
            "reliability_score": 0.85,
            "years_in_business": 8,
            "past_shipments": 75,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    # Create opportunities
    opportunities_data = [
        {"sector": "Agriculture", "country": "Nigeria", "region": "Africa", "product": "Premium Basmati Rice", "hs": "1006.30", "qty": "2000 MT", "timeline": "Q1 2025", "compliance": ["FSSAI", "ISO 22000"], "score": 0.85, "risk": 0.2},
        {"sector": "Marine / Frozen Foods", "country": "UAE", "region": "Middle East", "product": "Frozen Black Tiger Shrimp", "hs": "0306.17", "qty": "500 MT", "timeline": "Feb 2025", "compliance": ["HACCP", "Halal"], "score": 0.9, "risk": 0.15},
        {"sector": "Pharma", "country": "Germany", "region": "Europe", "product": "Paracetamol API", "hs": "2924.29", "qty": "100 MT", "timeline": "Q2 2025", "compliance": ["WHO-GMP", "EU-GMP"], "score": 0.78, "risk": 0.35},
        {"sector": "Special Chemicals", "country": "Morocco", "region": "Africa", "product": "NPK Fertilizer Blend", "hs": "3105.20", "qty": "3000 MT", "timeline": "Mar 2025", "compliance": ["ISO 9001", "MSDS"], "score": 0.72, "risk": 0.28},
        {"sector": "Value-Added Agri Products", "country": "Netherlands", "region": "Europe", "product": "Dehydrated Onion Flakes", "hs": "0712.20", "qty": "200 MT", "timeline": "Q1 2025", "compliance": ["ISO 22000", "BRC"], "score": 0.88, "risk": 0.12},
        {"sector": "Agriculture", "country": "Saudi Arabia", "region": "Middle East", "product": "Indian Wheat Flour", "hs": "1101.00", "qty": "5000 MT", "timeline": "Jan 2025", "compliance": ["FSSAI", "Halal"], "score": 0.82, "risk": 0.22}
    ]
    
    for opp in opportunities_data:
        opp_id = str(uuid.uuid4())
        await db.opportunities.insert_one({
            "id": opp_id,
            "sector": opp["sector"],
            "source_country": opp["country"],
            "region": opp["region"],
            "product_name": opp["product"],
            "hs_code": opp["hs"],
            "quantity": opp["qty"],
            "delivery_timeline": opp["timeline"],
            "compliance_requirements": opp["compliance"],
            "engagement_mode": "Introduction + Negotiation Support",
            "opportunity_score": opp["score"],
            "risk_score": opp["risk"],
            "status": "Active",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": admin_id,
            "matched_exporters": []
        })
    
    return {"message": "Demo data seeded successfully"}

# ===================== BUYER DISCOVERY ROUTES =====================

@api_router.post("/buyers/discover", response_model=List[BuyerResponse])
async def buyers_discover(req: BuyerDiscoverRequest, user: dict = Depends(require_admin)):
    """Run search-grounded buyer discovery for an HS code (+ optional country/product)."""
    if not req.hs_code or not req.hs_code.strip():
        raise HTTPException(status_code=400, detail="hs_code is required")
    if not os.environ.get("TAVILY_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="Buyer discovery unavailable: TAVILY_API_KEY not configured on backend",
        )
    rows = await discover_buyers_for_hs(
        hs_code=req.hs_code.strip(),
        country=(req.country or None),
        product_name=(req.product_name or None),
        max_results=max(1, min(req.max_results, 25)),
    )
    return [BuyerResponse(**r) for r in rows]

@api_router.get("/buyers", response_model=List[BuyerResponse])
async def buyers_list(
    hs_code: Optional[str] = None,
    country: Optional[str] = None,
    verified: Optional[bool] = None,
    limit: int = 100,
    user: dict = Depends(require_admin),
):
    query: dict = {}
    if hs_code:
        query["hs_code"] = hs_code
    if country:
        query["country_lower"] = country.lower()
    if verified is not None:
        query["verified"] = verified
    rows = await db.buyers.find(query, {"_id": 0}).sort("discovered_at", -1).to_list(max(1, min(limit, 500)))
    return [BuyerResponse(**{k: v for k, v in r.items() if k not in ("company_name_lower", "country_lower")}) for r in rows]

@api_router.get("/buyers/{buyer_id}", response_model=BuyerResponse)
async def buyers_get(buyer_id: str, user: dict = Depends(require_admin)):
    row = await db.buyers.find_one({"id": buyer_id}, {"_id": 0})
    if not row:
        raise HTTPException(status_code=404, detail="Buyer not found")
    return BuyerResponse(**{k: v for k, v in row.items() if k not in ("company_name_lower", "country_lower")})

@api_router.put("/buyers/{buyer_id}/verify", response_model=BuyerResponse)
async def buyers_verify(buyer_id: str, body: BuyerVerifyUpdate, user: dict = Depends(require_admin)):
    result = await db.buyers.update_one({"id": buyer_id}, {"$set": {"verified": body.verified}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Buyer not found")
    row = await db.buyers.find_one({"id": buyer_id}, {"_id": 0})
    return BuyerResponse(**{k: v for k, v in row.items() if k not in ("company_name_lower", "country_lower")})

@api_router.delete("/buyers/{buyer_id}")
async def buyers_delete(buyer_id: str, user: dict = Depends(require_admin)):
    result = await db.buyers.delete_one({"id": buyer_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Buyer not found")
    return {"deleted": True}

# ===================== HEALTH CHECK =====================

@api_router.get("/")
async def root():
    return {"message": "TradeNexus AI API", "version": "1.0.0"}

@api_router.get("/health")
async def health():
    return {"status": "healthy"}

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def ensure_indexes():
    try:
        await db.buyers.create_index("hs_code")
        await db.buyers.create_index([("company_name_lower", 1), ("country_lower", 1), ("hs_code", 1)])
    except Exception as e:
        logger.warning(f"Index creation skipped: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
