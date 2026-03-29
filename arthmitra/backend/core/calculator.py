"""
ArthMitra AI - Core Calculator Module
All financial calculations happen here - NO AI, just pure math
"""

import math
from typing import Dict, List, Any
from datetime import datetime


class ArthMitraCalculator:
    """Central calculator for all financial computations"""

    @staticmethod
    def calculate_mhs(profile: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate Money Health Score (0-100) with 5 dimensions"""
        try:
            # Extract values with safe defaults
            age = max(18, min(100, profile.get("age", 30)))
            monthly_income = max(0, profile.get("monthly_income", 0) // 100)  # Convert from paise
            monthly_expenses = max(0, profile.get("monthly_expenses", 0) // 100)
            monthly_emi = max(0, profile.get("monthly_emi", 0) // 100)
            emergency_fund = max(0, profile.get("emergency_fund", 0) // 100)
            monthly_sip = max(0, profile.get("monthly_sip", 0) // 100)
            term_cover = max(0, profile.get("term_cover", 0) // 100)
            health_cover = max(0, profile.get("health_cover", 0) // 100)
            cc_outstanding = max(0, profile.get("cc_outstanding", 0) // 100)

            # 1. Emergency Preparedness (0-20 points)
            emergency_months = emergency_fund / max(1, monthly_expenses)
            emergency_score = min(20, (emergency_months / 6) * 20)  # Target: 6 months

            # 2. Debt Health (0-20 points)
            debt_ratio = monthly_emi / max(1, monthly_income)
            debt_score = max(0, 20 - (debt_ratio * 100)) if debt_ratio <= 0.5 else 0
            if cc_outstanding > 0:
                debt_score = max(0, debt_score - 5)

            # 3. Savings Discipline (0-20 points)
            savings_rate = monthly_sip / max(1, monthly_income)
            savings_score = min(20, savings_rate * 200)  # Target: 10% of income

            # 4. Insurance Safety (0-20 points)
            term_score = min(10, (term_cover / max(1, monthly_income * 12 * 10)) * 10)
            health_score = min(10, (health_cover / 500000) * 10)
            insurance_score = term_score + health_score

            # 5. Investment Readiness (0-20 points)
            ideal_equity_pct = max(0.1, 1.0 - (age / 100))
            current_equity_pct = profile.get("equity_pct", 0.5)
            deviation = abs(current_equity_pct - ideal_equity_pct)
            investment_score = max(0, 20 - (deviation * 100))

            # Total score
            total_score = int(round(emergency_score + debt_score + savings_score + insurance_score + investment_score))

            dimensions = {
                "emergency": int(round(emergency_score * 5)),  # Scale to 0-100
                "debt": int(round(debt_score * 5)),
                "savings": int(round(savings_score * 5)),
                "insurance": int(round(insurance_score * 5)),
                "investment": int(round(investment_score * 5))
            }

            weakest = min(dimensions.items(), key=lambda x: x[1])[0]

            return {
                "total": total_score,
                "dimensions": dimensions,
                "weakest": weakest,
                "band": "excellent" if total_score >= 80 else "good" if total_score >= 60 else "fair" if total_score >= 40 else "poor"
            }

        except Exception as e:
            return {
                "total": 50,
                "dimensions": {"emergency": 50, "debt": 50, "savings": 50, "insurance": 50, "investment": 50},
                "weakest": "unknown",
                "band": "unknown",
                "error": str(e)
            }

    @staticmethod
    def calculate_tax(profile: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate tax optimization for India (Old vs New regime)"""
        try:
            annual_gross = max(0, profile.get("annual_gross", 0) // 100)
            basic_salary = max(0, profile.get("basic_salary", 0) // 100)
            hra_received = max(0, profile.get("hra_received", 0) // 100)
            rent_paid = max(0, profile.get("rent_paid", 0) // 100)
            is_metro = profile.get("city_type", "metro") == "metro"
            used_80c = min(150000, max(0, profile.get("used_80c", 0) // 100))
            health_premium = min(25000, max(0, profile.get("health_premium", 0) // 100))
            nps_tier1 = min(50000, max(0, profile.get("nps_tier1", 0) // 100))

            # HRA exemption calculation
            hra_exempt = min(hra_received, rent_paid, basic_salary * (0.5 if is_metro else 0.4))

            # Old regime calculations
            old_deductions = 50000 + hra_exempt + used_80c + health_premium + nps_tier1
            old_taxable = max(0, annual_gross - old_deductions)
            old_tax = ArthMitraCalculator._calculate_old_regime_tax(old_taxable) * 1.04  # Cess

            # New regime calculations
            new_deductions = 75000  # Standard deduction
            new_taxable = max(0, annual_gross - new_deductions)
            new_tax = ArthMitraCalculator._calculate_new_regime_tax(new_taxable) * 1.04  # Cess

            recommended = "old" if old_tax < new_tax else "new"
            savings = abs(old_tax - new_tax)

            # Missing deductions
            missing_deductions = []
            if used_80c < 150000:
                missing_deductions.append({
                    "name": "80C Gap",
                    "potential": 150000 - used_80c,
                    "saving": int((150000 - used_80c) * 0.20)  # Approx tax rate
                })
            if nps_tier1 < 50000:
                missing_deductions.append({
                    "name": "NPS 80CCD(1B)",
                    "potential": 50000 - nps_tier1,
                    "saving": int((50000 - nps_tier1) * 0.30)
                })

            return {
                "old_tax": int(old_tax),
                "new_tax": int(new_tax),
                "recommended": recommended,
                "savings": int(savings),
                "old_taxable": int(old_taxable),
                "new_taxable": int(new_taxable),
                "hra_exempt": int(hra_exempt),
                "used_80c": int(used_80c),
                "missing_deductions": missing_deductions
            }

        except Exception as e:
            return {
                "old_tax": 0,
                "new_tax": 0,
                "recommended": "new",
                "savings": 0,
                "error": str(e)
            }

    @staticmethod
    def _calculate_old_regime_tax(taxable: float) -> float:
        """Calculate tax under old regime"""
        tax = 0
        slabs = [
            (250000, 500000, 0.05),
            (500000, 1000000, 0.20),
            (1000000, float('inf'), 0.30)
        ]
        for start, end, rate in slabs:
            if taxable > start:
                amount = min(taxable, end) - start
                tax += amount * rate
        return tax

    @staticmethod
    def _calculate_new_regime_tax(taxable: float) -> float:
        """Calculate tax under new regime"""
        tax = 0
        slabs = [
            (300000, 700000, 0.05),
            (700000, 1000000, 0.10),
            (1000000, 1200000, 0.15),
            (1200000, 1500000, 0.20),
            (1500000, float('inf'), 0.30)
        ]
        for start, end, rate in slabs:
            if taxable > start:
                amount = min(taxable, end) - start
                tax += amount * rate
        return tax

    @staticmethod
    def calculate_fire(profile: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate FIRE (Financial Independence Retire Early) plan"""
        try:
            age = max(18, min(80, profile.get("age", 30)))
            target_age = max(age + 5, min(80, profile.get("target_retirement_age", 60)))
            years = target_age - age

            monthly_income = max(0, profile.get("monthly_income", 0) // 100)
            monthly_expenses = max(1, profile.get("monthly_expenses", 0) // 100)
            monthly_emi = max(0, profile.get("monthly_emi", 0) // 100)
            total_investments = max(0, profile.get("total_investments", 0) // 100)
            monthly_sip = max(0, profile.get("monthly_sip", 0) // 100)

            # FIRE calculations
            inflation_rate = 0.06
            safe_withdrawal_rate = 0.035
            expected_return = 0.10

            # Future expenses (adjusted for inflation)
            future_expenses = monthly_expenses * (1 + inflation_rate) ** years
            annual_fire_corpus = future_expenses * 12 / safe_withdrawal_rate
            fire_corpus = int(round(annual_fire_corpus))

            # Current projection
            monthly_investable = monthly_income - monthly_expenses - monthly_emi
            current_projection = ArthMitraCalculator._calculate_future_value(
                total_investments, monthly_sip, expected_return, years
            )

            gap = max(0, fire_corpus - current_projection)
            additional_monthly_sip = ArthMitraCalculator._calculate_required_sip(
                gap, expected_return, years
            )

            # Achievement percentage
            achievement_pct = min(100, int((current_projection / max(1, fire_corpus)) * 100))

            # Roadmap phases
            phases = [
                {"phase": "Phase 1: Foundation", "duration": "0-2 years", "focus": "Build emergency fund, start SIP"},
                {"phase": "Phase 2: Growth", "duration": "3-5 years", "focus": "Increase SIP, optimize taxes"},
                {"phase": "Phase 3: Acceleration", "duration": "6+ years", "focus": "Maximize investments, reduce expenses"}
            ]

            return {
                "fire_corpus": fire_corpus,
                "current_projection": int(current_projection),
                "gap": int(gap),
                "additional_monthly_sip": int(additional_monthly_sip),
                "years_to_go": years,
                "achievement_percentage": achievement_pct,
                "monthly_investable": monthly_investable,
                "phases": phases,
                "feasible": additional_monthly_sip <= monthly_investable
            }

        except Exception as e:
            return {
                "fire_corpus": 50000000,
                "current_projection": 10000000,
                "gap": 40000000,
                "additional_monthly_sip": 50000,
                "error": str(e)
            }

    @staticmethod
    def _calculate_future_value(present_value: float, monthly_investment: float,
                               annual_return: float, years: int) -> float:
        """Calculate future value of investments"""
        monthly_rate = annual_return / 12
        months = years * 12

        # Future value of current investments
        fv_current = present_value * (1 + annual_return) ** years

        # Future value of monthly investments
        if monthly_rate > 0:
            fv_monthly = monthly_investment * (((1 + monthly_rate) ** months - 1) / monthly_rate)
        else:
            fv_monthly = monthly_investment * months

        return fv_current + fv_monthly

    @staticmethod
    def _calculate_required_sip(target_amount: float, annual_return: float, years: int) -> float:
        """Calculate required monthly SIP to reach target"""
        if years <= 0 or target_amount <= 0:
            return 0

        monthly_rate = annual_return / 12
        months = years * 12

        if monthly_rate > 0:
            return target_amount * monthly_rate / ((1 + monthly_rate) ** months - 1)
        else:
            return target_amount / months

    @staticmethod
    def analyze_portfolio(portfolio: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze mutual fund portfolio"""
        try:
            if not portfolio:
                return {"error": "No portfolio data provided"}

            total_invested = sum(fund.get("invested", 0) for fund in portfolio)
            total_current = sum(fund.get("current", 0) for fund in portfolio)

            # Risk assessment based on fund types
            equity_funds = sum(1 for fund in portfolio if "equity" in fund.get("type", "").lower())
            debt_funds = sum(1 for fund in portfolio if "debt" in fund.get("type", "").lower())
            hybrid_funds = len(portfolio) - equity_funds - debt_funds

            risk_score = (equity_funds * 3 + hybrid_funds * 2 + debt_funds * 1) / max(1, len(portfolio))

            # Diversification score (0-100)
            diversification_score = min(100, len(portfolio) * 10 + (100 - risk_score * 10))

            # Overlap analysis (simplified)
            overlap_warnings = []
            if equity_funds > 2:
                overlap_warnings.append("Multiple equity funds - check for overlap")
            if debt_funds > 1:
                overlap_warnings.append("Multiple debt funds - consider consolidation")

            # Rebalancing suggestions
            suggestions = []
            if risk_score > 2.5:
                suggestions.append("Consider adding debt funds for stability")
            elif risk_score < 1.5:
                suggestions.append("Consider adding equity funds for growth")
            if len(portfolio) < 3:
                suggestions.append("Add more funds for better diversification")

            return {
                "total_invested": int(total_invested),
                "total_current": int(total_current),
                "total_return": int(total_current - total_invested),
                "total_return_pct": round((total_current / max(1, total_invested) - 1) * 100, 2),
                "fund_count": len(portfolio),
                "risk_score": round(risk_score, 1),
                "risk_level": "High" if risk_score > 2.5 else "Medium" if risk_score > 1.5 else "Low",
                "diversification_score": diversification_score,
                "overlap_warnings": overlap_warnings,
                "suggestions": suggestions
            }

        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def optimize_couple_finance(partner1: Dict[str, Any], partner2: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize finances for couples"""
        try:
            # Individual tax calculations
            tax1 = ArthMitraCalculator.calculate_tax(partner1)
            tax2 = ArthMitraCalculator.calculate_tax(partner2)

            # Combined tax (simplified - assuming separate filing)
            combined_tax = tax1["old_tax"] + tax2["old_tax"]
            combined_tax_new = tax1["new_tax"] + tax2["new_tax"]

            # SIP optimization (higher earner takes more for tax efficiency)
            income1 = partner1.get("annual_gross", 0) // 100
            income2 = partner2.get("annual_gross", 0) // 100

            if income1 > income2:
                sip_split_p1 = 70
                sip_split_p2 = 30
            else:
                sip_split_p1 = 50
                sip_split_p2 = 50

            # Insurance optimization
            total_cover_needed = (income1 + income2) * 10  # 10 years of combined income
            term_split = [60, 40] if income1 > income2 else [50, 50]

            return {
                "individual_tax": {
                    "partner1": tax1,
                    "partner2": tax2
                },
                "combined_tax": {
                    "old_regime": int(combined_tax),
                    "new_regime": int(combined_tax_new),
                    "recommended": "old" if combined_tax < combined_tax_new else "new",
                    "savings": int(abs(combined_tax - combined_tax_new))
                },
                "sip_optimization": {
                    "partner1_percentage": sip_split_p1,
                    "partner2_percentage": sip_split_p2,
                    "reason": "Higher earner contributes more for better tax efficiency"
                },
                "insurance_optimization": {
                    "total_cover_needed": int(total_cover_needed),
                    "term_split": term_split,
                    "recommendation": "Split term insurance based on income contribution"
                }
            }

        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def analyze_life_event(event_type: str, profile: Dict[str, Any], event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze life events and provide guidance"""
        try:
            actions = []

            if event_type == "bonus":
                bonus_amount = event_data.get("amount", 0) // 100
                actions = [
                    {"priority": 1, "action": f"Keep 20% ({int(bonus_amount * 0.2)}) for emergency fund", "amount": int(bonus_amount * 0.2)},
                    {"priority": 2, "action": f"Invest 50% ({int(bonus_amount * 0.5)}) in tax-saving instruments", "amount": int(bonus_amount * 0.5)},
                    {"priority": 3, "action": f"Use 30% ({int(bonus_amount * 0.3)}) for personal goals", "amount": int(bonus_amount * 0.3)}
                ]

            elif event_type == "job_change":
                new_salary = event_data.get("new_salary", 0) // 100
                old_salary = profile.get("monthly_income", 0) // 100
                increase = new_salary - old_salary
                if increase > 0:
                    actions = [
                        {"priority": 1, "action": f"Increase SIP by ₹{int(increase * 0.5)} per month", "amount": int(increase * 0.5)},
                        {"priority": 2, "action": f"Build emergency fund with ₹{int(increase * 0.3)}", "amount": int(increase * 0.3)},
                        {"priority": 3, "action": f"Review insurance coverage with new salary", "amount": 0}
                    ]

            elif event_type == "marriage":
                actions = [
                    {"priority": 1, "action": "Increase emergency fund to 9 months of expenses", "amount": 0},
                    {"priority": 2, "action": "Review term insurance for both partners", "amount": 0},
                    {"priority": 3, "action": "Start joint financial planning", "amount": 0}
                ]

            elif event_type == "baby":
                actions = [
                    {"priority": 1, "action": "Increase health insurance coverage", "amount": 0},
                    {"priority": 2, "action": "Start child education fund with ₹5000 SIP", "amount": 5000},
                    {"priority": 3, "action": "Review term insurance for family protection", "amount": 0}
                ]

            return {
                "event_type": event_type,
                "actions": actions,
                "impact": "positive" if event_type in ["bonus", "job_change"] else "moderate",
                "timeframe": "immediate" if event_type == "bonus" else "3-6 months"
            }

        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def instant_insight(profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate instant financial insights from basic profile"""
        try:
            monthly_income = profile.get("monthly_income", 0) // 100
            monthly_expenses = profile.get("monthly_expenses", 0) // 100

            # Quick calculations
            savings_rate = (monthly_income - monthly_expenses) / max(1, monthly_income)
            mhs_quick = ArthMitraCalculator.calculate_mhs(profile)

            insights = []

            if savings_rate < 0.1:
                insights.append("Savings rate is low - aim for 20% of income")
            elif savings_rate > 0.3:
                insights.append("Excellent savings rate!")

            if mhs_quick["total"] < 40:
                insights.append("Financial health needs attention")
            elif mhs_quick["total"] > 70:
                insights.append("Strong financial foundation")

            return {
                "monthly_income": monthly_income,
                "monthly_expenses": monthly_expenses,
                "savings_rate": round(savings_rate * 100, 1),
                "mhs_score": mhs_quick["total"],
                "key_insights": insights,
                "weakest_area": mhs_quick["weakest"]
            }

        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def what_if_simulation(profile: Dict[str, Any], changes: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate 'what if' scenarios"""
        try:
            # Create modified profile
            modified_profile = profile.copy()
            modified_profile.update(changes)

            # Calculate impacts
            original_mhs = ArthMitraCalculator.calculate_mhs(profile)
            modified_mhs = ArthMitraCalculator.calculate_mhs(modified_profile)

            impacts = []

            if changes.get("monthly_sip"):
                new_sip = changes["monthly_sip"] // 100
                # Simple projection: 10% annual return
                monthly_projection = new_sip * 12 * 0.1  # Rough annual return
                impacts.append(f"Additional monthly SIP of ₹{new_sip} could generate ~₹{int(monthly_projection)} annually")

            if changes.get("monthly_expenses"):
                expense_change = (changes["monthly_expenses"] - profile.get("monthly_expenses", 0)) // 100
                if expense_change < 0:
                    impacts.append(f"Reducing expenses by ₹{abs(expense_change)} improves savings rate")

            return {
                "original_mhs": original_mhs["total"],
                "modified_mhs": modified_mhs["total"],
                "improvement": modified_mhs["total"] - original_mhs["total"],
                "impacts": impacts
            }

        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def risk_alerts(profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate risk alerts based on profile"""
        alerts = []

        try:
            monthly_income = profile.get("monthly_income", 0) // 100
            monthly_expenses = profile.get("monthly_expenses", 0) // 100
            emergency_fund = profile.get("emergency_fund", 0) // 100
            term_cover = profile.get("term_cover", 0) // 100
            health_cover = profile.get("health_cover", 0) // 100
            cc_outstanding = profile.get("cc_outstanding", 0) // 100

            # Emergency fund check
            emergency_months = emergency_fund / max(1, monthly_expenses)
            if emergency_months < 3:
                alerts.append({
                    "type": "critical",
                    "title": "Low Emergency Fund",
                    "message": f"Emergency fund covers only {emergency_months:.1f} months. Target: 6 months.",
                    "action": "Build emergency fund to 6 months of expenses"
                })

            # Insurance check
            if term_cover == 0:
                alerts.append({
                    "type": "high",
                    "title": "No Term Insurance",
                    "message": "Term insurance is essential for family protection.",
                    "action": "Get term insurance covering 10-15 years of income"
                })

            if health_cover < 300000:
                alerts.append({
                    "type": "medium",
                    "title": "Low Health Cover",
                    "message": f"Health cover is ₹{health_cover}. Recommended: ₹5-10 lakhs.",
                    "action": "Increase health insurance coverage"
                })

            # Debt check
            debt_ratio = (profile.get("monthly_emi", 0) // 100) / max(1, monthly_income)
            if debt_ratio > 0.5:
                alerts.append({
                    "type": "high",
                    "title": "High Debt Burden",
                    "message": f"Debt payments are {debt_ratio*100:.1f}% of income. Should be <40%.",
                    "action": "Reduce debt or increase income"
                })

            if cc_outstanding > 10000:
                alerts.append({
                    "type": "medium",
                    "title": "Credit Card Debt",
                    "message": f"Outstanding CC balance: ₹{cc_outstanding}. Pay off immediately.",
                    "action": "Clear credit card debt this month"
                })

            # Savings check
            savings_rate = (monthly_income - monthly_expenses) / max(1, monthly_income)
            if savings_rate < 0.1:
                alerts.append({
                    "type": "medium",
                    "title": "Low Savings Rate",
                    "message": f"Saving only {savings_rate*100:.1f}% of income. Target: 20%.",
                    "action": "Increase savings to 20% of monthly income"
                })

        except Exception as e:
            alerts.append({
                "type": "error",
                "title": "Analysis Error",
                "message": f"Could not analyze risks: {str(e)}",
                "action": "Please provide complete financial information"
            })

        return alerts