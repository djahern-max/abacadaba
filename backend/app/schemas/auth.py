from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str

    @field_validator("password")
    @classmethod
    def check_password_length(cls, value: str) -> str:
        if len(value) < 10:
            raise ValueError("password must be at least 10 characters")
        return value

    @field_validator("display_name")
    @classmethod
    def check_display_name_length(cls, value: str) -> str:
        stripped = value.strip()
        if not (2 <= len(stripped) <= 80):
            raise ValueError("display_name must be 2 to 80 characters after stripping whitespace")
        return stripped


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    display_name: str
    is_admin: bool
