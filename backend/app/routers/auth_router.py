from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Client
from app.schemas import LoginRequest, RegisterRequest, Token, UserResponse
from app.auth import verify_password, hash_password, create_access_token, get_current_user, log_audit_event
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
def login(creds: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == creds.email).first()
    if not user or not verify_password(creds.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account is disabled")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": user.email, "role": user.role_name, "user_id": user.id},
        expires_delta=access_token_expires
    )

    log_audit_event(db, action="USER_LOGIN", user=user, details=f"User {user.email} logged in with role {user.role_name}")

    user_resp = UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role_name=user.role_name,
        avatar_url=user.avatar_url,
        is_active=user.is_active
    )
    return {"access_token": token, "token_type": "bearer", "user": user_resp}
 
@router.post("/register", response_model=Token)
def register(creds: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == creds.email.strip().lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Please sign in instead."
        )
    
    if len(creds.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters in length."
        )
    
    role = (creds.role_name or "client").lower().strip()
    if role not in ["client", "advisor", "sponsor", "participant", "admin"]:
        role = "client"

    hashed_pw = hash_password(creds.password)
    new_user = User(
        email=creds.email.strip().lower(),
        hashed_password=hashed_pw,
        full_name=creds.full_name.strip(),
        role_name=role,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    if role == "client":
        new_client = Client(
            user_id=new_user.id,
            risk_tolerance="Balanced Growth",
            net_worth=500000.0,
            invested_assets=420000.0,
            cash_balance=80000.0,
            retirement_assets=250000.0,
            ytd_return=8.12,
            tax_bracket="24% Federal, 5.0% State",
            status="Active"
        )
        db.add(new_client)
        db.commit()

    log_audit_event(db, action="USER_REGISTER", user=new_user, details=f"New user registered: {new_user.email} (Role: {new_user.role_name})")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": new_user.email, "role": new_user.role_name, "user_id": new_user.id},
        expires_delta=access_token_expires
    )

    user_resp = UserResponse(
        id=new_user.id,
        email=new_user.email,
        full_name=new_user.full_name,
        role_name=new_user.role_name,
        avatar_url=new_user.avatar_url,
        is_active=new_user.is_active
    )
    return {"access_token": token, "token_type": "bearer", "user": user_resp}

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/logout")
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    log_audit_event(db, action="USER_LOGOUT", user=current_user, details=f"User {current_user.email} logged out")
    return {"message": "Successfully logged out"}

@router.get("/demo-credentials")
def get_demo_credentials():
    return {
        "accounts": [
            {"role": "Client", "email": "client@nexqile.demo", "password": "Demo@123", "desc": "Alexander Mercer - High Net Worth Individual ($2.84M)"},
            {"role": "Financial Advisor", "email": "advisor@nexqile.demo", "password": "Demo@123", "desc": "Eleanor Vance, CFP®, CFA - Managing Principal ($148.5M AUM)"},
            {"role": "Institutional Sponsor", "email": "sponsor@nexqile.demo", "password": "Demo@123", "desc": "Marcus Sterling - Apex Global 401(k) Plan Fiduciary"},
            {"role": "Participant", "email": "participant@nexqile.demo", "password": "Demo@123", "desc": "Sophia Chen - 401(k) Plan Member ($248.5K Balance)"},
            {"role": "Administrator", "email": "admin@nexqile.demo", "password": "Demo@123", "desc": "David Chen - Enterprise Compliance & Security Admin"},
        ]
    }
