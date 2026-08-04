from pydantic_settings import BaseSettings,SettingsConfigDict
from pydantic import Field,field_validator
from typing import List,Union


class Settings(BaseSettings):
    project_name:str="bridgescore"
    version:str="v1.0"
    ai_v1_str:str="/api/v1"
    allowed_origins:List[str]=Field(...,validation_alias="ALLOWED_ORIGINS")
    database_url:str=Field(...,validation_alias="DATABASE_URL")
    anthropic_api_key:str=Field(...,validation_alias="ANTHROPIC_API_KEY")
    secret_key:str=Field(...,validation_alias="SECRET_KEY")
    production:bool=False
    is_dev_mode:bool=True

    @field_validator("allowed_origins",mode="after")
    @classmethod
    def validation_origin(cls,value:Union[str,List[str]])->List[str]:
        if isinstance(value,list):
            return [str(item).rstrip("/") for item in value]
        if isinstance(value,str):
            cleaned=value.strip()
            if cleaned.startswith("[") and cleaned.endswith("]"):
                cleaned=cleaned[1:-1]
            origin=[
                item.strip("'\'").rstrip("/")
                for item in cleaned.strip(",")
                if item.strip()     
            ]    
            for origin in origins:
                if not origin.startswith("http://","https://"):
                    raise ValueError(f"Invalid origin: {origin}. Must start with http:// or https://")
            return origin   
        raise ValueError("Invalid type for allowed_origins. Must be a list or a string.")

        model_config=SettingsConfigDict(
            env_file=".env",
            case_sensitive=True,
            extra="ignore"
        )  
settings=Settings()        


                 


        

    