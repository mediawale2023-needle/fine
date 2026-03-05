from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import json
import hashlib
import hmac
import base64
import httpx

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

SECTORS = [
    "Agriculture",
    "Marine / Frozen Foods",
    "Pharma & Life Sciences",
    "Chemicals & Petrochemicals",
    "Textiles & Apparel",
    "Engineering & Machinery",
    "Electronics & Technology",
    "Auto Components",
    "Food & Beverages",
    "Gems & Jewellery",
    "Leather & Footwear",
    "Plastics & Rubber",
    "Paper & Wood Products",
    "Construction Materials",
    "Handicrafts & Artisans",
    "Special Chemicals",
    "Value-Added Agri Products",
]
REGIONS = ["Africa", "Middle East", "Europe", "Asia Pacific", "North America", "South America", "Central Asia"]

HS_CODES_BY_SECTOR = {
    "Agriculture": [
        {"code": "1001", "label": "1001 - Wheat"},
        {"code": "1006", "label": "1006 - Rice"},
        {"code": "1201", "label": "1201 - Soybeans"},
        {"code": "0901", "label": "0901 - Coffee"},
        {"code": "0902", "label": "0902 - Tea"},
        {"code": "0701", "label": "0701 - Potatoes"},
        {"code": "0803", "label": "0803 - Bananas"},
        {"code": "0806", "label": "0806 - Grapes"},
        {"code": "1005", "label": "1005 - Maize (Corn)"},
        {"code": "1507", "label": "1507 - Soybean Oil"},
        {"code": "1701", "label": "1701 - Cane Sugar"},
        {"code": "2401", "label": "2401 - Tobacco"},
        {"code": "0401", "label": "0401 - Milk & Cream"},
    ],
    "Marine / Frozen Foods": [
        {"code": "0302", "label": "0302 - Fresh Fish"},
        {"code": "0303", "label": "0303 - Frozen Fish"},
        {"code": "0304", "label": "0304 - Fish Fillets"},
        {"code": "0305", "label": "0305 - Dried/Salted Fish"},
        {"code": "0306", "label": "0306 - Crustaceans (Shrimp/Crab)"},
        {"code": "0307", "label": "0307 - Molluscs (Squid/Octopus)"},
        {"code": "1604", "label": "1604 - Prepared/Preserved Fish"},
        {"code": "1605", "label": "1605 - Prepared Crustaceans"},
    ],
    "Pharma & Life Sciences": [
        {"code": "3004", "label": "3004 - Medicaments (Packaged)"},
        {"code": "3003", "label": "3003 - Medicaments (Mixed)"},
        {"code": "3002", "label": "3002 - Blood / Vaccines"},
        {"code": "2941", "label": "2941 - Antibiotics"},
        {"code": "2936", "label": "2936 - Vitamins"},
        {"code": "2924", "label": "2924 - API (Paracetamol etc.)"},
        {"code": "3005", "label": "3005 - Medical Dressings"},
        {"code": "3006", "label": "3006 - Pharmaceutical Goods"},
        {"code": "9018", "label": "9018 - Medical Instruments"},
    ],
    "Chemicals & Petrochemicals": [
        {"code": "2710", "label": "2710 - Petroleum Oils"},
        {"code": "2709", "label": "2709 - Crude Petroleum"},
        {"code": "2814", "label": "2814 - Ammonia"},
        {"code": "2815", "label": "2815 - Sodium Hydroxide (NaOH)"},
        {"code": "2901", "label": "2901 - Acyclic Hydrocarbons"},
        {"code": "2902", "label": "2902 - Cyclic Hydrocarbons"},
        {"code": "3105", "label": "3105 - Fertilizers (NPK)"},
        {"code": "3901", "label": "3901 - Polyethylene"},
        {"code": "3902", "label": "3902 - Polypropylene"},
        {"code": "3904", "label": "3904 - PVC"},
        {"code": "2804", "label": "2804 - Hydrogen / Noble Gases"},
    ],
    "Special Chemicals": [
        {"code": "2801", "label": "2801 - Halogens"},
        {"code": "2807", "label": "2807 - Sulphuric Acid"},
        {"code": "2811", "label": "2811 - Other Inorganic Acids"},
        {"code": "2903", "label": "2903 - Halogenated Hydrocarbons"},
        {"code": "3204", "label": "3204 - Synthetic Dyes"},
        {"code": "3205", "label": "3205 - Colour Lakes"},
        {"code": "3206", "label": "3206 - Pigments / Colouring"},
        {"code": "3402", "label": "3402 - Surface-Active Agents"},
        {"code": "3808", "label": "3808 - Pesticides"},
    ],
    "Textiles & Apparel": [
        {"code": "5201", "label": "5201 - Cotton (not carded)"},
        {"code": "5208", "label": "5208 - Woven Cotton Fabrics"},
        {"code": "5407", "label": "5407 - Woven Synthetic Yarn Fabrics"},
        {"code": "6109", "label": "6109 - T-Shirts / Vests"},
        {"code": "6110", "label": "6110 - Jerseys / Sweaters"},
        {"code": "6203", "label": "6203 - Men's Suits / Trousers"},
        {"code": "6204", "label": "6204 - Women's Suits / Dresses"},
        {"code": "6302", "label": "6302 - Bed Linen"},
        {"code": "6304", "label": "6304 - Furnishing Articles"},
        {"code": "6402", "label": "6402 - Footwear (Rubber/Plastic)"},
    ],
    "Engineering & Machinery": [
        {"code": "8408", "label": "8408 - Diesel Engines"},
        {"code": "8413", "label": "8413 - Pumps for Liquids"},
        {"code": "8414", "label": "8414 - Air / Vacuum Pumps"},
        {"code": "8419", "label": "8419 - Heat Treatment Machinery"},
        {"code": "8421", "label": "8421 - Centrifuges / Filters"},
        {"code": "8428", "label": "8428 - Lifting / Loading Machinery"},
        {"code": "8443", "label": "8443 - Printing Machinery"},
        {"code": "8477", "label": "8477 - Rubber/Plastics Machinery"},
        {"code": "8501", "label": "8501 - Electric Motors"},
        {"code": "8502", "label": "8502 - Electric Generators"},
    ],
    "Electronics & Technology": [
        {"code": "8517", "label": "8517 - Telephones / Smartphones"},
        {"code": "8471", "label": "8471 - Computers / Laptops"},
        {"code": "8504", "label": "8504 - Electrical Transformers"},
        {"code": "8523", "label": "8523 - Storage Media"},
        {"code": "8525", "label": "8525 - Transmission Apparatus"},
        {"code": "8528", "label": "8528 - Monitors / Projectors"},
        {"code": "8541", "label": "8541 - Diodes / Transistors"},
        {"code": "8542", "label": "8542 - Electronic Integrated Circuits"},
        {"code": "8544", "label": "8544 - Insulated Wire / Cable"},
        {"code": "8534", "label": "8534 - Printed Circuit Boards"},
    ],
    "Auto Components": [
        {"code": "8708", "label": "8708 - Car Parts & Accessories"},
        {"code": "8706", "label": "8706 - Chassis for Vehicles"},
        {"code": "8483", "label": "8483 - Transmission Shafts / Gears"},
        {"code": "8507", "label": "8507 - Electric Accumulators / Batteries"},
        {"code": "4011", "label": "4011 - New Pneumatic Tyres"},
        {"code": "8409", "label": "8409 - Engine Parts"},
        {"code": "8407", "label": "8407 - Spark-Ignition Engines"},
        {"code": "8714", "label": "8714 - Motorcycle Parts"},
        {"code": "8716", "label": "8716 - Trailers / Semi-Trailers"},
    ],
    "Food & Beverages": [
        {"code": "1602", "label": "1602 - Prepared / Preserved Meat"},
        {"code": "1704", "label": "1704 - Sugar Confectionery"},
        {"code": "1806", "label": "1806 - Chocolate Products"},
        {"code": "1902", "label": "1902 - Pasta / Noodles"},
        {"code": "1905", "label": "1905 - Bread / Pastries / Biscuits"},
        {"code": "2009", "label": "2009 - Fruit / Vegetable Juices"},
        {"code": "2106", "label": "2106 - Food Preparations"},
        {"code": "2202", "label": "2202 - Non-Alcoholic Beverages"},
        {"code": "2203", "label": "2203 - Beer"},
        {"code": "2204", "label": "2204 - Wine"},
        {"code": "2208", "label": "2208 - Spirits / Liquors"},
        {"code": "2101", "label": "2101 - Coffee / Tea Extracts"},
    ],
    "Value-Added Agri Products": [
        {"code": "0712", "label": "0712 - Dried Vegetables"},
        {"code": "0904", "label": "0904 - Pepper / Spices"},
        {"code": "0910", "label": "0910 - Ginger / Turmeric / Spices"},
        {"code": "1101", "label": "1101 - Wheat / Meslin Flour"},
        {"code": "1102", "label": "1102 - Cereal Flours (Non-Wheat)"},
        {"code": "1108", "label": "1108 - Starch"},
        {"code": "1515", "label": "1515 - Other Vegetable Oils"},
        {"code": "2001", "label": "2001 - Vegetables in Vinegar"},
        {"code": "2002", "label": "2002 - Tomatoes Prepared"},
        {"code": "2008", "label": "2008 - Other Prepared Fruits / Nuts"},
        {"code": "1209", "label": "1209 - Seeds for Sowing"},
    ],
    "Gems & Jewellery": [
        {"code": "7102", "label": "7102 - Diamonds"},
        {"code": "7103", "label": "7103 - Precious / Semi-Precious Stones"},
        {"code": "7106", "label": "7106 - Silver"},
        {"code": "7108", "label": "7108 - Gold"},
        {"code": "7110", "label": "7110 - Platinum"},
        {"code": "7113", "label": "7113 - Articles of Jewellery"},
        {"code": "7114", "label": "7114 - Articles of Goldsmiths"},
        {"code": "7117", "label": "7117 - Imitation Jewellery"},
        {"code": "7101", "label": "7101 - Pearls"},
    ],
    "Leather & Footwear": [
        {"code": "4104", "label": "4104 - Tanned Bovine Leather"},
        {"code": "4107", "label": "4107 - Full-Grain Leather"},
        {"code": "6403", "label": "6403 - Footwear with Leather Uppers"},
        {"code": "6404", "label": "6404 - Footwear with Textile Uppers"},
        {"code": "6401", "label": "6401 - Waterproof Footwear"},
        {"code": "4202", "label": "4202 - Travel Goods / Handbags"},
        {"code": "4203", "label": "4203 - Articles of Leather"},
        {"code": "4101", "label": "4101 - Raw Bovine / Equine Hides"},
    ],
    "Plastics & Rubber": [
        {"code": "3901", "label": "3901 - Polyethylene"},
        {"code": "3902", "label": "3902 - Polypropylene"},
        {"code": "3903", "label": "3903 - Polystyrene"},
        {"code": "3904", "label": "3904 - PVC"},
        {"code": "3907", "label": "3907 - Polyesters"},
        {"code": "3917", "label": "3917 - Plastic Tubes / Pipes"},
        {"code": "3923", "label": "3923 - Plastic Containers"},
        {"code": "3926", "label": "3926 - Other Plastic Articles"},
        {"code": "4002", "label": "4002 - Synthetic Rubber"},
        {"code": "4016", "label": "4016 - Other Rubber Articles"},
    ],
    "Paper & Wood Products": [
        {"code": "4403", "label": "4403 - Wood in the Rough"},
        {"code": "4407", "label": "4407 - Wood Sawn / Chipped"},
        {"code": "4412", "label": "4412 - Plywood"},
        {"code": "4418", "label": "4418 - Builders Joinery (Doors/Windows)"},
        {"code": "4802", "label": "4802 - Uncoated Paper"},
        {"code": "4810", "label": "4810 - Paper Coated with Kaolin"},
        {"code": "4819", "label": "4819 - Cartons / Boxes"},
        {"code": "4821", "label": "4821 - Paper Labels"},
        {"code": "4701", "label": "4701 - Mechanical Wood Pulp"},
    ],
    "Construction Materials": [
        {"code": "2523", "label": "2523 - Portland Cement"},
        {"code": "2515", "label": "2515 - Marble / Travertine"},
        {"code": "2516", "label": "2516 - Granite / Basalt"},
        {"code": "6907", "label": "6907 - Ceramic Tiles / Flags"},
        {"code": "6901", "label": "6901 - Bricks / Tiles (Fired)"},
        {"code": "7214", "label": "7214 - Iron / Steel Bars"},
        {"code": "7308", "label": "7308 - Structures of Iron / Steel"},
        {"code": "7610", "label": "7610 - Aluminium Structures"},
        {"code": "6810", "label": "6810 - Articles of Cement / Concrete"},
        {"code": "7010", "label": "7010 - Glass Containers"},
    ],
    "Handicrafts & Artisans": [
        {"code": "4420", "label": "4420 - Wood Carvings / Marquetry"},
        {"code": "5701", "label": "5701 - Knotted Carpets / Rugs"},
        {"code": "5702", "label": "5702 - Woven Carpets"},
        {"code": "6913", "label": "6913 - Ceramic Ornaments / Statuettes"},
        {"code": "9701", "label": "9701 - Paintings / Drawings"},
        {"code": "9703", "label": "9703 - Sculptures / Statuary"},
        {"code": "6304", "label": "6304 - Furnishing Articles (Handmade)"},
        {"code": "9602", "label": "9602 - Worked Vegetable / Mineral Materials"},
    ],
}
ENGAGEMENT_MODES = ["Introduction-only", "Introduction + Negotiation Support"]
PIPELINE_STAGES = ["Received", "Interest", "Shortlisted", "Introduction", "Negotiation", "Closed"]

