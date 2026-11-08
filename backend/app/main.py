import json
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import select
from .db import Base, engine, get_db
from .models import User, Profile, Report, ProfileChange
from .schemas import UserCreate, Token, ReportCreate, ReportOut, ProfileOut, ProfileChangeOut
from .security import hash_password, verify_password, create_access_token
from .dependencies import current_user, reviewer_user

Base.metadata.create_all(bind=engine)  # Replace with Alembic migrations before production.

app = FastAPI(title="TrollWatch API", version="0.1.0",
              description="Facebook-focused prototype API. Unverified reports are never public.")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/auth/register", status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(email=payload.email, password_hash=hash_password(payload.password), role="user")
    db.add(user)
    db.commit()
    return {"id": user.id, "email": user.email, "role": user.role}

@app.post("/auth/token", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == form.username))
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return Token(access_token=create_access_token(str(user.id)))

@app.post("/reports", response_model=ReportOut, status_code=201)
def create_report(payload: ReportCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    url = str(payload.profile_url)
    profile = db.scalar(select(Profile).where(Profile.profile_url == url))
    if not profile:
        profile = Profile(profile_url=url, current_name=payload.profile_name, platform="facebook")
        db.add(profile)
        db.flush()
    report = Report(
        profile_id=profile.id, reporter_id=user.id,
        reason_category=payload.reason_category,
        description=payload.description,
        evidence_urls=json.dumps([str(u) for u in payload.evidence_urls]),
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report

@app.get("/profiles/flagged", response_model=list[ProfileOut])
def flagged_profiles(db: Session = Depends(get_db)):
    return list(db.scalars(select(Profile).where(Profile.status.in_(["confirmed_network", "documented"]))).all())

@app.get("/profiles/{profile_id}/history", response_model=list[ProfileChangeOut])
def profile_history(profile_id: int, db: Session = Depends(get_db)):
    profile = db.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return list(db.scalars(select(ProfileChange).where(ProfileChange.profile_id == profile_id).order_by(ProfileChange.observed_at.desc())).all())

@app.get("/admin/reports")
def pending_reports(_: User = Depends(reviewer_user), db: Session = Depends(get_db)):
    return list(db.scalars(select(Report).where(Report.status == "pending").order_by(Report.created_at.asc())).all())

@app.post("/admin/reports/{report_id}/decision")
def decide_report(report_id: int, decision: str, rationale: str,
                  reviewer: User = Depends(reviewer_user), db: Session = Depends(get_db)):
    if decision not in {"documented", "confirmed_network", "linked", "rejected", "needs_evidence"}:
        raise HTTPException(status_code=422, detail="Unsupported decision")
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    report.status = decision
    if decision in {"documented", "confirmed_network"}:
        profile = db.get(Profile, report.profile_id)
        profile.status = decision
    db.commit()
    return {"report_id": report_id, "decision": decision, "reviewer_id": reviewer.id,
            "rationale": rationale, "decided_at": datetime.now(timezone.utc).isoformat()}
