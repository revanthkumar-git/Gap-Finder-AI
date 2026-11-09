from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Message, Meeting, Task
from app.auth import get_current_user, log_audit_event
from app.schemas import MessageResponse, MessageCreate, MeetingResponse, TaskResponse, TaskUpdate

router = APIRouter(prefix="/comm", tags=["Communications, Meetings & Tasks"])

# Messages
@router.get("/messages", response_model=List[MessageResponse])
def get_messages(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    msgs = db.query(Message).filter(
        (Message.sender_id == current_user.id) | (Message.recipient_id == current_user.id)
    ).order_by(Message.created_at.desc()).all()

    # Fallback to all messages if none for demo
    if not msgs:
        msgs = db.query(Message).order_by(Message.created_at.desc()).all()

    res = []
    for m in msgs:
        sender = db.query(User).filter(User.id == m.sender_id).first()
        sender_name = sender.full_name if sender else "Nexqile Advisory"
        res.append(MessageResponse(
            id=m.id,
            sender_id=m.sender_id,
            sender_name=sender_name,
            recipient_id=m.recipient_id,
            subject=m.subject,
            body=m.body,
            is_read=m.is_read,
            created_at=m.created_at
        ))
    return res

@router.post("/messages", response_model=MessageResponse)
def send_message(msg_in: MessageCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    msg = Message(
        sender_id=current_user.id,
        recipient_id=msg_in.recipient_id,
        subject=msg_in.subject,
        body=msg_in.body,
        is_read=False,
        created_at=datetime.utcnow()
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    log_audit_event(db, action="SEND_MESSAGE", user=current_user, details=f"Sent message: {msg.subject}")

    return MessageResponse(
        id=msg.id,
        sender_id=msg.sender_id,
        sender_name=current_user.full_name,
        recipient_id=msg.recipient_id,
        subject=msg.subject,
        body=msg.body,
        is_read=msg.is_read,
        created_at=msg.created_at
    )

# Meetings
@router.get("/meetings", response_model=List[MeetingResponse])
def get_meetings(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    meetings = db.query(Meeting).order_by(Meeting.meeting_date.asc()).all()
    res = []
    for m in meetings:
        advisor_name = "Eleanor Vance, CFP®, CFA"
        if m.advisor and m.advisor.user:
            advisor_name = m.advisor.user.full_name

        res.append(MeetingResponse(
            id=m.id,
            title=m.title,
            advisor_name=advisor_name,
            meeting_date=m.meeting_date,
            duration_minutes=m.duration_minutes,
            location=m.location,
            status=m.status,
            agenda=m.agenda,
            prep_notes=m.prep_notes
        ))
    return res

# Tasks
@router.get("/tasks", response_model=List[TaskResponse])
def get_tasks(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tasks = db.query(Task).all()
    return tasks

@router.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task_in: TaskUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task_in.status is not None:
        task.status = task_in.status
    if task_in.title is not None:
        task.title = task_in.title
    if task_in.priority is not None:
        task.priority = task_in.priority

    db.commit()
    db.refresh(task)
    log_audit_event(db, action="UPDATE_TASK", user=current_user, entity_type="Task", entity_id=str(task_id), details=f"Status changed to {task.status}")
    return task