# Razorpay config
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "rzp_test_placeholder")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "placeholder_secret")

# NBFC partner configuration
NBFC_PARTNERS = {
    "credlix": {
        "name": "Credlix",
        "api_url": os.environ.get("CREDLIX_API_URL", ""),
        "api_key": os.environ.get("CREDLIX_API_KEY", ""),
        "commission_rate": 0.02,
    },
    "drip_capital": {
        "name": "Drip Capital",
        "api_url": os.environ.get("DRIP_CAPITAL_API_URL", ""),
        "api_key": os.environ.get("DRIP_CAPITAL_API_KEY", ""),
        "commission_rate": 0.018,
    },
    "vayana": {
        "name": "Vayana Network",
        "api_url": os.environ.get("VAYANA_API_URL", ""),
        "api_key": os.environ.get("VAYANA_API_KEY", ""),
        "commission_rate": 0.022,
    },
}

# WhatsApp / Twilio config
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.environ.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

CERTIFICATIONS = {
    "Agriculture": ["FSSAI", "ISO 22000", "HACCP", "BRC", "Halal", "Organic", "GlobalG.A.P."],
    "Marine / Frozen Foods": ["FSSAI", "ISO 22000", "HACCP", "BRC", "Halal", "MSC", "ASC"],
    "Pharma & Life Sciences": ["WHO-GMP", "USFDA", "EU-GMP", "ISO 9001", "ISO 13485", "GLP"],
    "Chemicals & Petrochemicals": ["ISO 9001", "ISO 14001", "REACH", "MSDS", "ADR", "ISO 45001"],
    "Special Chemicals": ["ISO 9001", "ISO 14001", "REACH", "MSDS", "ADR"],
    "Textiles & Apparel": ["OEKO-TEX", "GOTS", "ISO 9001", "SA8000", "BCI"],
    "Engineering & Machinery": ["ISO 9001", "CE Mark", "ISO 14001", "ISO 45001", "BIS"],
    "Electronics & Technology": ["CE Mark", "RoHS", "ISO 9001", "FCC", "BIS"],
    "Auto Components": ["ISO 9001", "IATF 16949", "CE Mark", "BIS", "AIS"],
    "Food & Beverages": ["FSSAI", "ISO 22000", "HACCP", "BRC", "Halal", "Kosher", "FDA"],
    "Value-Added Agri Products": ["FSSAI", "ISO 22000", "HACCP", "BRC", "Halal", "Organic"],
    "Gems & Jewellery": ["ISO 9001", "BIS Hallmark", "Kimberley Process", "RJC"],
    "Leather & Footwear": ["ISO 9001", "LWG", "REACH", "SA8000"],
    "Plastics & Rubber": ["ISO 9001", "REACH", "RoHS", "ISO 14001"],
    "Paper & Wood Products": ["ISO 9001", "FSC", "PEFC", "ISO 14001"],
    "Construction Materials": ["ISO 9001", "CE Mark", "BIS", "ISO 14001"],
    "Handicrafts & Artisans": ["ISO 9001", "Fair Trade", "EPCH"],
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

# ---- Buyer Models ----
class BuyerProfileCreate(BaseModel):
    company_name: str
    country: str
    industry: str
    annual_import_volume: Optional[str] = None
    preferred_sectors: List[str] = []

class BuyerProfileResponse(BaseModel):
    id: str
    user_id: str
    company_name: str
    country: str
    industry: str
    annual_import_volume: Optional[str] = None
    preferred_sectors: List[str] = []
    verified: bool = False
    created_at: str

class BuyerRFQCreate(BaseModel):
    product_name: str
    sector: str
    quantity: str
    delivery_country: str
    region: str
    delivery_timeline: str
    compliance_requirements: List[str] = []
    hs_code: Optional[str] = None
    budget_range: Optional[str] = None
    notes: Optional[str] = None

class BuyerRFQResponse(BaseModel):
    id: str
    buyer_id: str
    buyer_company: str
    product_name: str
    sector: str
    quantity: str
    delivery_country: str
    region: str
    delivery_timeline: str
    compliance_requirements: List[str]
    hs_code: Optional[str] = None
    budget_range: Optional[str] = None
    notes: Optional[str] = None
    status: str
    listing_fee_paid: bool = False
    matched_exporters: List[dict] = []
    created_at: str

# ---- Deal Room / Messaging Models ----
class MessageCreate(BaseModel):
    content: str
    attachment_url: Optional[str] = None
    attachment_name: Optional[str] = None

class MessageResponse(BaseModel):
    id: str
    deal_id: str
    sender_id: str
    sender_name: str
    sender_role: str
    content: str
    attachment_url: Optional[str] = None
    attachment_name: Optional[str] = None
    read_by: List[str] = []
    created_at: str

# ---- Document Models ----
class DocumentResponse(BaseModel):
    id: str
    deal_id: Optional[str] = None
    uploaded_by: str
    filename: str
    doc_type: str
    parsed_data: Optional[dict] = None
    url: Optional[str] = None
    created_at: str

# ---- Razorpay Models ----
class PaymentOrderCreate(BaseModel):
    plan: str

class PaymentVerify(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    plan: str

# ---- NBFC Automation Models ----
class NBFCSubmitResponse(BaseModel):
    request_id: str
    submitted_to: List[str]
    message: str

class NBFCOfferWebhook(BaseModel):
    nbfc_partner: str
    request_id: str
    offer_amount: float
    interest_rate: float
    tenure_months: int
    processing_fee: float
    notes: Optional[str] = None

# ---- Market Intelligence Models ----
class SectorInsightResponse(BaseModel):
    sector: str
    total_opportunities: int
    total_deals: int
    avg_deal_value_inr: float
    top_markets: List[dict]
    avg_time_to_close_days: float
    win_rate: float
    compliance_frequency: List[dict]

class MarketInsightResponse(BaseModel):
    country: str
    region: str
    total_opportunities: int
    top_sectors: List[dict]
    avg_quantity: str
    typical_compliance: List[str]

class PlatformOverviewResponse(BaseModel):
    total_opportunities: int
    total_deals: int
    total_exporters: int
    total_buyers: int
    closed_deals: int
    total_revenue_inr: float
    sector_breakdown: List[dict]
    region_breakdown: List[dict]
    monthly_trend: List[dict]

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

async def require_exporter(user: dict = Depends(get_current_user)):
    if user.get("role") != "exporter":
        raise HTTPException(status_code=403, detail="Exporter access required")
    return user

async def require_buyer(user: dict = Depends(get_current_user)):
    if user.get("role") != "buyer":
        raise HTTPException(status_code=403, detail="Buyer access required")
    return user

# ===================== AI SERVICE =====================

async def ai_parse_opportunity(raw_text: str) -> dict:
    """Parse raw text into structured opportunity using keyword matching."""
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
    """Calculate opportunity and risk scores based on sector and country."""
    sector = opportunity.get("sector", "")
    country = opportunity.get("source_country", "")
    risk = COUNTRY_RISK_SCORES.get(country, 30) / 100.0
    score = max(0.5, 1.0 - risk * 0.5)
    return (round(score, 2), round(risk, 2))

async def ai_rank_exporters(opportunity: dict, exporters: list) -> list:
    """Rank exporters for an opportunity using rule-based scoring."""
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

# ===================== WHATSAPP NOTIFICATION SERVICE =====================

async def send_whatsapp_notification(phone: str, message: str):
    """Send WhatsApp notification via Twilio. Silently skips if credentials not configured."""
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        logger.info(f"WhatsApp (mock) → {phone}: {message[:80]}")
        return
    try:
        async with httpx.AsyncClient() as client_http:
            await client_http.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json",
                auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
                data={
                    "From": TWILIO_WHATSAPP_FROM,
                    "To": f"whatsapp:{phone}",
                    "Body": message,
                },
                timeout=10,
            )
    except Exception as e:
        logger.warning(f"WhatsApp notification failed: {e}")

async def notify_deal_stage_change(deal_id: str, new_stage: str):
    """Notify exporter via WhatsApp when deal stage changes."""
    deal = await db.deals.find_one({"id": deal_id}, {"_id": 0})
    if not deal:
        return
    user = await db.users.find_one({"id": deal.get("exporter_user_id")}, {"_id": 0})
    if not user or not user.get("whatsapp_phone"):
        return
    opp = await db.opportunities.find_one({"id": deal.get("opportunity_id")}, {"_id": 0})
    product = opp.get("product_name", "your deal") if opp else "your deal"
    msg = (
        f"🚀 TradeNexus Update\n\n"
        f"Your deal for *{product}* has moved to stage: *{new_stage}*\n\n"
        f"Login to TradeNexus to view details and take action."
    )
    await send_whatsapp_notification(user["whatsapp_phone"], msg)

async def notify_nbfc_offer_received(finance_request_id: str):
    """Notify exporter when NBFC offer arrives."""
    req = await db.finance_requests.find_one({"id": finance_request_id}, {"_id": 0})
    if not req:
        return
    user = await db.users.find_one({"id": req.get("exporter_id")}, {"_id": 0})
    if not user or not user.get("whatsapp_phone"):
        return
    msg = (
        f"💰 TradeNexus — Financing Offer Ready\n\n"
        f"An NBFC has made an offer on your financing request.\n"
        f"*Partner:* {req.get('nbfc_partner', 'NBFC')}\n"
        f"*Amount:* ₹{req.get('nbfc_offer_amount', 0):,.0f}\n"
        f"*Rate:* {req.get('nbfc_interest_rate', 0)}% p.a.\n\n"
        f"Login to TradeNexus to accept or reject."
    )
    await send_whatsapp_notification(user["whatsapp_phone"], msg)

async def notify_new_opportunity_matched(exporter_user_id: str, product_name: str, opportunity_id: str):
    """Notify exporter about a new matched opportunity."""
    user = await db.users.find_one({"id": exporter_user_id}, {"_id": 0})
    if not user or not user.get("whatsapp_phone"):
        return
    msg = (
        f"🌍 TradeNexus — New Opportunity\n\n"
        f"A new opportunity matching your profile is available:\n"
        f"*Product:* {product_name}\n\n"
        f"Reply *1* to Express Interest or login to TradeNexus."
    )
    await send_whatsapp_notification(user["whatsapp_phone"], msg)

# ===================== AI DOCUMENT PARSER =====================

async def ai_parse_document(content: str, doc_hint: str = "") -> dict:
    """Parse trade documents (LC, Invoice, BL) using keyword matching."""
    return _mock_document_parse(content, doc_hint)

def _mock_document_parse(content: str, doc_hint: str = "") -> dict:
    content_lower = content.lower()
    doc_type = "Invoice"
    if "letter of credit" in content_lower or "l/c" in content_lower or "lc no" in content_lower:
        doc_type = "LC"
    elif "bill of lading" in content_lower or "b/l" in content_lower:
        doc_type = "Bill of Lading"
    elif "certificate" in content_lower:
        doc_type = "Certificate of Origin"
    return {
        "doc_type": doc_type,
        "product_name": "Agricultural Products",
        "hs_code": None,
        "quantity": "1000 MT",
        "value_usd": 500000,
        "buyer_name": "International Trading Co.",
        "seller_name": "Indian Exports Ltd.",
        "origin_country": "India",
        "destination_country": "UAE",
        "delivery_date": "2025-03-31",
        "payment_terms": "LC at sight",
        "compliance_requirements": ["FSSAI", "ISO 22000"],
        "currency": "USD",
        "key_notes": "Parsed by mock parser. Upload real document for accurate extraction.",
    }

# ===================== SECTORS & HS CODE REFERENCE ROUTE =====================

@api_router.get("/sectors-data")
async def get_sectors_data():
    """Return all sectors, regions, HS codes per sector, and certifications per sector."""
    return {
        "sectors": SECTORS,
        "regions": REGIONS,
        "hs_codes_by_sector": HS_CODES_BY_SECTOR,
        "certifications_by_sector": CERTIFICATIONS,
    }

# ===================== AUTH ROUTES =====================

@api_router.post("/auth/register", response_model=TokenResponse, status_code=201)
async def register(data: UserCreate):
    existing = await db.users.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if data.role not in ["admin", "exporter", "buyer"]:
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

    await notify_deal_stage_change(deal_id, stage)
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

# ===================== RAZORPAY PAYMENT ROUTES =====================

@api_router.post("/payments/create-order")
async def create_payment_order(data: PaymentOrderCreate, user: dict = Depends(require_exporter)):
    """Create a Razorpay order for subscription payment."""
    plan = data.plan
    if plan not in SUBSCRIPTION_PLANS:
        raise HTTPException(status_code=400, detail=f"Invalid plan. Must be one of: {SUBSCRIPTION_PLANS}")

    amount_paise = SUBSCRIPTION_PRICES.get(plan, 9999) * 100  # Razorpay uses paise

    # If Razorpay keys are configured, create real order; otherwise return mock
    if RAZORPAY_KEY_ID and RAZORPAY_KEY_ID != "rzp_test_placeholder":
        try:
            import razorpay
            rz_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
            order = rz_client.order.create({
                "amount": amount_paise,
                "currency": "INR",
                "notes": {"plan": plan, "user_id": user["id"]},
            })
            return {
                "order_id": order["id"],
                "amount": amount_paise,
                "currency": "INR",
                "plan": plan,
                "key_id": RAZORPAY_KEY_ID,
            }
        except Exception as e:
            logger.error(f"Razorpay order creation failed: {e}")
            raise HTTPException(status_code=500, detail="Payment gateway error")

    # Mock order for development/testing
    mock_order_id = f"order_mock_{uuid.uuid4().hex[:16]}"
    return {
        "order_id": mock_order_id,
        "amount": amount_paise,
        "currency": "INR",
        "plan": plan,
        "key_id": RAZORPAY_KEY_ID,
        "mock": True,
    }

@api_router.post("/payments/verify")
async def verify_payment(data: PaymentVerify, user: dict = Depends(require_exporter)):
    """Verify Razorpay payment signature and activate subscription."""
    plan = data.plan
    if plan not in SUBSCRIPTION_PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan")

    # Verify signature (skip for mock orders)
    is_mock = data.razorpay_order_id.startswith("order_mock_")
    if not is_mock:
        expected_sig = hmac.new(
            RAZORPAY_KEY_SECRET.encode(),
            f"{data.razorpay_order_id}|{data.razorpay_payment_id}".encode(),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected_sig, data.razorpay_signature):
            raise HTTPException(status_code=400, detail="Invalid payment signature")

    # Activate subscription
    expiry_date = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {
            "subscription_plan": plan,
            "subscription_status": "active",
            "subscription_expiry": expiry_date,
        }}
    )

    # Record revenue
    revenue_id = str(uuid.uuid4())
    await db.revenue_records.insert_one({
        "id": revenue_id,
        "revenue_type": "subscription",
        "exporter_id": user["id"],
        "amount": SUBSCRIPTION_PRICES.get(plan, 9999),
        "description": f"{plan} subscription - 1 year",
        "razorpay_order_id": data.razorpay_order_id,
        "razorpay_payment_id": data.razorpay_payment_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    return {
        "message": "Subscription activated",
        "plan": plan,
        "expiry": expiry_date,
    }

# ===================== BUYER PORTAL ROUTES =====================

@api_router.post("/buyer/profile", response_model=BuyerProfileResponse, status_code=201)
async def create_buyer_profile(data: BuyerProfileCreate, user: dict = Depends(require_buyer)):
    existing = await db.buyer_profiles.find_one({"user_id": user["id"]})
    if existing:
        raise HTTPException(status_code=400, detail="Profile already exists")

    profile_id = str(uuid.uuid4())
    doc = {
        "id": profile_id,
        "user_id": user["id"],
        "company_name": data.company_name,
        "country": data.country,
        "industry": data.industry,
        "annual_import_volume": data.annual_import_volume,
        "preferred_sectors": data.preferred_sectors,
        "verified": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.buyer_profiles.insert_one(doc)
    return BuyerProfileResponse(**{k: v for k, v in doc.items() if k != "_id"})

@api_router.get("/buyer/profile", response_model=BuyerProfileResponse)
async def get_buyer_profile(user: dict = Depends(require_buyer)):
    profile = await db.buyer_profiles.find_one({"user_id": user["id"]}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return BuyerProfileResponse(**profile)

@api_router.put("/buyer/profile", response_model=BuyerProfileResponse)
async def update_buyer_profile(data: BuyerProfileCreate, user: dict = Depends(require_buyer)):
    result = await db.buyer_profiles.update_one(
        {"user_id": user["id"]},
        {"$set": data.model_dump()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Profile not found. Create it first.")
    profile = await db.buyer_profiles.find_one({"user_id": user["id"]}, {"_id": 0})
    return BuyerProfileResponse(**profile)

@api_router.post("/buyer/rfqs", response_model=BuyerRFQResponse, status_code=201)
async def create_buyer_rfq(data: BuyerRFQCreate, user: dict = Depends(require_buyer)):
    """Buyer posts a new RFQ. Auto-scores and matches exporters."""
    profile = await db.buyer_profiles.find_one({"user_id": user["id"]}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=400, detail="Please complete your buyer profile first")

    opp_score, risk_score = await ai_score_opportunity(data.model_dump())

    rfq_id = str(uuid.uuid4())
    rfq_doc = {
        "id": rfq_id,
        "buyer_id": user["id"],
        "buyer_company": user["company_name"],
        "product_name": data.product_name,
        "sector": data.sector,
        "quantity": data.quantity,
        "delivery_country": data.delivery_country,
        "region": data.region,
        "delivery_timeline": data.delivery_timeline,
        "compliance_requirements": data.compliance_requirements,
        "hs_code": data.hs_code,
        "budget_range": data.budget_range,
        "notes": data.notes,
        "opportunity_score": opp_score,
        "risk_score": risk_score,
        "status": "Active",
        "listing_fee_paid": False,
        "matched_exporters": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": "buyer_portal",
    }
    await db.buyer_rfqs.insert_one(rfq_doc)

    # Also insert into main opportunities collection so exporters can see it
    opp_doc = {
        "id": rfq_id,
        "sector": data.sector,
        "source_country": data.delivery_country,
        "region": data.region,
        "product_name": data.product_name,
        "hs_code": data.hs_code,
        "quantity": data.quantity,
        "delivery_timeline": data.delivery_timeline,
        "compliance_requirements": data.compliance_requirements,
        "engagement_mode": "Introduction + Negotiation Support",
        "opportunity_score": opp_score,
        "risk_score": risk_score,
        "status": "Active",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user["id"],
        "buyer_rfq": True,
        "matched_exporters": [],
    }
    await db.opportunities.insert_one(opp_doc)

    # Auto-run matchmaking
    profiles = await db.exporter_profiles.find({}, {"_id": 0}).to_list(100)
    for p in profiles:
        u = await db.users.find_one({"id": p["user_id"]}, {"_id": 0})
        if u:
            p["company_name"] = u.get("company_name", "Unknown")
    ranked = await ai_rank_exporters(rfq_doc, profiles)
    matched = [{"exporter_id": e["id"], "company_name": e.get("company_name"), "match_score": e.get("match_score", 0)} for e in ranked]
    await db.buyer_rfqs.update_one({"id": rfq_id}, {"$set": {"matched_exporters": matched}})
    await db.opportunities.update_one({"id": rfq_id}, {"$set": {"matched_exporters": matched}})

    # Notify matched exporters via WhatsApp
    for match in matched[:3]:
        exporter_profile = await db.exporter_profiles.find_one({"id": match["exporter_id"]}, {"_id": 0})
        if exporter_profile:
            await notify_new_opportunity_matched(exporter_profile["user_id"], data.product_name, rfq_id)

    rfq_doc["matched_exporters"] = matched
    return BuyerRFQResponse(**{k: v for k, v in rfq_doc.items() if k not in ("_id", "opportunity_score", "risk_score", "source")})

@api_router.get("/buyer/rfqs", response_model=List[BuyerRFQResponse])
async def get_buyer_rfqs(user: dict = Depends(require_buyer)):
    rfqs = await db.buyer_rfqs.find({"buyer_id": user["id"]}, {"_id": 0}).to_list(100)
    return [BuyerRFQResponse(**{k: v for k, v in r.items() if k not in ("opportunity_score", "risk_score", "source")}) for r in rfqs]

@api_router.get("/buyer/rfqs/{rfq_id}", response_model=BuyerRFQResponse)
async def get_buyer_rfq(rfq_id: str, user: dict = Depends(require_buyer)):
    rfq = await db.buyer_rfqs.find_one({"id": rfq_id, "buyer_id": user["id"]}, {"_id": 0})
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    return BuyerRFQResponse(**{k: v for k, v in rfq.items() if k not in ("opportunity_score", "risk_score", "source")})

@api_router.get("/admin/buyer-rfqs")
async def admin_get_all_rfqs(user: dict = Depends(require_admin)):
    rfqs = await db.buyer_rfqs.find({}, {"_id": 0}).to_list(200)
    return rfqs

@api_router.put("/admin/buyer-rfqs/{rfq_id}/verify-payment")
async def admin_verify_rfq_payment(rfq_id: str, user: dict = Depends(require_admin)):
    result = await db.buyer_rfqs.update_one({"id": rfq_id}, {"$set": {"listing_fee_paid": True}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="RFQ not found")
    return {"message": "Listing fee marked as paid"}

@api_router.get("/admin/users/buyers")
async def admin_get_all_buyers(user: dict = Depends(require_admin)):
    """Return all registered buyers with their profile data."""
    buyers = await db.users.find({"role": "buyer"}, {"_id": 0, "password": 0}).to_list(500)
    profiles = await db.buyer_profiles.find({}, {"_id": 0}).to_list(500)
    profile_map = {p["user_id"]: p for p in profiles}
    for b in buyers:
        b["profile"] = profile_map.get(b["id"])
    return buyers

@api_router.get("/admin/users/exporters")
async def admin_get_all_exporters(user: dict = Depends(require_admin)):
    """Return all registered exporters with their profile data."""
    exporters = await db.users.find({"role": "exporter"}, {"_id": 0, "password": 0}).to_list(500)
    profiles = await db.exporter_profiles.find({}, {"_id": 0}).to_list(500)
    profile_map = {p["user_id"]: p for p in profiles}
    for e in exporters:
        e["profile"] = profile_map.get(e["id"])
    return exporters

# ===================== DEAL ROOM (MESSAGING) ROUTES =====================

@api_router.get("/deals/{deal_id}/messages", response_model=List[MessageResponse])
async def get_deal_messages(deal_id: str, user: dict = Depends(get_current_user)):
    deal = await db.deals.find_one({"id": deal_id}, {"_id": 0})
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    # Access control: admin sees all, exporter only sees their own deals
    if user["role"] == "exporter" and deal.get("exporter_user_id") != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    messages = await db.deal_messages.find({"deal_id": deal_id}, {"_id": 0}).sort("created_at", 1).to_list(500)

    # Mark as read
    await db.deal_messages.update_many(
        {"deal_id": deal_id, "read_by": {"$nin": [user["id"]]}},
        {"$push": {"read_by": user["id"]}}
    )

    return [MessageResponse(**m) for m in messages]

@api_router.post("/deals/{deal_id}/messages", response_model=MessageResponse, status_code=201)
async def post_deal_message(deal_id: str, data: MessageCreate, user: dict = Depends(get_current_user)):
    deal = await db.deals.find_one({"id": deal_id}, {"_id": 0})
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    if user["role"] == "exporter" and deal.get("exporter_user_id") != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    msg_id = str(uuid.uuid4())
    msg_doc = {
        "id": msg_id,
        "deal_id": deal_id,
        "sender_id": user["id"],
        "sender_name": user["company_name"],
        "sender_role": user["role"],
        "content": data.content,
        "attachment_url": data.attachment_url,
        "attachment_name": data.attachment_name,
        "read_by": [user["id"]],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.deal_messages.insert_one(msg_doc)
    return MessageResponse(**{k: v for k, v in msg_doc.items() if k != "_id"})

@api_router.get("/deals/{deal_id}/unread-count")
async def get_unread_count(deal_id: str, user: dict = Depends(get_current_user)):
    count = await db.deal_messages.count_documents({
        "deal_id": deal_id,
        "read_by": {"$nin": [user["id"]]},
        "sender_id": {"$ne": user["id"]},
    })
    return {"deal_id": deal_id, "unread": count}

# ===================== DOCUMENT INTELLIGENCE ROUTES =====================

@api_router.post("/documents/parse")
async def parse_document_text(
    content: str = Form(...),
    doc_hint: str = Form(""),
    deal_id: Optional[str] = Form(None),
    user: dict = Depends(get_current_user)
):
    """Parse trade document text using AI and optionally attach to a deal."""
    parsed = await ai_parse_document(content, doc_hint)

    doc_id = str(uuid.uuid4())
    doc_record = {
        "id": doc_id,
        "deal_id": deal_id,
        "uploaded_by": user["id"],
        "filename": f"parsed_document_{doc_id[:8]}.txt",
        "doc_type": parsed.get("doc_type", "Other"),
        "parsed_data": parsed,
        "url": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.documents.insert_one(doc_record)
    return {"document_id": doc_id, "parsed": parsed}

@api_router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    deal_id: Optional[str] = Form(None),
    user: dict = Depends(get_current_user)
):
    """Upload and parse a trade document (text extraction + AI parse)."""
    MAX_SIZE = 5 * 1024 * 1024  # 5MB
    content_bytes = await file.read()
    if len(content_bytes) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max 5MB.")

    # Extract text from file
    text_content = ""
    filename = file.filename or "upload"

    if filename.endswith(".txt"):
        text_content = content_bytes.decode("utf-8", errors="ignore")
    elif filename.endswith(".pdf"):
        try:
            import pdfplumber
            import io
            with pdfplumber.open(io.BytesIO(content_bytes)) as pdf:
                text_content = "\n".join(page.extract_text() or "" for page in pdf.pages)
        except Exception:
            text_content = content_bytes.decode("utf-8", errors="ignore")
    else:
        text_content = content_bytes.decode("utf-8", errors="ignore")

    parsed = await ai_parse_document(text_content, filename)

    # Store as base64 for retrieval
    encoded = base64.b64encode(content_bytes).decode()
    doc_id = str(uuid.uuid4())
    doc_record = {
        "id": doc_id,
        "deal_id": deal_id,
        "uploaded_by": user["id"],
        "filename": filename,
        "doc_type": parsed.get("doc_type", "Other"),
        "parsed_data": parsed,
        "content_b64": encoded,
        "url": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.documents.insert_one(doc_record)
    return {"document_id": doc_id, "filename": filename, "parsed": parsed}

@api_router.get("/documents/deal/{deal_id}", response_model=List[DocumentResponse])
async def get_deal_documents(deal_id: str, user: dict = Depends(get_current_user)):
    deal = await db.deals.find_one({"id": deal_id}, {"_id": 0})
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    if user["role"] == "exporter" and deal.get("exporter_user_id") != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    docs = await db.documents.find({"deal_id": deal_id}, {"_id": 0, "content_b64": 0}).to_list(50)
    return [DocumentResponse(**d) for d in docs]

# ===================== NBFC AUTOMATION ROUTES =====================

async def _simulate_nbfc_offer(nbfc_key: str, nbfc_info: dict, finance_request: dict) -> Optional[dict]:
    """Simulate NBFC API call. Replace with real API integration per NBFC."""
    api_url = nbfc_info.get("api_url")
    api_key = nbfc_info.get("api_key")

    if api_url and api_key:
        try:
            async with httpx.AsyncClient() as hc:
                resp = await hc.post(
                    f"{api_url}/finance/apply",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={
                        "applicant_id": finance_request["exporter_id"],
                        "amount_requested": finance_request["financing_amount_requested"],
                        "deal_type": finance_request.get("collateral_type", "LC"),
                        "tenure_months": 6,
                    },
                    timeout=15,
                )
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
            logger.warning(f"NBFC {nbfc_key} API call failed: {e}")
            return None

    # Simulate offer with realistic variance per partner
    import random
    base_rate = {"credlix": 12.5, "drip_capital": 13.0, "vayana": 11.8}.get(nbfc_key, 13.0)
    requested = finance_request.get("financing_amount_requested", 0)
    risk_score = finance_request.get("risk_score", 0.3)
    approval_ratio = max(0.5, 0.9 - risk_score * 0.4)

    return {
        "nbfc_partner": nbfc_info["name"],
        "offer_amount": round(requested * approval_ratio, 2),
        "interest_rate": round(base_rate + random.uniform(-0.5, 1.0), 2),
        "tenure_months": 6,
        "processing_fee": round(requested * 0.005, 2),
        "notes": f"Auto-offer from {nbfc_info['name']}. Subject to document verification.",
    }

@api_router.post("/finance-requests/{request_id}/submit-to-nbfcs", response_model=NBFCSubmitResponse)
async def submit_to_nbfcs(request_id: str, user: dict = Depends(require_admin)):
    """Fan out financing request to all configured NBFC partners simultaneously."""
    req = await db.finance_requests.find_one({"id": request_id}, {"_id": 0})
    if not req:
        raise HTTPException(status_code=404, detail="Finance request not found")

    if req["financing_status"] not in ("requested", "under_review"):
        raise HTTPException(status_code=400, detail="Request must be in requested/under_review state")

    await db.finance_requests.update_one(
        {"id": request_id},
        {"$set": {"financing_status": "sent_to_nbfc", "submitted_to_nbfcs_at": datetime.now(timezone.utc).isoformat()}}
    )

    # Fan out to all NBFC partners concurrently
    import asyncio
    tasks = {
        key: _simulate_nbfc_offer(key, info, req)
        for key, info in NBFC_PARTNERS.items()
    }
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)
    submitted_to = []
    all_offers = []

    for nbfc_key, result in zip(tasks.keys(), results):
        if isinstance(result, Exception) or result is None:
            continue
        submitted_to.append(NBFC_PARTNERS[nbfc_key]["name"])
        all_offers.append({**result, "nbfc_key": nbfc_key, "received_at": datetime.now(timezone.utc).isoformat()})

    # Store all offers; pick the best (lowest rate with highest amount)
    if all_offers:
        best = min(all_offers, key=lambda o: o.get("interest_rate", 99))
        await db.finance_requests.update_one(
            {"id": request_id},
            {"$set": {
                "financing_status": "nbfc_offer_received",
                "nbfc_partner": best["nbfc_partner"],
                "nbfc_offer_amount": best["offer_amount"],
                "nbfc_interest_rate": best["interest_rate"],
                "nbfc_tenure_months": best.get("tenure_months", 6),
                "nbfc_processing_fee": best.get("processing_fee", 0),
                "nbfc_all_offers": all_offers,
                "nbfc_offer_received_at": datetime.now(timezone.utc).isoformat(),
            }}
        )
        await notify_nbfc_offer_received(request_id)

    return NBFCSubmitResponse(
        request_id=request_id,
        submitted_to=submitted_to,
        message=f"Submitted to {len(submitted_to)} NBFC(s). Best offer pre-selected." if submitted_to else "No NBFC responses received.",
    )

@api_router.get("/finance-requests/{request_id}/offers")
async def get_nbfc_offers(request_id: str, user: dict = Depends(get_current_user)):
    """Get all NBFC offers for a financing request (for comparison view)."""
    req = await db.finance_requests.find_one({"id": request_id}, {"_id": 0})
    if not req:
        raise HTTPException(status_code=404, detail="Finance request not found")

    if user["role"] == "exporter" and req.get("exporter_id") != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    return {
        "request_id": request_id,
        "status": req.get("financing_status"),
        "offers": req.get("nbfc_all_offers", []),
        "selected_offer": {
            "nbfc_partner": req.get("nbfc_partner"),
            "offer_amount": req.get("nbfc_offer_amount"),
            "interest_rate": req.get("nbfc_interest_rate"),
            "tenure_months": req.get("nbfc_tenure_months"),
            "processing_fee": req.get("nbfc_processing_fee"),
        } if req.get("nbfc_partner") else None,
    }

@api_router.post("/webhooks/nbfc-offer")
async def nbfc_offer_webhook(data: NBFCOfferWebhook):
    """Receive NBFC offer via webhook (for real NBFC API integrations)."""
    req = await db.finance_requests.find_one({"id": data.request_id}, {"_id": 0})
    if not req:
        raise HTTPException(status_code=404, detail="Finance request not found")

    offer = {
        "nbfc_partner": data.nbfc_partner,
        "offer_amount": data.offer_amount,
        "interest_rate": data.interest_rate,
        "tenure_months": data.tenure_months,
        "processing_fee": data.processing_fee,
        "notes": data.notes,
        "received_at": datetime.now(timezone.utc).isoformat(),
    }

    await db.finance_requests.update_one(
        {"id": data.request_id},
        {
            "$set": {
                "financing_status": "nbfc_offer_received",
                "nbfc_partner": data.nbfc_partner,
                "nbfc_offer_amount": data.offer_amount,
                "nbfc_interest_rate": data.interest_rate,
                "nbfc_tenure_months": data.tenure_months,
                "nbfc_processing_fee": data.processing_fee,
            },
            "$push": {"nbfc_all_offers": offer},
        }
    )
    await notify_nbfc_offer_received(data.request_id)
    return {"message": "Offer recorded"}

# ===================== MARKET INTELLIGENCE ROUTES =====================

@api_router.get("/insights/overview", response_model=PlatformOverviewResponse)
async def get_platform_overview(user: dict = Depends(get_current_user)):
    """Platform-wide KPIs. Full detail for admin, summary for exporters."""
    total_opps = await db.opportunities.count_documents({})
    total_deals = await db.deals.count_documents({})
    closed_deals = await db.deals.count_documents({"stage": "Closed"})
    total_exporters = await db.exporter_profiles.count_documents({})
    total_buyers = await db.buyer_profiles.count_documents({})

    # Revenue total
    revenue_docs = await db.revenue_records.find({}, {"_id": 0, "amount": 1}).to_list(10000)
    total_revenue = sum(r.get("amount", 0) for r in revenue_docs)

    # Sector breakdown
    sector_breakdown = []
    for sector in SECTORS:
        count = await db.opportunities.count_documents({"sector": sector})
        deals_in_sector = await db.deals.count_documents({})  # simplified
        sector_breakdown.append({"sector": sector, "opportunities": count})

    # Region breakdown
    region_breakdown = []
    for region in REGIONS:
        count = await db.opportunities.count_documents({"region": region})
        region_breakdown.append({"region": region, "opportunities": count})

    # Monthly trend (last 6 months)
    monthly_trend = []
    now = datetime.now(timezone.utc)
    for i in range(5, -1, -1):
        month_start = (now.replace(day=1) - timedelta(days=i * 30)).replace(day=1)
        month_end = month_start.replace(day=28) + timedelta(days=4)
        month_end = month_end.replace(day=1)
        month_label = month_start.strftime("%b %Y")
        count = await db.opportunities.count_documents({
            "created_at": {"$gte": month_start.isoformat(), "$lt": month_end.isoformat()}
        })
        deal_count = await db.deals.count_documents({
            "created_at": {"$gte": month_start.isoformat(), "$lt": month_end.isoformat()}
        })
        monthly_trend.append({"month": month_label, "opportunities": count, "deals": deal_count})

    return PlatformOverviewResponse(
        total_opportunities=total_opps,
        total_deals=total_deals,
        total_exporters=total_exporters,
        total_buyers=total_buyers,
        closed_deals=closed_deals,
        total_revenue_inr=total_revenue if user["role"] == "admin" else 0,
        sector_breakdown=sector_breakdown,
        region_breakdown=region_breakdown,
        monthly_trend=monthly_trend,
    )

@api_router.get("/insights/sector/{sector}")
async def get_sector_insight(sector: str, user: dict = Depends(get_current_user)):
    """Deep sector intelligence — opportunity patterns, top markets, compliance requirements."""
    if sector not in SECTORS:
        raise HTTPException(status_code=400, detail=f"Invalid sector. Choose from: {SECTORS}")

    opportunities = await db.opportunities.find({"sector": sector}, {"_id": 0}).to_list(500)
    deals = await db.deals.find({}, {"_id": 0}).to_list(500)

    # Top destination markets
    market_counts: Dict[str, int] = {}
    for opp in opportunities:
        country = opp.get("source_country", "Unknown")
        market_counts[country] = market_counts.get(country, 0) + 1
    top_markets = sorted(
        [{"country": k, "opportunities": v} for k, v in market_counts.items()],
        key=lambda x: x["opportunities"], reverse=True
    )[:5]

    # Compliance frequency
    compliance_counts: Dict[str, int] = {}
    for opp in opportunities:
        for cert in opp.get("compliance_requirements", []):
            compliance_counts[cert] = compliance_counts.get(cert, 0) + 1
    compliance_frequency = sorted(
        [{"cert": k, "count": v} for k, v in compliance_counts.items()],
        key=lambda x: x["count"], reverse=True
    )

    # Closed deals for win rate
    sector_opp_ids = {opp["id"] for opp in opportunities}
    sector_deals = [d for d in deals if d.get("opportunity_id") in sector_opp_ids]
    closed_sector_deals = [d for d in sector_deals if d.get("stage") == "Closed"]
    win_rate = len(closed_sector_deals) / len(sector_deals) if sector_deals else 0

    return {
        "sector": sector,
        "total_opportunities": len(opportunities),
        "total_deals": len(sector_deals),
        "avg_deal_value_inr": 3500000,  # placeholder — enrich when deal value is tracked
        "top_markets": top_markets,
        "avg_time_to_close_days": 42,  # placeholder
        "win_rate": round(win_rate, 3),
        "compliance_frequency": compliance_frequency,
        "active_opportunities": sum(1 for o in opportunities if o.get("status") == "Active"),
    }

@api_router.get("/insights/market/{country}")
async def get_market_insight(country: str, user: dict = Depends(get_current_user)):
    """Intelligence for a specific destination market/country."""
    opportunities = await db.opportunities.find(
        {"source_country": {"$regex": country, "$options": "i"}},
        {"_id": 0}
    ).to_list(500)

    sector_counts: Dict[str, int] = {}
    compliance_counts: Dict[str, int] = {}
    regions = set()

    for opp in opportunities:
        s = opp.get("sector", "Unknown")
        sector_counts[s] = sector_counts.get(s, 0) + 1
        regions.add(opp.get("region", "Unknown"))
        for cert in opp.get("compliance_requirements", []):
            compliance_counts[cert] = compliance_counts.get(cert, 0) + 1

    top_sectors = sorted(
        [{"sector": k, "count": v} for k, v in sector_counts.items()],
        key=lambda x: x["count"], reverse=True
    )
    typical_compliance = sorted(compliance_counts, key=lambda x: compliance_counts[x], reverse=True)[:5]

    return {
        "country": country,
        "region": list(regions)[0] if regions else "Unknown",
        "total_opportunities": len(opportunities),
        "top_sectors": top_sectors,
        "avg_quantity": "1500 MT",  # placeholder
        "typical_compliance": typical_compliance,
    }

@api_router.get("/insights/exporter/benchmarks")
async def get_exporter_benchmarks(user: dict = Depends(require_exporter)):
    """Show an exporter how they compare to anonymous industry benchmarks."""
    profile = await db.exporter_profiles.find_one({"user_id": user["id"]}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=404, detail="Complete your profile first")

    my_deals = await db.deals.find({"exporter_user_id": user["id"]}, {"_id": 0}).to_list(100)
    my_interests = await db.interests.count_documents({"exporter_user_id": user["id"]})
    my_closed = sum(1 for d in my_deals if d.get("stage") == "Closed")

    all_deals = await db.deals.count_documents({})
    all_closed = await db.deals.count_documents({"stage": "Closed"})
    platform_win_rate = all_closed / all_deals if all_deals else 0
    my_win_rate = my_closed / len(my_deals) if my_deals else 0

    return {
        "my_stats": {
            "total_deals": len(my_deals),
            "closed_deals": my_closed,
            "win_rate": round(my_win_rate, 3),
            "interests_expressed": my_interests,
            "reliability_score": profile.get("reliability_score", 0),
        },
        "platform_benchmarks": {
            "avg_win_rate": round(platform_win_rate, 3),
            "avg_deals_per_exporter": round(all_deals / max(await db.exporter_profiles.count_documents({}), 1), 1),
            "top_certifications": ["FSSAI", "ISO 22000", "HACCP"],
            "top_markets": ["UAE", "Nigeria", "Germany"],
        },
    }

# ===================== WHATSAPP PHONE UPDATE =====================

@api_router.put("/profile/whatsapp")
async def update_whatsapp_phone(phone: str, user: dict = Depends(get_current_user)):
    """Exporter/buyer saves their WhatsApp number for notifications."""
    # Basic validation
    phone = phone.strip().replace(" ", "").replace("-", "")
    if not phone.startswith("+"):
        phone = "+91" + phone  # default to India
    await db.users.update_one({"id": user["id"]}, {"$set": {"whatsapp_phone": phone}})
    return {"message": "WhatsApp number updated", "phone": phone}

@api_router.get("/profile/whatsapp")
async def get_whatsapp_phone(user: dict = Depends(get_current_user)):
    u = await db.users.find_one({"id": user["id"]}, {"_id": 0, "whatsapp_phone": 1})
    return {"phone": u.get("whatsapp_phone") if u else None}

# ===================== HEALTH CHECK =====================

@api_router.get("/")
async def root():
    return {"message": "TradeNexus AI API", "version": "1.0.0"}

@api_router.get("/health")
async def health():
    try:
        await db.command("ping")
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    return {
        "status": "healthy",
        "db": db_status,
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

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
async def startup_event():
    """Create indexes and seed demo data on startup."""
    logger.info("TradeNexus AI starting up...")
    try:
        # Create indexes for performance
        await db.users.create_index("email", unique=True)
        await db.users.create_index("role")
        await db.opportunities.create_index("status")
        await db.opportunities.create_index("sector")
        await db.opportunities.create_index("region")
        await db.opportunities.create_index([("created_at", -1)])
        await db.deals.create_index("opportunity_id")
        await db.deals.create_index("exporter_user_id")
        await db.deals.create_index("stage")
        await db.deals.create_index([("created_at", -1)])
        await db.messages.create_index("deal_id")
        await db.messages.create_index([("deal_id", 1), ("created_at", 1)])
        await db.finance_requests.create_index("exporter_id")
        await db.finance_requests.create_index("financing_status")
        await db.buyer_rfqs.create_index("buyer_user_id")
        await db.buyer_rfqs.create_index("status")
        await db.revenue_records.create_index([("created_at", -1)])
        await db.exporter_profiles.create_index("user_id", unique=True)
        logger.info("MongoDB indexes created successfully")
    except Exception as e:
        logger.warning(f"Index creation skipped (may already exist): {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    logger.info("TradeNexus AI shut down cleanly")

# ── Serve React SPA ───────────────────────────────────────────────────────────
# When deployed on Railway, the frontend build is placed at:
#   /app/frontend/build   (set FRONTEND_BUILD_DIR to override)
_FRONTEND_BUILD = Path(
    os.environ.get("FRONTEND_BUILD_DIR", ROOT_DIR.parent / "frontend" / "build")
)

if _FRONTEND_BUILD.exists():
    # Serve hashed static assets (JS/CSS bundles)
    app.mount(
        "/static",
        StaticFiles(directory=_FRONTEND_BUILD / "static"),
        name="react-static",
    )

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        """Serve the React SPA for any non-API path."""
        candidate = _FRONTEND_BUILD / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_FRONTEND_BUILD / "index.html")
else:
    logger.info(
        f"Frontend build not found at {_FRONTEND_BUILD}. "
        "API-only mode — set FRONTEND_BUILD_DIR or run `yarn build` in frontend/."
    )
