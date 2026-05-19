from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum, TIMESTAMP, func
from sqlalchemy.orm import relationship
from database import Base

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    billing_address = Column(Text, nullable=True)
    shipping_address = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    outlets = relationship("Outlet", back_populates="customer_rel")
    delivery_orders = relationship("DeliveryOrder", back_populates="customer_rel")

class Outlet(Base):
    __tablename__ = "outlets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    address = Column(Text, nullable=True)
    region = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    type = Column(String(50), nullable=True)
    status = Column(Enum("Active", "Inactive"), default="Active")
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    customer_rel = relationship("Customer", back_populates="outlets")
    delivery_orders = relationship("DeliveryOrder", back_populates="outlet_rel")

class DeliveryOrder(Base):
    __tablename__ = "delivery_orders"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    do_no = Column(String(50), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False)
    outlet_id = Column(Integer, ForeignKey("outlets.id", ondelete="RESTRICT"), nullable=False)
    salesperson = Column(String(100), nullable=True)
    bill_to = Column(Text, nullable=True)
    ship_to = Column(Text, nullable=True)
    affected_screen = Column(String(255), nullable=True)
    status = Column(Enum("pending", "in_progress", "completed", "cancelled"), default="pending")
    created_at = Column(TIMESTAMP, server_default=func.now())
    
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
    client_addr_json = Column(Text, nullable=False)
    store_type = Column(String(100), nullable=True)
    store_name = Column(String(255), nullable=True)
    pic_name = Column(String(100), nullable=False)
    pic_tel = Column(String(50), nullable=True)
    diagnostic = Column(Text, nullable=True)
    action_taken = Column(Text, nullable=True)
    ack_signed_by = Column(String(100), nullable=False)
    ack_signature_upload_id = Column(Integer, ForeignKey("uploads.id", ondelete="RESTRICT"), nullable=False)
    ack_signed_at = Column(TIMESTAMP, nullable=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    do_rel = relationship("DeliveryOrder", back_populates="service_reports")
    signature_rel = relationship("Upload", back_populates="service_reports")
