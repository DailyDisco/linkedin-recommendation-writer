#!/usr/bin/env python3
"""
Check users in database
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.dependencies import get_database_session
from app.models.user import User
from sqlalchemy import select


async def main():
    async for session in get_database_session():
        result = await session.execute(select(User))
        users = result.scalars().all()
        print(f"Found {len(users)} users:")
        for user in users:
            print(f"- ID: {user.id}, Username: {user.username}, Email: {user.email}, Has password: {bool(user.hashed_password)}")
        break


if __name__ == "__main__":
    asyncio.run(main())
