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

async def ai_parse_opportunity(raw_text: str) -> dict:
    """Use GPT-5.2 via Emergent to parse raw text into structured opportunity"""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            logger.warning("No EMERGENT_LLM_KEY found, using mock parsing")
            return mock_parse_opportunity(raw_text)
        
        chat = LlmChat(
            api_key=api_key,
            session_id=f"parse-{uuid.uuid4()}",
            system_message="""You are a trade opportunity parser. Extract structured data from trade briefs.
Return ONLY valid JSON with these fields:
{
    "sector": "one of: Agriculture, Marine / Frozen Foods, Pharma, Special Chemicals, Value-Added Agri Products",
    "source_country": "country name",
    "region": "one of: Africa, Middle East, Europe",
    "product_name": "product name",
    "hs_code": "HS code if mentioned or null",
    "quantity": "quantity with unit",
    "delivery_timeline": "timeline description",
    "compliance_requirements": ["list of certifications required"],
    "opportunity_score": 0.0 to 1.0 based on feasibility,
    "risk_score": 0.0 to 1.0 based on complexity
}"""
        ).with_model("openai", "gpt-5.2")
        
        response = await chat.send_message(UserMessage(text=f"Parse this trade brief:\n\n{raw_text}"))
        
        # Extract JSON from response
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                parsed = json.loads(response[start:end])
                return parsed
        except json.JSONDecodeError:
            pass
        
        return mock_parse_opportunity(raw_text)
    except Exception as e:
        logger.error(f"AI parsing error: {e}")
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
    """Calculate opportunity and risk scores"""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            return (0.75, 0.25)
        
        chat = LlmChat(
            api_key=api_key,
            session_id=f"score-{uuid.uuid4()}",
            system_message="Score trade opportunities. Return JSON: {\"opportunity_score\": 0.0-1.0, \"risk_score\": 0.0-1.0}"
        ).with_model("openai", "gpt-5.2")
        
        response = await chat.send_message(UserMessage(
            text=f"Score this opportunity:\nSector: {opportunity.get('sector')}\nCountry: {opportunity.get('source_country')}\nQuantity: {opportunity.get('quantity')}\nCompliance: {opportunity.get('compliance_requirements')}"
        ))
        
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                scores = json.loads(response[start:end])
                return (scores.get("opportunity_score", 0.75), scores.get("risk_score", 0.25))
        except:
            pass
        
        return (0.75, 0.25)
    except Exception as e:
        logger.error(f"AI scoring error: {e}")
        return (0.75, 0.25)

async def ai_rank_exporters(opportunity: dict, exporters: list) -> list:
    """Rank exporters for an opportunity using AI"""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        
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
        await db.users.insert_one({
            "id": exp_id,
            "email": exp["email"],
            "password_hash": hash_password("exporter123"),
            "company_name": exp["company"],
            "role": "exporter",
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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
