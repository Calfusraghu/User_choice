from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Annotated
import models
import logging
from database import engine, SessionLocal
from sqlalchemy.orm import session, Session

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

app = FastAPI()
models.Base.metadata.create_all(
    bind=engine)  # creates all the tables in the database but also need connection to databse

logger.info(f'FILE MAIN.PY')
logger.log(logging.WARNING, 'FROM MAIN.PY')


#Pydantic model
class ChoiceBase(BaseModel):
    choice_txt: str
    is_correct: bool


class QuestionBase(BaseModel):
    question_text: str
    choice: List[ChoiceBase]


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


@app.get("/health")
async def check_database_connection():
    logger.info(f'FUNCTION check_database_connection')
    return {"status": "healthy"}


#as we passed QuestionBase as type it will validate request body
@app.post("/question/")
async def create_question(question: QuestionBase, db: db_dependency):
    logger.info(f'FUNCTION create_question')
    try:
        db_question = models.Question(question_text=question.question_text)
        db.add(db_question)
        db.commit()
        db.refresh(db_question)

        for choice in question.choice:
            db_choice = models.Choices(choice_txt=choice.choice_txt, is_correct=choice.is_correct,
                                       question_id=db_question.id)
            db.add(db_choice)
        db.commit()

        return {"message": "Question created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating question: {str(e)}")
