"""
ArthMitra AI - Finance API Routes
Direct API access to financial calculations
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..core.calculator import ArthMitraCalculator
from ..core.validator import ArthMitraValidator

router = APIRouter(prefix="/api/finance", tags=["finance"])


# Pydantic models for request/response
class FinancialProfile(BaseModel):
    age: int = Field(..., ge=18, le=100)
    monthly_income: int = Field(..., ge=0)
    monthly_expenses: int = Field(..., ge=0)
    monthly_emi: int = Field(default=0, ge=0)
    emergency_fund: int = Field(default=0, ge=0)
    monthly_sip: int = Field(default=0, ge=0)
    term_cover: int = Field(default=0, ge=0)
    health_cover: int = Field(default=0, ge=0)
    cc_outstanding: int = Field(default=0, ge=0)
    annual_gross: Optional[int] = Field(default=None, ge=0)
    basic_salary: Optional[int] = Field(default=None, ge=0)
    hra_received: int = Field(default=0, ge=0)
    rent_paid: int = Field(default=0, ge=0)
    city_type: str = Field(default="metro", pattern="^(metro|non-metro)$")
    total_investments: int = Field(default=0, ge=0)
    equity_pct: float = Field(default=0.5, ge=0, le=1)
    used_80c: int = Field(default=0, ge=0, le=150000)
    health_premium: int = Field(default=0, ge=0, le=25000)
    nps_tier1: int = Field(default=0, ge=0, le=50000)
    target_retirement_age: int = Field(default=60, ge=40, le=80)


class PortfolioFund(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., pattern="^(equity|debt|hybrid|elss|liquid|gold|international)$")
    invested: int = Field(..., ge=0)
    current: int = Field(..., ge=0)


class LifeEventRequest(BaseModel):
    event_type: str = Field(..., pattern="^(bonus|job_change|marriage|baby|retirement|education|house_purchase)$")
    event_data: Dict[str, Any] = Field(default_factory=dict)


class CoupleFinanceRequest(BaseModel):
    partner1: FinancialProfile
    partner2: FinancialProfile


class WhatIfRequest(BaseModel):
    profile: FinancialProfile
    changes: Dict[str, Any]


@router.post("/mhs", summary="Calculate Money Health Score")
async def calculate_mhs(profile: FinancialProfile) -> Dict[str, Any]:
    """Calculate comprehensive Money Health Score with 5 dimensions"""
    try:
        # Convert to dict for calculator
        profile_dict = profile.dict()

        # Validate input
        validation = ArthMitraValidator.validate_financial_profile(profile_dict)
        if not validation["valid"]:
            raise HTTPException(status_code=400, detail={
                "error": "Invalid input data",
                "details": validation["errors"]
            })

        # Calculate MHS
        result = ArthMitraCalculator.calculate_mhs(validation["sanitized"])

        return {
            "success": True,
            "data": result,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@router.post("/tax", summary="Calculate Tax Optimization")
async def calculate_tax(profile: FinancialProfile) -> Dict[str, Any]:
    """Calculate tax liability under old vs new regime with optimization suggestions"""
    try:
        profile_dict = profile.dict()

        # Validate input (focus on tax fields)
        validation = ArthMitraValidator.validate_financial_profile(profile_dict)
        if not validation["valid"]:
            raise HTTPException(status_code=400, detail={
                "error": "Invalid input data",
                "details": validation["errors"]
            })

        # Check required tax fields
        sanitized = validation["sanitized"]
        if not sanitized.get("annual_gross") or not sanitized.get("basic_salary"):
            raise HTTPException(status_code=400, detail={
                "error": "Annual gross and basic salary are required for tax calculation"
            })

        result = ArthMitraCalculator.calculate_tax(sanitized)

        return {
            "success": True,
            "data": result,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tax calculation error: {str(e)}")


@router.post("/fire", summary="Calculate FIRE Plan")
async def calculate_fire(profile: FinancialProfile) -> Dict[str, Any]:
    """Calculate Financial Independence Retire Early plan with projections"""
    try:
        profile_dict = profile.dict()

        validation = ArthMitraValidator.validate_financial_profile(profile_dict)
        if not validation["valid"]:
            raise HTTPException(status_code=400, detail={
                "error": "Invalid input data",
                "details": validation["errors"]
            })

        result = ArthMitraCalculator.calculate_fire(validation["sanitized"])

        return {
            "success": True,
            "data": result,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FIRE calculation error: {str(e)}")


@router.post("/portfolio", summary="Analyze Mutual Fund Portfolio")
async def analyze_portfolio(portfolio: List[PortfolioFund]) -> Dict[str, Any]:
    """Analyze mutual fund portfolio for diversification, risk, and returns"""
    try:
        portfolio_dict = [fund.dict() for fund in portfolio]

        validation = ArthMitraValidator.validate_portfolio(portfolio_dict)
        if not validation["valid"]:
            raise HTTPException(status_code=400, detail={
                "error": "Invalid portfolio data",
                "details": validation["errors"]
            })

        result = ArthMitraCalculator.analyze_portfolio(validation["sanitized"])

        return {
            "success": True,
            "data": result,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Portfolio analysis error: {str(e)}")


@router.post("/couple", summary="Optimize Couple Finances")
async def optimize_couple_finance(request: CoupleFinanceRequest) -> Dict[str, Any]:
    """Optimize financial planning for couples with tax and investment strategies"""
    try:
        partner1_dict = request.partner1.dict()
        partner2_dict = request.partner2.dict()

        validation = ArthMitraValidator.validate_couple_profiles(partner1_dict, partner2_dict)
        if not validation["valid"]:
            raise HTTPException(status_code=400, detail={
                "error": "Invalid couple profile data",
                "details": validation["errors"]
            })

        result = ArthMitraCalculator.optimize_couple_finance(
            validation["partner1"], validation["partner2"]
        )

        return {
            "success": True,
            "data": result,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Couple finance optimization error: {str(e)}")


@router.post("/life-event", summary="Analyze Life Event Impact")
async def analyze_life_event(request: LifeEventRequest) -> Dict[str, Any]:
    """Analyze financial impact of life events and provide action plan"""
    try:
        # We need profile data for life event analysis - this should come from user session
        # For now, we'll use a basic profile or require it in the request
        profile = {}  # TODO: Get from user session/database

        result = ArthMitraCalculator.analyze_life_event(
            request.event_type, profile, request.event_data
        )

        return {
            "success": True,
            "data": result,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Life event analysis error: {str(e)}")


@router.post("/instant-insight", summary="Get Instant Financial Insights")
async def get_instant_insight(profile: FinancialProfile) -> Dict[str, Any]:
    """Get quick financial insights from basic profile data"""
    try:
        profile_dict = profile.dict()

        validation = ArthMitraValidator.validate_financial_profile(profile_dict)
        if not validation["valid"]:
            raise HTTPException(status_code=400, detail={
                "error": "Invalid input data",
                "details": validation["errors"]
            })

        result = ArthMitraCalculator.instant_insight(validation["sanitized"])

        return {
            "success": True,
            "data": result,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Instant insight error: {str(e)}")


@router.post("/what-if", summary="Run What-If Simulation")
async def run_what_if_simulation(request: WhatIfRequest) -> Dict[str, Any]:
    """Simulate financial scenarios with hypothetical changes"""
    try:
        profile_dict = request.profile.dict()

        validation = ArthMitraValidator.validate_financial_profile(profile_dict)
        if not validation["valid"]:
            raise HTTPException(status_code=400, detail={
                "error": "Invalid profile data",
                "details": validation["errors"]
            })

        result = ArthMitraCalculator.what_if_simulation(
            validation["sanitized"], request.changes
        )

        return {
            "success": True,
            "data": result,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"What-if simulation error: {str(e)}")


@router.post("/risk-alerts", summary="Get Risk Alerts")
async def get_risk_alerts(profile: FinancialProfile) -> Dict[str, Any]:
    """Generate personalized risk alerts based on financial profile"""
    try:
        profile_dict = profile.dict()

        validation = ArthMitraValidator.validate_financial_profile(profile_dict)
        if not validation["valid"]:
            raise HTTPException(status_code=400, detail={
                "error": "Invalid input data",
                "details": validation["errors"]
            })

        alerts = ArthMitraCalculator.risk_alerts(validation["sanitized"])

        return {
            "success": True,
            "data": {
                "alerts": alerts,
                "total_alerts": len(alerts),
                "critical_count": len([a for a in alerts if a["type"] == "critical"]),
                "high_count": len([a for a in alerts if a["type"] == "high"]),
                "medium_count": len([a for a in alerts if a["type"] == "medium"])
            },
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk alerts error: {str(e)}")


@router.get("/health", summary="Finance API Health Check")
async def finance_health() -> Dict[str, Any]:
    """Check if finance calculation APIs are working"""
    return {
        "status": "healthy",
        "service": "arthmitra-finance-api",
        "features": [
            "mhs", "tax", "fire", "portfolio", "couple",
            "life_event", "instant_insight", "what_if", "risk_alerts"
        ],
        "timestamp": datetime.now().isoformat()
    }