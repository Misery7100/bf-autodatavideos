def build_connection_url(
        user: str, 
        db: str, 
        password: str, 
        host: str, 
        port: int = 5432, 
        protocol: str = 'postgresql'
    ) -> str:

    return f"{protocol}://{user}:{password}@{host}:{port}/{db}"