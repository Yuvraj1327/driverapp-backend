"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-08-04

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- roles ---
    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(50), nullable=False, unique=True, index=True),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("full_name", sa.String(150), nullable=False),
        sa.Column("email", sa.String(150), nullable=False, unique=True, index=True),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- drivers ---
    op.create_table(
        "drivers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("license_number", sa.String(100), nullable=False, unique=True),
        sa.Column("license_expiry", sa.Date, nullable=True),
        sa.Column("address", sa.String(255), nullable=True),
        sa.Column("emergency_contact", sa.String(30), nullable=True),
        sa.Column("is_available", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- vehicles ---
    vehicle_status_enum = postgresql.ENUM("active", "in_service", "inactive", "retired", name="vehicle_status")
    vehicle_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "vehicles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("registration_number", sa.String(50), nullable=False, unique=True, index=True),
        sa.Column("make", sa.String(100), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("color", sa.String(50), nullable=True),
        sa.Column("vin", sa.String(100), nullable=True, unique=True),
        sa.Column("current_odometer", sa.Float, nullable=False, server_default="0"),
        sa.Column("mulkiya_number", sa.String(100), nullable=True),
        sa.Column("mulkiya_expiry", sa.Date, nullable=True),
        sa.Column("insurance_provider", sa.String(150), nullable=True),
        sa.Column("insurance_policy_number", sa.String(100), nullable=True),
        sa.Column("insurance_expiry", sa.Date, nullable=True),
        sa.Column("status", vehicle_status_enum, nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- vehicle_assignments ---
    assignment_status_enum = postgresql.ENUM("active", "unassigned", name="assignment_status")
    assignment_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "vehicle_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("driver_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assigned_date", sa.Date, nullable=False),
        sa.Column("unassigned_date", sa.Date, nullable=True),
        sa.Column("status", assignment_status_enum, nullable=False, server_default="active"),
        sa.Column("notes", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- km_logs ---
    op.create_table(
        "km_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("driver_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("log_date", sa.Date, nullable=False),
        sa.Column("start_odometer", sa.Float, nullable=False),
        sa.Column("end_odometer", sa.Float, nullable=False),
        sa.Column("distance_covered", sa.Float, nullable=False),
        sa.Column("trip_purpose", sa.String(255), nullable=True),
        sa.Column("notes", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- expense_categories ---
    op.create_table(
        "expense_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- expenses ---
    expense_status_enum = postgresql.ENUM("pending", "approved", "rejected", name="expense_status")
    expense_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "expenses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("driver_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("expense_categories.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("amount", sa.Float, nullable=False),
        sa.Column("expense_date", sa.Date, nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("receipt_url", sa.String(500), nullable=True),
        sa.Column("status", expense_status_enum, nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- expense_approvals ---
    approval_decision_enum = postgresql.ENUM("pending", "approved", "rejected", name="approval_decision")
    approval_decision_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "expense_approvals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("expense_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("expenses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("decision", approval_decision_enum, nullable=False),
        sa.Column("remarks", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- tyres ---
    op.create_table(
        "tyres",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("brand", sa.String(100), nullable=False),
        sa.Column("position", sa.String(50), nullable=False),
        sa.Column("serial_number", sa.String(100), nullable=True),
        sa.Column("installed_date", sa.Date, nullable=False),
        sa.Column("installed_odometer", sa.Float, nullable=False),
        sa.Column("expected_life_km", sa.Float, nullable=False, server_default="50000"),
        sa.Column("removed_date", sa.Date, nullable=True),
        sa.Column("cost", sa.Float, nullable=True),
        sa.Column("condition", sa.String(50), nullable=True),
        sa.Column("notes", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- services ---
    op.create_table(
        "services",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("service_type", sa.String(150), nullable=False),
        sa.Column("service_date", sa.Date, nullable=False),
        sa.Column("odometer_reading", sa.Float, nullable=False),
        sa.Column("cost", sa.Float, nullable=False),
        sa.Column("workshop_name", sa.String(150), nullable=True),
        sa.Column("next_service_due_km", sa.Float, nullable=True),
        sa.Column("next_service_due_date", sa.Date, nullable=True),
        sa.Column("notes", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- reminders ---
    reminder_type_enum = postgresql.ENUM(
        "insurance_expiry", "mulkiya_expiry", "service_due", "tyre_change", "custom", name="reminder_type"
    )
    reminder_type_enum.create(op.get_bind(), checkfirst=True)
    reminder_status_enum = postgresql.ENUM("pending", "sent", "read", "dismissed", name="reminder_status")
    reminder_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "reminders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=True),
        sa.Column("driver_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("drivers.id", ondelete="CASCADE"), nullable=True),
        sa.Column("reminder_type", reminder_type_enum, nullable=False),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("due_date", sa.Date, nullable=False),
        sa.Column("status", reminder_status_enum, nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- notifications ---
    notification_type_enum = postgresql.ENUM("info", "warning", "alert", "approval", name="notification_type")
    notification_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("message", sa.String(500), nullable=False),
        sa.Column("notification_type", notification_type_enum, nullable=False, server_default="info"),
        sa.Column("is_read", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("link", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- reports ---
    report_type_enum = postgresql.ENUM(
        "daily", "weekly", "monthly", "vehicle_wise", "driver_wise", "expense_wise", name="report_type"
    )
    report_type_enum.create(op.get_bind(), checkfirst=True)
    export_format_enum = postgresql.ENUM("pdf", "excel", name="export_format")
    export_format_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("generated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("report_type", report_type_enum, nullable=False),
        sa.Column("export_format", export_format_enum, nullable=False),
        sa.Column("period_start", sa.Date, nullable=True),
        sa.Column("period_end", sa.Date, nullable=True),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("reports")
    op.drop_table("notifications")
    op.drop_table("reminders")
    op.drop_table("services")
    op.drop_table("tyres")
    op.drop_table("expense_approvals")
    op.drop_table("expenses")
    op.drop_table("expense_categories")
    op.drop_table("km_logs")
    op.drop_table("vehicle_assignments")
    op.drop_table("vehicles")
    op.drop_table("drivers")
    op.drop_table("users")
    op.drop_table("roles")

    bind = op.get_bind()
    for enum_name in [
        "export_format",
        "report_type",
        "notification_type",
        "reminder_status",
        "reminder_type",
        "approval_decision",
        "expense_status",
        "assignment_status",
        "vehicle_status",
    ]:
        postgresql.ENUM(name=enum_name).drop(bind, checkfirst=True)
