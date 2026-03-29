CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(100),
  age INTEGER,
  city VARCHAR(50),
  is_salaried BOOLEAN DEFAULT true,
  monthly_income BIGINT DEFAULT 0,
  monthly_expenses BIGINT DEFAULT 0,
  monthly_emi BIGINT DEFAULT 0,
  risk_profile VARCHAR(20) DEFAULT 'moderate',
  tax_regime VARCHAR(10) DEFAULT 'new',
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS financial_profile (
  user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  emergency_fund BIGINT DEFAULT 0,
  total_investments BIGINT DEFAULT 0,
  monthly_sip BIGINT DEFAULT 0,
  term_cover BIGINT DEFAULT 0,
  health_cover BIGINT DEFAULT 0,
  epf_balance BIGINT DEFAULT 0,
  invested_80c BIGINT DEFAULT 0,
  has_nps BOOLEAN DEFAULT false,
  cc_outstanding BIGINT DEFAULT 0,
  equity_pct FLOAT DEFAULT 0.7,
  mhs_score INTEGER,
  mhs_dimensions JSONB,
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS goals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR(100),
  target_amount BIGINT,
  target_year INTEGER,
  monthly_sip BIGINT DEFAULT 0,
  goal_type VARCHAR(30)
);

CREATE TABLE IF NOT EXISTS conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  feature VARCHAR(50) NOT NULL,
  messages JSONB DEFAULT '[]',
  created_at TIMESTAMP DEFAULT NOW()
);

