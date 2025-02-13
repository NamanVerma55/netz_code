from models import *
from secret_vars import *
from authenticate import *
from datetime import datetime, timedelta
from fastapi import FastAPI,Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, Secret_key, algorithm=algorithm)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, Secret_key, algorithms=[algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user(username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: dict = Depends(get_current_user)):
    if current_user["disabled"]:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


app=FastAPI()


@app.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection error")

    try:
        cur = conn.cursor()

        # Check if username or email already exists
        try:
            cur.execute("SELECT * FROM users WHERE username = %s OR email = %s", (user.username, user.email))
            existing_user = cur.fetchone()
            if existing_user:
                raise HTTPException(status_code=400, detail="Username or Email already exists")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database query error: {str(e)}")

        hashed_password = get_password_hash(user.password)

        # Insert new user into the database
        cur.execute(
            "INSERT INTO users (username, full_name, email, hashed_password) VALUES (%s, %s, %s, %s) RETURNING id",
            (user.username, user.full_name, user.email, hashed_password)
        )
        conn.commit()
        user_id = cur.fetchone()["id"]

        return {"message": "User registered successfully", "user_id": user_id}

    except HTTPException as http_exc:
        raise http_exc  # If it's an HTTP exception, re-raise it

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    finally:
        cur.close()
        conn.close()


@app.post("/token", response_model=Token,deprecated=True)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user["username"]}, expires_delta=access_token_expires)

    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


# @app.get("/users/me/generate-token")
# async def read_users_me(current_user: User = Depends(get_current_active_user),token_type:TokenType=TokenType.FREE):
#     # print(type(current_user))  # To check the type of current_user
#     user_data=User(**current_user)
#     access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token = create_access_token(data={"sub": user_data.username , "type":token_type}, expires_delta=access_token_expires)
#     with open("tokens.txt","a") as file:
#         file.write(f"{access_token}\n")
#     return {"message":"Token generated successfully"}




@app.get("/users/me/generate-token")
async def generate_token(
    current_user: User = Depends(get_current_active_user), 
    token_type: TokenType = TokenType.FREE
):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection error")

    try:
        cur = conn.cursor()

        # Check if a valid token of the same type already exists
        cur.execute(
            "SELECT access_token, expiry FROM user_tokens WHERE user_id = %s AND token_type = %s",
            (current_user["id"], token_type),
        )
        existing_token = cur.fetchone()
        

        if existing_token:
            token=dict(existing_token)
            expiry = token["expiry"]

            # Compare expiry with current time
            if datetime.now() < expiry:
                return {"message": "Token already exists"}

            # If expired, remove the old token
            cur.execute(
                "DELETE FROM user_tokens WHERE user_id = %s AND token_type = %s",
                (current_user["id"], token_type),
            )
            conn.commit()

        # Generate a new token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": current_user["username"], "type": token_type}, 
            expires_delta=access_token_expires
        )

        expiry_time = datetime.now() + access_token_expires

        # Save new token in the database
        cur.execute(
            "INSERT INTO user_tokens (user_id, access_token, token_type, expiry) VALUES (%s, %s, %s, %s)",
            (current_user["id"], access_token, token_type, expiry_time),
        )
        conn.commit()

        return {"message": "Token generated successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    finally:
        cur.close()
        conn.close()


@app.get("/users/me/view-tokens")
def view_tokens(current_user: User = Depends(get_current_active_user)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection error")

    try:
        cur = conn.cursor()
        cur.execute("SELECT access_token, token_type, expiry FROM user_tokens WHERE user_id = %s", (current_user["id"],))
        tokens = cur.fetchall()
        print(tokens)
        print(type(tokens))

        return {"tokens": tokens}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    finally:
        cur.close()
        conn.close()


@app.delete("/users/me/deactivate-token")
def delete_token(current_user: User = Depends(get_current_active_user), token: str = ""):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection error")
    try:
        cur = conn.cursor()

        # Ensure that the token is not empty
        if not token:
            raise HTTPException(status_code=400, detail="No token provided")

        # Check if the token exists for the current user
        cur.execute("SELECT access_token FROM user_tokens WHERE access_token = %s AND user_id = %s", (token, current_user["id"]))
        existing_token = cur.fetchone()

        if not existing_token:
            raise HTTPException(status_code=404, detail="Token not found")

        # Deactivate the token by deleting it from the table
        cur.execute("DELETE FROM user_tokens WHERE access_token = %s", (token,))
        conn.commit()

        return {"message": "Token deactivated successfully"}

    except Exception as e:
        raise e
    
    finally:
        cur.close()
        conn.close()


@app.post("/test")
def test(token: str, lst: list):
    return {"message": "Test successful"}