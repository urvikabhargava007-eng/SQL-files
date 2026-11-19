from fastapi import FastAPI, Depends, Response,status
from sqlmodel import SQLModel, Field, create_engine, select, Session
from pydantic import BaseModel
from pydantic import Field as Pyd_field
import bcrypt
import jwt
from datetime import datetime , timedelta

class BankAccount(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(nullable=False,unique=True, min_length=3, max_length=50)
    password: str = Field(nullable=False)
    mob: str = Field(nullable=False, unique=True, min_length=10, max_length=10)
    age: int = Field(nullable=False, gt=18, le=150)
    dob: str = Field(nullable=False)
    balance: float = Field(nullable=False, gt=0)

my_secret_key = "catalystprogrammers" #line79

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

class Withdraw(BaseModel):
    mob: str = Field(nullable=False, min_length=10, max_length=10)
    amount: float = Field(nullable=False, gt=0)

class AuthInfo(BaseModel):
    username: str = Field(nullable=False, min_length=3, max_length=50)
    password: str = Field(nullable=False, min_length=6)

# @app.post("/login")
# def login(auth_info: AuthInfo, res: Response, db: Session = Depends(tr_func)):
#     user_info = db.exec(select(BankAccount).filter(BankAccount.name == auth_info.username)).one_or_none()
#     if bcrypt.checkpw(auth_info.password.encode(), user_info.password.encode()):
#         return True
#     else:
#         res.status_code = status.HTTP_401_UNAUTHORIZED
#         return {
#             "Status": False, 
#             "Message": "Invalid username or password."
#             }

@app.post("/login")
def login(user_info: AuthInfo, resp:Response, db: Session = Depends(tr_func)):
    user_info_from_db = db.exec(select(BankAccount).filter(BankAccount.name == user_info.username)).one_or_none()
    if not user_info_from_db:
        resp.status_code = status.HTTP_401_UNAUTHORIZED
        return {
            "Status": False,
            "access_token": "", 
            "Message": "Invalid username or password."
            }
    
    if bcrypt.checkpw(user_info.password.encode(), user_info_from_db.password.encode()):
         data= {
             "username": user_info_from_db.name,
             "mob": user_info_from_db.mob,
             "exp":datetime.now() + timedelta(minutes=1)
             }
         token = jwt.encode(data, my_secret_key,"HS256")

         return {
             "Status": True,
             "access_token": token,
             "Message": "Login successful."
         }
    else:
        return {
            "Status": False, 
            "Message": "Invalid username or password."
            }

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/get_users")
def get_users( db: Session = Depends(tr_func)):
   
   data = db.exec(select(BankAccount)).all()
   data = [{"name": user.name, "mob": user.mob, "age": user.age, "dob": user.dob, "balance": user.balance} for user in data]
   return {
       "status": True,
       "message": "Users retrieved successfully.",
         "data": data
   }

@app.get("/get_user_by_id/{id:int}")
def get_user_by_id(id:int, db: Session = Depends(tr_func)):
    data = db.exec(select(BankAccount).filter(BankAccount.id == id)).one_or_none()
    if data: 
        return {
            "Status": True, 
            "Message": "User found successfully.",
            "data" : {"name": data.name, "mob": data.mob, "age": data.age, "dob": data.dob, "balance": data.balance}}
    else:
        return {
            "Status": False, 
            "Message": "User not found."
            }
       

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

    res.status_code = status.HTTP_201_CREATED 
    return {
            "Status": True, 
            "Message": "User created successfully."
        }

   except:
    res.status_code = status.HTTP_400_BAD_REQUEST
    return {
        "Status": False, 
        "Message": "User creation failed. Please check the input data."
    } 
    

@app.post("/deposit/{mob}")
def deposit(req_data: Deposits, res: Response, db: Session = Depends(tr_func)):
        user = db.exec(select(BankAccount).filter(BankAccount.mob == req_data.mob)).one_or_none()
        if not user:
            res.status_code = status.HTTP_400_BAD_REQUEST
            return {"Status": False, 
                    "Message": "Invalid mobile number."
                    }
        else:
            user.balance += req_data.amount
            db.add(user)
            db.commit()
            db.refresh(user)

        return {
        "Status": True,
        "Message": f"Deposit successful. New balance is {req_data.amount}."
    }

@app.patch("/withdraw/{mob}")   
def withdraw(req_data: Withdraw, res: Response, db: Session = Depends(tr_func)):
        user = db.exec(select(BankAccount).filter(BankAccount.mob == req_data.mob)).one_or_none()
        if not user:
            res.status_code = status.HTTP_400_BAD_REQUEST
            return {"Status": False, 
                    "Message": "Invalid mobile number."
                    }
        
        if user.balance < req_data.amount:
            res.status_code = status.HTTP_400_BAD_REQUEST
            return {"Status": False, 
                    "Message": "Insufficient balance."
                    }
        
        user.balance -= req_data.amount
        db.add(user)
        db.commit()
        db.refresh(user)

        return {
            "Status": True,
            "Message": f"Withdrawal successful. New balance is {user.balance}."
        }



   