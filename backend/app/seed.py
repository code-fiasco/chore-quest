"""Database seed helpers for default household data."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.household import Category, Household

DEFAULT_CATEGORY_NAMES = (
    "Cleaning",
    "Cooking",
    "Laundry",
    "Tidying",
    "Maintenance",
    "Shopping",
    "Admin",
    "Gardening",
    "Pets",
)


def ensure_default_categories(db: Session, household_id: int) -> list[Category]:
    """Create default categories for a household if none exist yet."""
    existing_count = db.scalar(
        select(func.count())
        .select_from(Category)
        .where(Category.household_id == household_id)
    ) or 0

    if existing_count > 0:
        return list(
            db.scalars(
                select(Category)
                .where(Category.household_id == household_id)
                .order_by(Category.name)
            ).all()
        )

    categories = [
        Category(name=name, household_id=household_id)
        for name in DEFAULT_CATEGORY_NAMES
    ]
    db.add_all(categories)
    db.flush()
    return categories


def seed_all_households() -> None:
    """Ensure every household has default categories when empty."""
    db = SessionLocal()
    try:
        households = db.scalars(select(Household)).all()
        for household in households:
            ensure_default_categories(db, household.id)
        db.commit()
        print(f"Seeded categories for {len(households)} household(s).")
    finally:
        db.close()


if __name__ == "__main__":
    seed_all_households()
