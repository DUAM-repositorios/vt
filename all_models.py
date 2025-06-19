from datetime import datetime
from typing import Any, List, Optional
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Text,
    func,
    event
)
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator

# Importar Base de database.py
from database import Base

# --- Tipo PostgreSQL vector (pgvector) -------------------------------------- #
class Vector(TypeDecorator):
    """Soporte para el tipo vector de pgvector"""
    impl = Text
    cache_ok = True

    def __init__(self, dim: int = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dim = dim

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return str(value)

    
    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value


# =========================  TABLAS DEL SISTEMA  ============================ #
class Embedding(Base):
    """Tabla para almacenar embeddings de búsqueda"""
    __tablename__ = "embeddings"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    content = Column(Text, nullable=False)
    embedding = Column(Vector(384), nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Embedding {self.id}>"


class Migration(Base):
    """Tabla para control de migraciones"""
    __tablename__ = "migrations"

    version = Column(Text, primary_key=True)
    name = Column(Text)
    applied_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Migration {self.version}>"


# =========================  ESQUEMA public  ================================= #
class Proveedor(Base):
    __tablename__ = "proveedores"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    nombre = Column(Text, nullable=False, unique=True)
    web = Column(Text)
    pais_casa_matriz = Column(Text)
    industria = Column(Text)
    resumen = Column(Text)
    logo_link = Column(Text)

    # --- relaciones ---
    contactos = relationship(
        "Contacto",
        back_populates="proveedor",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    rfis = relationship(
        "RFI",
        back_populates="proveedor",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    resultados = relationship(
        "ResultadoBusqueda",
        back_populates="proveedor",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Proveedor {self.nombre}>"


class VT(Base):
    __tablename__ = "vt"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    nombre = Column(Text, nullable=False)
    fecha_solicitud = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    tecnologia = Column(Text, nullable=False)
    cliente = Column(Text, nullable=False)
    fecha_entrada = Column(DateTime(timezone=True), nullable=False)

    # --- relaciones ---
    rfis = relationship(
        "RFI", back_populates="vt", cascade="all, delete-orphan", passive_deletes=True
    )
    techs_asociadas = relationship(
        "TechVT",
        back_populates="vt",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    resultados = relationship(
        "ResultadoBusqueda",
        back_populates="vt",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    contactos_rel = relationship(
        "ContactoVT",
        back_populates="vt",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<VT {self.nombre}>"


class TechServicio(Base):
    __tablename__ = "tech_servicios"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    caracteristicas = Column(Text, nullable=False)
    detalles = Column(Text)
    imagen = Column(Text)
    web_link = Column(Text)
    nombre = Column(Text, nullable=False)
    categoria = Column(Text)
    descripcion = Column(Text)

    # --- relaciones ---
    vts_asociadas = relationship(
        "TechVT",
        back_populates="tech",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    resultados = relationship(
        "ResultadoBusqueda",
        back_populates="tech",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<TechServicio {self.nombre}>"


# ---------- tablas de “vínculo” N:M ---------------------------------------- #
class TechVT(Base):
    __tablename__ = "tech_vt"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tech_id = Column(
        BigInteger,
        ForeignKey("tech_servicios.id", ondelete="CASCADE"),
        nullable=False,
    )
    vt_id = Column(
        BigInteger,
        ForeignKey("vt.id", ondelete="CASCADE"),
        nullable=False,
    )

    # -- relaciones bidireccionales
    tech = relationship("TechServicio", back_populates="vts_asociadas")
    vt = relationship("VT", back_populates="techs_asociadas")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<TechVT tech={self.tech_id} vt={self.vt_id}>"


class ContactoVT(Base):
    __tablename__ = "contactos_vt"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    contacto_id = Column(
        BigInteger,
        ForeignKey("contactos.id", ondelete="CASCADE"),
        nullable=False,
    )
    vt_id = Column(
        BigInteger,
        ForeignKey("vt.id", ondelete="CASCADE"),
        nullable=False,
    )

    contacto = relationship("Contacto", back_populates="vts_rel")
    vt = relationship("VT", back_populates="contactos_rel")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ContactoVT contacto={self.contacto_id} vt={self.vt_id}>"


# ---------- tablas “hijas” -------------------------------------------------- #
class Contacto(Base):
    __tablename__ = "contactos"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    proveedor_id = Column(
        BigInteger,
        ForeignKey("proveedores.id", ondelete="CASCADE"),
        nullable=False,
    )
    nombre = Column(Text, nullable=False)
    cargo = Column(Text)
    fecha_corroboracion = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    telefono = Column(Text)
    pais = Column(Text)
    idioma = Column(Text)

    proveedor = relationship("Proveedor", back_populates="contactos")
    vts_rel = relationship(
        "ContactoVT",
        back_populates="contacto",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Contacto {self.nombre}>"


class RFI(Base):
    __tablename__ = "rfi"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    nombre = Column(Text, nullable=False)
    proveedor_id = Column(
        BigInteger,
        ForeignKey("proveedores.id", ondelete="CASCADE"),
        nullable=False,
    )
    vt_id = Column(
        BigInteger,
        ForeignKey("vt.id", ondelete="CASCADE"),
        nullable=False,
    )

    proveedor = relationship("Proveedor", back_populates="rfis")
    vt = relationship("VT", back_populates="rfis")
    estados = relationship(
        "EstadoRFI",
        back_populates="rfi",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<RFI {self.nombre}>"


class EstadoRFI(Base):
    __tablename__ = "estados_rfi"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    rfi_id = Column(
        BigInteger,
        ForeignKey("rfi.id", ondelete="CASCADE"),
        nullable=False,
    )
    estado = Column(Text, nullable=False)
    fecha = Column(DateTime(timezone=True), nullable=False)

    rfi = relationship("RFI", back_populates="estados")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<EstadoRFI {self.estado} #{self.rfi_id}>"


class ResultadoBusqueda(Base):
    __tablename__ = "resultados_busquedas"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    proveedor_id = Column(
        BigInteger,
        ForeignKey("proveedores.id", ondelete="CASCADE"),
        nullable=False,
    )
    tech_id = Column(
        BigInteger,
        ForeignKey("tech_servicios.id", ondelete="CASCADE"),
        nullable=False,
    )
    vt_id = Column(
        BigInteger,
        ForeignKey("vt.id", ondelete="CASCADE"),
        nullable=False,
    )
    fecha = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    proveedor = relationship("Proveedor", back_populates="resultados")
    tech = relationship("TechServicio", back_populates="resultados")
    vt = relationship("VT", back_populates="resultados")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ResultadoBusqueda vt={self.vt_id} proveedor={self.proveedor_id}>"


