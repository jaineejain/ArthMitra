import uuid

from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, BigInteger, String, Text, TIMESTAMP, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=True)
    name = Column(String(100), nullable=True)
    age = Column(Integer, nullable=True)
    city = Column(String(50), nullable=True)
    is_salaried = Column(Boolean, nullable=False, default=True)
    monthly_income = Column(BigInteger, nullable=False, default=0)
    monthly_expenses = Column(BigInteger, nullable=False, default=0)
    monthly_emi = Column(BigInteger, nullable=False, default=0)
    risk_profile = Column(String(20), nullable=False, default="moderate")
    tax_regime = Column(String(10), nullable=False, default="new")
    created_at = Column(TIMESTAMP(timezone=False), nullable=True)

    financial_profile = relationship("FinancialProfile", back_populates="user", uselist=False)
    conversations = relationship("Conversation", back_populates="user", cascade="all,delete")
    chats = relationship("Chat", back_populates="user", cascade="all,delete-orphan")


class FinancialProfile(Base):
    __tablename__ = "financial_profile"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    emergency_fund = Column(BigInteger, nullable=False, default=0)
    total_investments = Column(BigInteger, nullable=False, default=0)
    monthly_sip = Column(BigInteger, nullable=False, default=0)
    term_cover = Column(BigInteger, nullable=False, default=0)
    health_cover = Column(BigInteger, nullable=False, default=0)
    epf_balance = Column(BigInteger, nullable=False, default=0)
    invested_80c = Column(BigInteger, nullable=False, default=0)
    has_nps = Column(Boolean, nullable=False, default=False)
    cc_outstanding = Column(BigInteger, nullable=False, default=0)
    equity_pct = Column(Float, nullable=False, default=0.7)
    mhs_score = Column(Integer, nullable=True)
    mhs_dimensions = Column(JSONB, nullable=True)
    updated_at = Column(TIMESTAMP(timezone=False), nullable=True)

    user = relationship("User", back_populates="financial_profile")


class Goal(Base):
    __tablename__ = "goals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=True)
    target_amount = Column(BigInteger, nullable=False, default=0)
    target_year = Column(Integer, nullable=True)
    monthly_sip = Column(BigInteger, nullable=False, default=0)
    goal_type = Column(String(30), nullable=True)


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    feature = Column(String(50), nullable=False)
    messages = Column(JSONB, nullable=False, default=list)
    created_at = Column(TIMESTAMP(timezone=False), nullable=True)

    user = relationship("User", back_populates="conversations")


class Chat(Base):
    """One row per (user, module) — normalized chat threads."""

    __tablename__ = "chats"
    __table_args__ = (UniqueConstraint("user_id", "module_name", name="uq_chats_user_module"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    module_name = Column(String(80), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=True)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=True)

    user = relationship("User", back_populates="chats")
    messages_rel = relationship("Message", back_populates="chat", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id", ondelete="CASCADE"), nullable=False, index=True)
    sender = Column(String(10), nullable=False)  # "user" | "ai"
    content = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=True)

    chat = relationship("Chat", back_populates="messages_rel")

