"""Database constraints and triggers for data validation."""

import logging
from typing import Any, Dict

from sqlalchemy import text

from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class DatabaseConstraints:
    """Manage database-level constraints and validation triggers."""

    @staticmethod
    async def create_validation_constraints() -> Dict[str, Any]:
        """Create essential database constraints and validation triggers."""
        try:
            async with AsyncSessionLocal() as session:
                constraints_created = []

                # Email format validation trigger
                await session.execute(
                    text(
                        """
                    CREATE OR REPLACE FUNCTION validate_email_format()
                    RETURNS TRIGGER AS $$
                    BEGIN
                        -- Check basic email format
                        IF NEW.email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$' THEN
                            RAISE EXCEPTION 'Invalid email format: %', NEW.email;
                        END IF;

                        -- Check length
                        IF length(NEW.email) > 255 THEN
                            RAISE EXCEPTION 'Email too long: maximum 255 characters';
                        END IF;

                        RETURN NEW;
                    END;
                    $$ LANGUAGE plpgsql;
                """
                    )
                )
                constraints_created.append("email_format_function")

                # Username validation trigger
                await session.execute(
                    text(
                        """
                    CREATE OR REPLACE FUNCTION validate_username_format()
                    RETURNS TRIGGER AS $$
                    BEGIN
                        -- Check length constraints
                        IF length(NEW.username) < 3 THEN
                            RAISE EXCEPTION 'Username too short: minimum 3 characters';
                        END IF;

                        IF length(NEW.username) > 50 THEN
                            RAISE EXCEPTION 'Username too long: maximum 50 characters';
                        END IF;

                        -- Check character constraints
                        IF NEW.username !~ '^[a-zA-Z0-9_-]+$' THEN
                            RAISE EXCEPTION 'Invalid username format: only letters, numbers, underscores, and hyphens allowed';
                        END IF;

                        RETURN NEW;
                    END;
                    $$ LANGUAGE plpgsql;
                """
                    )
                )
                constraints_created.append("username_format_function")

                # Recommendation content validation trigger
                await session.execute(
                    text(
                        """
                    CREATE OR REPLACE FUNCTION validate_recommendation_content()
                    RETURNS TRIGGER AS $$
                    BEGIN
                        -- Check content length
                        IF length(NEW.content) < 50 THEN
                            RAISE EXCEPTION 'Recommendation content too short: minimum 50 characters';
                        END IF;

                        IF length(NEW.content) > 5000 THEN
                            RAISE EXCEPTION 'Recommendation content too long: maximum 5000 characters';
                        END IF;

                        -- Check word count (approximate)
                        IF array_length(string_to_array(trim(NEW.content), ' '), 1) < 8 THEN
                            RAISE EXCEPTION 'Recommendation content insufficient: minimum 8 words required';
                        END IF;

                        RETURN NEW;
                    END;
                    $$ LANGUAGE plpgsql;
                """
                    )
                )
                constraints_created.append("recommendation_content_function")

                # Daily recommendation limit trigger
                await session.execute(
                    text(
                        """
                    CREATE OR REPLACE FUNCTION validate_daily_recommendation_limit()
                    RETURNS TRIGGER AS $$
                    DECLARE
                        user_role text;
                        daily_limit int;
                        current_count int;
                        last_date date;
                        needs_reset boolean := false;
                    BEGIN
                        -- Get user information
                        SELECT role, recommendation_count, last_recommendation_date
                        INTO user_role, current_count, last_date
                        FROM users
                        WHERE id = NEW.user_id;

                        -- Set limits based on role
                        CASE user_role
                            WHEN 'premium' THEN daily_limit := 50;
                            WHEN 'admin' THEN daily_limit := 1000;
                            ELSE daily_limit := 5;  -- free users
                        END CASE;

                        -- Check if we need to reset the counter
                        IF last_date IS NULL OR last_date < CURRENT_DATE THEN
                            needs_reset := true;
                            current_count := 0;
                        END IF;

                        -- Check if limit exceeded
                        IF current_count >= daily_limit THEN
                            RAISE EXCEPTION 'Daily recommendation limit exceeded for % users: %/%',
                                user_role, current_count, daily_limit;
                        END IF;

                        RETURN NEW;
                    END;
                    $$ LANGUAGE plpgsql;
                """
                    )
                )
                constraints_created.append("daily_limit_function")

                # GitHub profile validation trigger
                await session.execute(
                    text(
                        """
                    CREATE OR REPLACE FUNCTION validate_github_profile()
                    RETURNS TRIGGER AS $$
                    BEGIN
                        -- Validate GitHub username format
                        IF NEW.username !~ '^[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38}$' THEN
                            RAISE EXCEPTION 'Invalid GitHub username format: %', NEW.username;
                        END IF;

                        -- Validate profile URL if provided
                        IF NEW.profile_url IS NOT NULL AND NEW.profile_url != '' THEN
                            IF NEW.profile_url !~ '^https?://github\\.com/[^/]+/?$' THEN
                                RAISE EXCEPTION 'Invalid GitHub profile URL format: %', NEW.profile_url;
                            END IF;
                        END IF;

                        RETURN NEW;
                    END;
                    $$ LANGUAGE plpgsql;
                """
                    )
                )
                constraints_created.append("github_profile_function")

                await session.commit()

                return {"status": "success", "constraints_created": constraints_created, "message": f"Created {len(constraints_created)} validation functions"}

        except Exception as e:
            logger.error(f"Failed to create validation constraints: {e}")
            return {"status": "error", "error": str(e), "message": "Failed to create validation constraints"}

    @staticmethod
    async def create_triggers() -> Dict[str, Any]:
        """Create database triggers for validation."""
        try:
            async with AsyncSessionLocal() as session:
                triggers_created = []

                # Email validation trigger
                await session.execute(
                    text(
                        """
                    DROP TRIGGER IF EXISTS validate_user_email ON users;
                    CREATE TRIGGER validate_user_email
                        BEFORE INSERT OR UPDATE ON users
                        FOR EACH ROW EXECUTE FUNCTION validate_email_format();
                """
                    )
                )
                triggers_created.append("validate_user_email")

                # Username validation trigger
                await session.execute(
                    text(
                        """
                    DROP TRIGGER IF EXISTS validate_user_username ON users;
                    CREATE TRIGGER validate_user_username
                        BEFORE INSERT OR UPDATE ON users
                        FOR EACH ROW
                        WHEN (NEW.username IS NOT NULL)
                        EXECUTE FUNCTION validate_username_format();
                """
                    )
                )
                triggers_created.append("validate_user_username")

                # Recommendation content validation trigger
                await session.execute(
                    text(
                        """
                    DROP TRIGGER IF EXISTS validate_recommendation_content_trigger ON recommendations;
                    CREATE TRIGGER validate_recommendation_content_trigger
                        BEFORE INSERT OR UPDATE ON recommendations
                        FOR EACH ROW EXECUTE FUNCTION validate_recommendation_content();
                """
                    )
                )
                triggers_created.append("validate_recommendation_content_trigger")

                # Daily limit validation trigger
                await session.execute(
                    text(
                        """
                    DROP TRIGGER IF EXISTS validate_daily_limit ON recommendations;
                    CREATE TRIGGER validate_daily_limit
                        BEFORE INSERT ON recommendations
                        FOR EACH ROW EXECUTE FUNCTION validate_daily_recommendation_limit();
                """
                    )
                )
                triggers_created.append("validate_daily_limit")

                # GitHub profile validation trigger
                await session.execute(
                    text(
                        """
                    DROP TRIGGER IF EXISTS validate_github_profile_trigger ON github_profiles;
                    CREATE TRIGGER validate_github_profile_trigger
                        BEFORE INSERT OR UPDATE ON github_profiles
                        FOR EACH ROW EXECUTE FUNCTION validate_github_profile();
                """
                    )
                )
                triggers_created.append("validate_github_profile_trigger")

                await session.commit()

                return {"status": "success", "triggers_created": triggers_created, "message": f"Created {len(triggers_created)} validation triggers"}

        except Exception as e:
            logger.error(f"Failed to create triggers: {e}")
            return {"status": "error", "error": str(e), "message": "Failed to create validation triggers"}

    @staticmethod
    async def create_audit_triggers() -> Dict[str, Any]:
        """Create audit triggers for tracking changes."""
        try:
            async with AsyncSessionLocal() as session:
                # Create audit log table if it doesn't exist
                await session.execute(
                    text(
                        """
                    CREATE TABLE IF NOT EXISTS audit_log (
                        id SERIAL PRIMARY KEY,
                        table_name VARCHAR(50) NOT NULL,
                        operation VARCHAR(10) NOT NULL,
                        record_id INTEGER,
                        old_values JSONB,
                        new_values JSONB,
                        user_id INTEGER,
                        changed_by INTEGER,
                        changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    CREATE INDEX IF NOT EXISTS idx_audit_log_table_operation
                    ON audit_log(table_name, operation);

                    CREATE INDEX IF NOT EXISTS idx_audit_log_changed_at
                    ON audit_log(changed_at);
                """
                    )
                )

                # Generic audit trigger function
                await session.execute(
                    text(
                        """
                    CREATE OR REPLACE FUNCTION audit_trigger_function()
                    RETURNS TRIGGER AS $$
                    DECLARE
                        user_id_val INTEGER;
                        operation_type TEXT;
                        record_id_val INTEGER;
                    BEGIN
                        -- Determine operation type
                        IF TG_OP = 'INSERT' THEN
                            operation_type := 'INSERT';
                            record_id_val := NEW.id;
                            user_id_val := NEW.user_id;
                        ELSIF TG_OP = 'UPDATE' THEN
                            operation_type := 'UPDATE';
                            record_id_val := NEW.id;
                            user_id_val := NEW.user_id;
                        ELSIF TG_OP = 'DELETE' THEN
                            operation_type := 'DELETE';
                            record_id_val := OLD.id;
                            user_id_val := OLD.user_id;
                        END IF;

                        -- Insert audit record
                        INSERT INTO audit_log (
                            table_name,
                            operation,
                            record_id,
                            old_values,
                            new_values,
                            user_id,
                            changed_at
                        ) VALUES (
                            TG_TABLE_NAME,
                            operation_type,
                            record_id_val,
                            CASE WHEN TG_OP != 'INSERT' THEN row_to_json(OLD)::jsonb ELSE NULL END,
                            CASE WHEN TG_OP != 'DELETE' THEN row_to_json(NEW)::jsonb ELSE NULL END,
                            user_id_val,
                            CURRENT_TIMESTAMP
                        );

                        RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
                    END;
                    $$ LANGUAGE plpgsql;
                """
                    )
                )

                # Create audit triggers for key tables
                audit_triggers = [("users", "audit_users_trigger"), ("recommendations", "audit_recommendations_trigger"), ("github_profiles", "audit_github_profiles_trigger")]

                for table_name, trigger_name in audit_triggers:
                    await session.execute(
                        text(
                            f"""
                        DROP TRIGGER IF EXISTS {trigger_name} ON {table_name};
                        CREATE TRIGGER {trigger_name}
                            AFTER INSERT OR UPDATE OR DELETE ON {table_name}
                            FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
                    """
                        )
                    )

                await session.commit()

                return {"status": "success", "message": "Audit system created successfully", "audit_triggers": [trigger for _, trigger in audit_triggers]}

        except Exception as e:
            logger.error(f"Failed to create audit triggers: {e}")
            return {"status": "error", "error": str(e), "message": "Failed to create audit triggers"}

    @staticmethod
    async def add_table_constraints() -> Dict[str, Any]:
        """Add table-level constraints for data integrity."""
        try:
            async with AsyncSessionLocal() as session:
                constraints_added = []

                # Add check constraints to existing tables
                try:
                    await session.execute(
                        text(
                            """
                        ALTER TABLE users
                        ADD CONSTRAINT IF NOT EXISTS check_user_role
                        CHECK (role IN ('free', 'premium', 'admin'));

                        ALTER TABLE users
                        ADD CONSTRAINT IF NOT EXISTS check_username_length
                        CHECK (length(username) >= 3 AND length(username) <= 50);

                        ALTER TABLE users
                        ADD CONSTRAINT IF NOT EXISTS check_daily_limit_range
                        CHECK (daily_limit >= 1 AND daily_limit <= 1000);
                    """
                        )
                    )
                    constraints_added.extend(["check_user_role", "check_username_length", "check_daily_limit_range"])
                except Exception as e:
                    logger.warning(f"Failed to add user constraints: {e}")

                try:
                    await session.execute(
                        text(
                            """
                        ALTER TABLE recommendations
                        ADD CONSTRAINT IF NOT EXISTS check_recommendation_content_length
                        CHECK (length(content) >= 50 AND length(content) <= 5000);

                        ALTER TABLE recommendations
                        ADD CONSTRAINT IF NOT EXISTS check_recommendation_title_length
                        CHECK (length(title) >= 5 AND length(title) <= 200);
                    """
                        )
                    )
                    constraints_added.extend(["check_recommendation_content_length", "check_recommendation_title_length"])
                except Exception as e:
                    logger.warning(f"Failed to add recommendation constraints: {e}")

                try:
                    await session.execute(
                        text(
                            """
                        ALTER TABLE github_profiles
                        ADD CONSTRAINT IF NOT EXISTS check_github_username_format
                        CHECK (username ~ '^[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38}$');

                        ALTER TABLE github_profiles
                        ADD CONSTRAINT IF NOT EXISTS check_github_profile_url
                        CHECK (profile_url IS NULL OR profile_url ~ '^https?://github\\.com/[^/]+/?$');
                    """
                        )
                    )
                    constraints_added.extend(["check_github_username_format", "check_github_profile_url"])
                except Exception as e:
                    logger.warning(f"Failed to add GitHub profile constraints: {e}")

                await session.commit()

                return {"status": "success", "constraints_added": constraints_added, "message": f"Added {len(constraints_added)} table constraints"}

        except Exception as e:
            logger.error(f"Failed to add table constraints: {e}")
            return {"status": "error", "error": str(e), "message": "Failed to add table constraints"}

    @staticmethod
    async def setup_all_constraints() -> Dict[str, Any]:
        """Set up all database constraints, triggers, and validation."""
        results = []

        # Create validation functions
        result = await DatabaseConstraints.create_validation_constraints()
        results.append({"step": "validation_constraints", **result})

        # Create triggers
        result = await DatabaseConstraints.create_triggers()
        results.append({"step": "triggers", **result})

        # Add table constraints
        result = await DatabaseConstraints.add_table_constraints()
        results.append({"step": "table_constraints", **result})

        # Create audit system
        result = await DatabaseConstraints.create_audit_triggers()
        results.append({"step": "audit_system", **result})

        # Summarize results
        successful_steps = [r for r in results if r.get("status") == "success"]
        failed_steps = [r for r in results if r.get("status") != "success"]

        return {
            "status": "completed" if len(failed_steps) == 0 else "partial",
            "successful_steps": len(successful_steps),
            "failed_steps": len(failed_steps),
            "details": results,
            "message": f"Database constraints setup completed: {len(successful_steps)}/{len(results)} steps successful",
        }
