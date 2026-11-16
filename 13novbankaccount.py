from fastapi import FastAPI, Depends, Response,status
from sqlmodel import SQLModel, Field, create_engine, select, Session
from pydantic import BaseModel
from pydantic import Field as Pyd_field
import bcrypt

class BankAccount(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(nullable=False)
    password: str = Field(nullable=False)
    mob: str = Field(nullable=False, unique=True, min_length=10, max_length=10)
    age: int = Field(nullable=False, gt=18, le=150)
    dob: str = Field(nullable=False)
    balance: float = Field(nullable=False, gt=0)

engine = create_engine("sqlite:///13novbank.db")
def tr_func():
    with Session(engine) as db:
        yield db

SQLModel.metadata.create_all(engine)
# db=Session(engine)

app = FastAPI()

class CreateAccount(BaseModel):
    name: str = Field(nullable=False, min_length=3, max_length=50)
    password: str = Field(nullable=False, min_length=6)
    mob: str = Field(nullable=False, min_length=10, max_length=10)
    age: int = Field(nullable=False, gt=18, le=150)
    dob: str = Field(nullable=False)
    balance: float = Field(nullable=False, gt=0)

class Deposits(BaseModel):
    mob: str = Field(nullable=False, min_length=10, max_length=10)
    amount: float = Field(nullable=False, gt=0)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/create_user")
def create_user(user_data: CreateAccount, res: Response, db: Session = Depends(tr_func)): 
   try:  
    user = BankAccount(
        name=user_data.name,
        password=bcrypt.hashpw(user_data.password.encode(), bcrypt.gensalt()),
        mob=user_data.mob,
        age=user_data.age,
        dob=user_data.dob,
        balance=user_data.balance
    )  
    db.add(user)
    db.commit()
    db.refresh(user)

   except Exception as e:
    res.status_code = status.HTTP_400_BAD_REQUEST
    return {
        "Status": False, 
        "Message": "User creation failed. Please check the input data."
    } 
    res.status_code = status.HTTP_201_CREATED 
    return {
        "Status": True, 
        "Message": "User created successfully."
    }

@app.post("/deposit/{mob}")
def deposit(req_data: Deposits, amount: float, res: Response, db: Session = Depends(tr_func)):
    try:
        user = db.exec(select(BankAccount).filter(BankAccount.mob == mob)).one_or_none()
        if not user:
            res.status_code = status.HTTP_404_NOT_FOUND
            return {"Status": False, "Message": "User not found."}
        
        if amount <= 0:
            res.status_code = status.HTTP_400_BAD_REQUEST
            return {"Status": False, "Message": "Deposit amount must be greater than zero."}
        
        user.balance += amount
        db.add(user)
        db.commit()
        db.refresh(user)
        
    except Exception as e:
        res.status_code = status.HTTP_400_BAD_REQUEST
        return {
            "Status": False,
            "Message": "Deposit failed. Please check the input data."
        }
    
    res.status_code = status.HTTP_200_OK
    return {
        "Status": True,
        "Message": f"Deposit successful. New balance is {user.balance}."
    }

    




   