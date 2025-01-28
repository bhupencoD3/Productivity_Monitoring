from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from PIL import Image
from app.service.user_service import UserService
import io

router = APIRouter()
user_service = UserService()


@router.post("/add_employee/")
async def add_employee(name: str = Form(...), file: UploadFile = File(...)):
    """
    Add a new employee's embedding to the Milvus database.
    """
    try:
        image = Image.open(io.BytesIO(await file.read())).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file")
    message = user_service.add_employee(name, image)
    return {"message": message}


@router.get("/list_employees/")
async def list_employees():
    """
    List all employees in the database.
    """
    employees = user_service.list_employees()
    return {"employees": employees}


@router.delete("/delete_employee/{name}")
async def delete_employee(name: str):
    """
    Delete an employee from the database by name.
    """
    message = user_service.delete_employee(name)
    return {"message": message}


@router.post("/search_employee/")
async def search_employee(file: UploadFile = File(...)):
    """
    Search for an employee using an image.
    """
    try:
        image = Image.open(io.BytesIO(await file.read())).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file")
    result = user_service.search_employee(image)
    return result
