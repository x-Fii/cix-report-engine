from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Date, Enum, TIMESTAMP, func, Boolean
from sqlalchemy.orm import relationship
from config.database import Base

class Region(Base):
    __tablename__ = "regions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)

    outlets = relationship("Outlet", back_populates="region_rel")

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    billing_address = Column(Text, nullable=True)
    shipping_address = Column(Text, nullable=True)
    license_number = Column(String(100), nullable=True)
    license_expiry = Column(Date, nullable=True)
    
    outlets = relationship("Outlet", back_populates="customer_rel")
    delivery_orders = relationship("DeliveryOrder", back_populates="customer_rel")

class Outlet(Base):
    __tablename__ = "outlets"
    
    maxis_centre_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False)
    region_id = Column(Integer, ForeignKey("regions.id", ondelete="RESTRICT"), nullable=False)
    maxis_centre_name = Column(String(255), nullable=False)
    type = Column(Enum('MC+', 'MC', 'MEP', 'MEP Lite', 'Kiosk', 'Flagship'), nullable=False)
    state = Column(Enum('Johor', 'Kedah', 'Kelantan', 'Melaka', 'Negeri Sembilan', 'Pahang', 'Penang', 'Perak', 'Perlis', 'Sabah', 'Sarawak', 'Selangor', 'Terengganu', 'Kuala Lumpur', 'Labuan', 'Putrajaya'), nullable=False)
    locality = Column(String(255), nullable=True)
    address = Column(Text, nullable=False)
    store_pic = Column(String(255), nullable=True)
    contact_no = Column(String(50), nullable=True)
    project_ref = Column(String(50), nullable=False)
    
    customer_rel = relationship("Customer", back_populates="outlets")
    region_rel = relationship("Region", back_populates="outlets")
    delivery_orders = relationship("DeliveryOrder", back_populates="outlet_rel")

class DeliveryOrder(Base):
    __tablename__ = "delivery_orders"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    do_no = Column(String(50), unique=True, nullable=False)
    so_id = Column(Integer, nullable=True) # Adding so_id as placeholder for now since sales_orders might not be fully mapped
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False)
    maxis_centre_id = Column(Integer, ForeignKey("outlets.maxis_centre_id", ondelete="RESTRICT"), nullable=False)
    salesperson = Column(String(100), nullable=False)
    bill_to = Column(Text, nullable=False)
    ship_to = Column(Text, nullable=False)
    affected_screen = Column(String(255), nullable=True)
    status = Column(Enum('draft', 'assigned', 'in_transit', 'delivered', 'split'), default="draft")
    parent_do_id = Column(Integer, ForeignKey("delivery_orders.id", ondelete="SET NULL"), nullable=True)
    signed_by = Column(String(255), nullable=True)
    signature_upload_id = Column(Integer, nullable=True)
    signed_at = Column(DateTime, nullable=True)
    
    customer_rel = relationship("Customer", back_populates="delivery_orders")
    outlet_rel = relationship("Outlet", back_populates="delivery_orders")
    service_reports = relationship("ServiceReport", back_populates="do_rel")

class Upload(Base):
    __tablename__ = "uploads"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    path = Column(String(500), nullable=False)
    mime = Column(String(100), nullable=False)
    size = Column(Integer, nullable=False)
    sha256 = Column(String(64), nullable=False)
    uploaded_by = Column(Integer, nullable=True)
    uploaded_at = Column(TIMESTAMP, server_default=func.now())
    
    service_reports = relationship("ServiceReport", back_populates="signature_rel")

class ServiceReport(Base):
    __tablename__ = "service_reports"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sr_no = Column(String(50), unique=True, nullable=False)
    do_id = Column(Integer, ForeignKey("delivery_orders.id", ondelete="RESTRICT"), nullable=False)
    wo_number = Column(String(50), nullable=True)
    remedy_number = Column(String(50), nullable=True)
    client_company = Column(String(255), nullable=False)
    client_addr_json = Column(Text, nullable=False) # JSON in schema, but Text works in sqlalchemy if JSON is not imported
    store_type = Column(String(50), nullable=True)
    store_name = Column(String(255), nullable=True)
    pic_name = Column(String(255), nullable=True)
    pic_tel = Column(String(50), nullable=True)
    diagnostic = Column(Text, nullable=True)
    action_taken = Column(Text, nullable=True)
    before_photos_json = Column(Text, nullable=False)
    after_photos_json = Column(Text, nullable=False)
    ack_signed_by = Column(String(255), nullable=False)
    ack_signature_upload_id = Column(Integer, ForeignKey("uploads.id", ondelete="RESTRICT"), nullable=False)
    ack_signed_at = Column(DateTime, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    do_rel = relationship("DeliveryOrder", back_populates="service_reports")
    signature_rel = relationship("Upload", back_populates="service_reports")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    display_name = Column(String(255), nullable=False)
    initials = Column(String(10), nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    roles = relationship("Role", secondary="user_roles", back_populates="users")

class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False)
    
    users = relationship("User", secondary="user_roles", back_populates="roles")

class UserRole(Base):
    __tablename__ = "user_roles"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
