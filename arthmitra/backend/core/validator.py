"""
ArthMitra AI - Input Validation Module
All input validation and sanitization happens here
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime


class ArthMitraValidator:
    """Central validator for all user inputs"""

    @staticmethod
    def validate_financial_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize financial profile data"""
        errors = []
        warnings = []
        sanitized = {}

        try:
            # Age validation
            age = profile.get("age")
            if age is None:
                errors.append("Age is required")
            elif not isinstance(age, (int, float)) or age < 18 or age > 100:
                errors.append("Age must be between 18 and 100")
            else:
                sanitized["age"] = int(age)

            # Income validation
            monthly_income = profile.get("monthly_income")
            if monthly_income is None:
                errors.append("Monthly income is required")
            elif not isinstance(monthly_income, (int, float)) or monthly_income < 0:
                errors.append("Monthly income must be a positive number")
            elif monthly_income > 10000000:  # 1 crore per month
                warnings.append("Monthly income seems unusually high")
                sanitized["monthly_income"] = int(monthly_income)
            else:
                sanitized["monthly_income"] = int(monthly_income)

            # Expenses validation
            monthly_expenses = profile.get("monthly_expenses")
            if monthly_expenses is None:
                errors.append("Monthly expenses is required")
            elif not isinstance(monthly_expenses, (int, float)) or monthly_expenses < 0:
                errors.append("Monthly expenses must be a positive number")
            else:
                sanitized["monthly_expenses"] = int(monthly_expenses)

                # Check if expenses > income
                if monthly_income and monthly_expenses > monthly_income:
                    warnings.append("Monthly expenses exceed income - consider reducing expenses")

            # EMI validation
            monthly_emi = profile.get("monthly_emi", 0)
            if not isinstance(monthly_emi, (int, float)) or monthly_emi < 0:
                errors.append("Monthly EMI must be a non-negative number")
            else:
                sanitized["monthly_emi"] = int(monthly_emi)

            # Emergency fund validation
            emergency_fund = profile.get("emergency_fund", 0)
            if not isinstance(emergency_fund, (int, float)) or emergency_fund < 0:
                errors.append("Emergency fund must be a non-negative number")
            else:
                sanitized["emergency_fund"] = int(emergency_fund)

            # SIP validation
            monthly_sip = profile.get("monthly_sip", 0)
            if not isinstance(monthly_sip, (int, float)) or monthly_sip < 0:
                errors.append("Monthly SIP must be a non-negative number")
            else:
                sanitized["monthly_sip"] = int(monthly_sip)

            # Insurance validation
            term_cover = profile.get("term_cover", 0)
            if not isinstance(term_cover, (int, float)) or term_cover < 0:
                errors.append("Term cover must be a non-negative number")
            else:
                sanitized["term_cover"] = int(term_cover)

            health_cover = profile.get("health_cover", 0)
            if not isinstance(health_cover, (int, float)) or health_cover < 0:
                errors.append("Health cover must be a non-negative number")
            else:
                sanitized["health_cover"] = int(health_cover)

            # Credit card outstanding
            cc_outstanding = profile.get("cc_outstanding", 0)
            if not isinstance(cc_outstanding, (int, float)) or cc_outstanding < 0:
                errors.append("Credit card outstanding must be a non-negative number")
            else:
                sanitized["cc_outstanding"] = int(cc_outstanding)

            # Tax-related fields
            annual_gross = profile.get("annual_gross")
            if annual_gross is not None:
                if not isinstance(annual_gross, (int, float)) or annual_gross < 0:
                    errors.append("Annual gross must be a non-negative number")
                else:
                    sanitized["annual_gross"] = int(annual_gross)

            basic_salary = profile.get("basic_salary")
            if basic_salary is not None:
                if not isinstance(basic_salary, (int, float)) or basic_salary < 0:
                    errors.append("Basic salary must be a non-negative number")
                else:
                    sanitized["basic_salary"] = int(basic_salary)

            # HRA and rent
            hra_received = profile.get("hra_received", 0)
            if not isinstance(hra_received, (int, float)) or hra_received < 0:
                errors.append("HRA received must be a non-negative number")
            else:
                sanitized["hra_received"] = int(hra_received)

            rent_paid = profile.get("rent_paid", 0)
            if not isinstance(rent_paid, (int, float)) or rent_paid < 0:
                errors.append("Rent paid must be a non-negative number")
            else:
                sanitized["rent_paid"] = int(rent_paid)

            # City type
            city_type = profile.get("city_type", "metro")
            if city_type not in ["metro", "non-metro"]:
                warnings.append("City type should be 'metro' or 'non-metro'")
                sanitized["city_type"] = "metro"
            else:
                sanitized["city_type"] = city_type

            # Investment fields
            total_investments = profile.get("total_investments", 0)
            if not isinstance(total_investments, (int, float)) or total_investments < 0:
                errors.append("Total investments must be a non-negative number")
            else:
                sanitized["total_investments"] = int(total_investments)

            equity_pct = profile.get("equity_pct", 0.5)
            if not isinstance(equity_pct, (int, float)) or equity_pct < 0 or equity_pct > 1:
                errors.append("Equity percentage must be between 0 and 1")
            else:
                sanitized["equity_pct"] = float(equity_pct)

            # Deductions
            used_80c = profile.get("used_80c", 0)
            if not isinstance(used_80c, (int, float)) or used_80c < 0 or used_80c > 150000:
                errors.append("80C deduction must be between 0 and 150000")
            else:
                sanitized["used_80c"] = int(used_80c)

            health_premium = profile.get("health_premium", 0)
            if not isinstance(health_premium, (int, float)) or health_premium < 0 or health_premium > 25000:
                errors.append("Health premium must be between 0 and 25000")
            else:
                sanitized["health_premium"] = int(health_premium)

            nps_tier1 = profile.get("nps_tier1", 0)
            if not isinstance(nps_tier1, (int, float)) or nps_tier1 < 0 or nps_tier1 > 50000:
                errors.append("NPS Tier 1 must be between 0 and 50000")
            else:
                sanitized["nps_tier1"] = int(nps_tier1)

            # FIRE fields
            target_retirement_age = profile.get("target_retirement_age", 60)
            if not isinstance(target_retirement_age, (int, float)) or target_retirement_age < 40 or target_retirement_age > 80:
                errors.append("Target retirement age must be between 40 and 80")
            else:
                sanitized["target_retirement_age"] = int(target_retirement_age)

        except Exception as e:
            errors.append(f"Validation error: {str(e)}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "sanitized": sanitized if len(errors) == 0 else {}
        }

    @staticmethod
    def validate_portfolio(portfolio: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate mutual fund portfolio data"""
        errors = []
        warnings = []
        sanitized = []

        try:
            if not isinstance(portfolio, list):
                errors.append("Portfolio must be a list of funds")
                return {"valid": False, "errors": errors, "warnings": warnings, "sanitized": []}

            if len(portfolio) > 20:
                warnings.append("Portfolio has many funds - consider consolidation")

            for i, fund in enumerate(portfolio):
                fund_errors = []
                fund_data = {}

                # Fund name
                name = fund.get("name", "").strip()
                if not name:
                    fund_errors.append(f"Fund {i+1}: Name is required")
                elif len(name) > 100:
                    fund_errors.append(f"Fund {i+1}: Name too long")
                else:
                    fund_data["name"] = name

                # Fund type
                fund_type = fund.get("type", "").strip().lower()
                valid_types = ["equity", "debt", "hybrid", "elss", "liquid", "gold", "international"]
                if not fund_type:
                    fund_errors.append(f"Fund {i+1}: Type is required")
                elif fund_type not in valid_types:
                    fund_errors.append(f"Fund {i+1}: Invalid fund type. Must be one of: {', '.join(valid_types)}")
                else:
                    fund_data["type"] = fund_type

                # Invested amount
                invested = fund.get("invested")
                if invested is None:
                    fund_errors.append(f"Fund {i+1}: Invested amount is required")
                elif not isinstance(invested, (int, float)) or invested < 0:
                    fund_errors.append(f"Fund {i+1}: Invested amount must be a positive number")
                else:
                    fund_data["invested"] = int(invested)

                # Current value
                current = fund.get("current")
                if current is None:
                    fund_errors.append(f"Fund {i+1}: Current value is required")
                elif not isinstance(current, (int, float)) or current < 0:
                    fund_errors.append(f"Fund {i+1}: Current value must be a positive number")
                else:
                    fund_data["current"] = int(current)

                if fund_errors:
                    errors.extend(fund_errors)
                else:
                    sanitized.append(fund_data)

        except Exception as e:
            errors.append(f"Portfolio validation error: {str(e)}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "sanitized": sanitized
        }

    @staticmethod
    def validate_life_event(event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate life event data"""
        errors = []
        warnings = []
        sanitized = {}

        try:
            valid_events = ["bonus", "job_change", "marriage", "baby", "retirement", "education", "house_purchase"]
            if event_type not in valid_events:
                errors.append(f"Invalid event type. Must be one of: {', '.join(valid_events)}")
                return {"valid": False, "errors": errors, "warnings": warnings, "sanitized": {}}

            if event_type == "bonus":
                amount = event_data.get("amount")
                if amount is None:
                    errors.append("Bonus amount is required")
                elif not isinstance(amount, (int, float)) or amount < 0:
                    errors.append("Bonus amount must be a positive number")
                else:
                    sanitized["amount"] = int(amount)

            elif event_type == "job_change":
                new_salary = event_data.get("new_salary")
                if new_salary is None:
                    errors.append("New salary is required")
                elif not isinstance(new_salary, (int, float)) or new_salary < 0:
                    errors.append("New salary must be a positive number")
                else:
                    sanitized["new_salary"] = int(new_salary)

            elif event_type == "baby":
                expected_year = event_data.get("expected_year", datetime.now().year)
                if not isinstance(expected_year, int) or expected_year < datetime.now().year or expected_year > datetime.now().year + 5:
                    warnings.append("Expected year seems unusual")
                    sanitized["expected_year"] = expected_year
                else:
                    sanitized["expected_year"] = expected_year

            # Generic validation for all events
            description = event_data.get("description", "").strip()
            if len(description) > 500:
                errors.append("Description too long (max 500 characters)")
            else:
                sanitized["description"] = description

        except Exception as e:
            errors.append(f"Life event validation error: {str(e)}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "sanitized": sanitized
        }

    @staticmethod
    def validate_couple_profiles(partner1: Dict[str, Any], partner2: Dict[str, Any]) -> Dict[str, Any]:
        """Validate couple financial profiles"""
        errors = []
        warnings = []

        # Validate both profiles
        p1_validation = ArthMitraValidator.validate_financial_profile(partner1)
        p2_validation = ArthMitraValidator.validate_financial_profile(partner2)

        errors.extend(p1_validation["errors"])
        errors.extend(p2_validation["errors"])
        warnings.extend(p1_validation["warnings"])
        warnings.extend(p2_validation["warnings"])

        # Couple-specific validations
        if p1_validation["valid"] and p2_validation["valid"]:
            p1_income = p1_validation["sanitized"].get("monthly_income", 0)
            p2_income = p2_validation["sanitized"].get("monthly_income", 0)

            if p1_income + p2_income < 20000:  # Very low combined income
                warnings.append("Combined monthly income is quite low for financial planning")

            # Check for unrealistic income disparity
            ratio = max(p1_income, p2_income) / max(1, min(p1_income, p2_income))
            if ratio > 10:
                warnings.append("Large income disparity between partners - consider separate planning")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "partner1": p1_validation["sanitized"] if p1_validation["valid"] else {},
            "partner2": p2_validation["sanitized"] if p2_validation["valid"] else {}
        }

    @staticmethod
    def sanitize_text_input(text: str, max_length: int = 1000) -> str:
        """Sanitize text input by removing harmful content"""
        if not isinstance(text, str):
            return ""

        # Remove null bytes and other control characters
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)

        # Limit length
        if len(text) > max_length:
            text = text[:max_length] + "..."

        # Basic XSS prevention (remove script tags)
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<[^>]+>', '', text)  # Remove all HTML tags

        return text.strip()

    @staticmethod
    def validate_api_request(request_data: Dict[str, Any], required_fields: List[str]) -> Dict[str, Any]:
        """Validate API request data"""
        errors = []
        missing_fields = []

        for field in required_fields:
            if field not in request_data or request_data[field] is None:
                missing_fields.append(field)

        if missing_fields:
            errors.append(f"Missing required fields: {', '.join(missing_fields)}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "missing_fields": missing_fields
        }

    @staticmethod
    def validate_calculation_request(feature: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate calculation requests for different features"""
        errors = []
        warnings = []

        try:
            if feature == "mhs":
                required = ["age", "monthly_income", "monthly_expenses"]
                validation = ArthMitraValidator.validate_api_request(data, required)
                if not validation["valid"]:
                    errors.extend(validation["errors"])

            elif feature == "tax":
                required = ["annual_gross", "basic_salary"]
                validation = ArthMitraValidator.validate_api_request(data, required)
                if not validation["valid"]:
                    errors.extend(validation["errors"])

            elif feature == "fire":
                required = ["age", "monthly_income", "monthly_expenses"]
                validation = ArthMitraValidator.validate_api_request(data, required)
                if not validation["valid"]:
                    errors.extend(validation["errors"])

            elif feature == "portfolio":
                if "portfolio" not in data:
                    errors.append("Portfolio data is required")
                else:
                    portfolio_validation = ArthMitraValidator.validate_portfolio(data["portfolio"])
                    if not portfolio_validation["valid"]:
                        errors.extend(portfolio_validation["errors"])
                    warnings.extend(portfolio_validation["warnings"])

            elif feature == "couple":
                if "partner1" not in data or "partner2" not in data:
                    errors.append("Both partner profiles are required")
                else:
                    couple_validation = ArthMitraValidator.validate_couple_profiles(
                        data["partner1"], data["partner2"]
                    )
                    if not couple_validation["valid"]:
                        errors.extend(couple_validation["errors"])
                    warnings.extend(couple_validation["warnings"])

            elif feature == "life_event":
                if "event_type" not in data:
                    errors.append("Event type is required")
                else:
                    event_validation = ArthMitraValidator.validate_life_event(
                        data["event_type"], data.get("event_data", {})
                    )
                    if not event_validation["valid"]:
                        errors.extend(event_validation["errors"])
                    warnings.extend(event_validation["warnings"])

            else:
                errors.append(f"Unknown feature: {feature}")

        except Exception as e:
            errors.append(f"Request validation error: {str(e)}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }