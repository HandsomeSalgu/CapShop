from sqlalchemy import text
from sqlalchemy.orm import Session
import pandas as pd

def get_user_events_with_products(db: Session, user_id: int) -> pd.DataFrame:
    """
    Fetch user events joined with products to get textual metadata for the given user.
    """
    query = text("""
        SELECT 
            ue.event_type,
            p.title,
            p.brand,
            p.category_name
        FROM user_events ue
        JOIN products p ON ue.product_id = p.product_id
        WHERE ue.user_id = :user_id
        ORDER BY ue.created_at DESC
        LIMIT 100
    """)
    
    result = db.execute(query, {"user_id": user_id})
    rows = result.fetchall()
    
    # Convert to DataFrame
    df = pd.DataFrame(rows, columns=["event_type", "title", "brand", "category_name"])
    return df
