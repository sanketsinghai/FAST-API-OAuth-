from fastapi import FastAPI, Request, Depends
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Add session middleware for managing user sessions
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"))

# Set up templates
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# OAuth configuration
oauth = OAuth()
# oauth.register(
#     name="google",
#     client_id=os.getenv("GOOGLE_CLIENT_ID"),
#     client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
#     access_token_url="https://oauth2.googleapis.com/token",
#     access_token_params=None,
#     authorize_url="https://accounts.google.com/o/oauth2/auth",
#     authorize_params=None,
#     api_base_url="https://www.googleapis.com/oauth2/v1/",
#     client_kwargs={"scope": "openid email profile"},
# )

oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile"
    }
)


# Home route
@app.get("/")
async def homepage(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Login route
@app.get("/auth/login")
async def login(request: Request):
    redirect_uri = "http://localhost:8000/auth/callback"  # Ensure this matches the Google Cloud Console
    return await oauth.google.authorize_redirect(request, redirect_uri)


# Callback route
@app.get("/auth/callback")
async def auth_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    if token:
        user_info = token.get("userinfo", {})
        user_name = user_info.get("name")
        email = user_info.get("email")

        # Store user information in session
        request.session["user"] = {"name": user_name, "email": email}

        # Print token and user info for debugging
        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        print(token)
        print(user_info)
        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")

    return templates.TemplateResponse("post_login.html", {"request": request, "user": user_name})


@app.get("/post_login")
async def post_login(request: Request):
    user = request.session.get("user")
    if user:
        return templates.TemplateResponse("post_login.html", {"request": request, "user": user["name"]})
    return templates.TemplateResponse("post_login.html", {"request": request, "user": "Guest"})

# Logout route
@app.get("/logout")
async def logout(request: Request):
    request.session.clear()  # Clear the session
    return RedirectResponse(url="/") 