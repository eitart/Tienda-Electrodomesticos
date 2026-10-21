from functools import wraps
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash



main = Flask(__name__)
base_name = "datitos.db"

main.config["SECRET_KEY"] = "El-bryan-prefiere-a-las-del-don-bosco-que-a-la-rayzeel"

def conexion_auto():
    conexion = sqlite3.connect(base_name)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON;")
    return conexion


def tabla_proveedor():
    conexion = conexion_auto()
    conexion.execute("""
        CREATE TABLE IF NOT EXISTS proveedor(
            idProveedor    INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre         TEXT NOT NULL,
            apellido       TEXT NOT NULL,
            direc          TEXT NOT NULL,
            telef          TEXT NOT NULL
        )
    """)
    conexion.commit()
    conexion.close()

def tabla_Suministra():
    conexion = conexion_auto()
    conexion.execute("""
        CREATE TABLE IF NOT EXISTS Suministra(
            idSuministra    INTEGER PRIMARY KEY AUTOINCREMENT,
            idProveedor     TEXT NOT NULL,
            codProducto     INTEGER NOT NULL,
            FOREIGN KEY (idProveedor) REFERENCES proveedor(idProveedor),
            FOREIGN KEY (codProducto) REFERENCES Electrodomestico(codProducto)
        )
    """)
    conexion.commit()
    conexion.close()
    
def tabla_electrodomestico():
    conexion = conexion_auto()
    conexion.execute("""
        CREATE TABLE IF NOT EXISTS Electrodomestico(
            codProducto    TEXT PRIMARY KEY AUTOINCREMENT,
            nombre     TEXT NOT NULL,
            marca    TEXT NOT NULL,
            categoria     TEXT ,
            modelo TEXT NOT NULL,
            precio DOUBLE NOT NULL,
            stock INTEGER,
            foto TEXT NOT NULL
        )
    """)
    conexion.commit()
    conexion.close()


def tabla_detalleVenta():
    conexion = conexion_auto()
    conexion.execute("""
        CREATE TABLE IF NOT EXISTS detalleVenta(
            idVenta    INTEGER NOT NULL,
            codProducto  INTEGER NOT NULL,
            cantidad INTEGER NOT NULL,
            precioSubtotal INTEGER NOT NULL,
            precioUnitario INTEGER NOT NULL,
            FOREIGN KEY (codProducto) REFERENCES Electrodomestico(codProducto),
            FOREIGN KEY (idVenta) REFERENCES Venta(idVenta)
        )
    """)
    conexion.commit()
    conexion.close()

def tabla_Venta():
    conexion = conexion_auto()
    conexion.execute("""
        CREATE TABLE IF NOT EXISTS Venta(
            idVenta    INTEGER PRIMARY KEY AUTOINCREMENT,
            CI  TEXT NOT NULL ,
            idEmpleado TEXT NOT NULL,
            total DOUBLE,
            MetodoPago TEXT NOT NULL,
            fecha datetime('now'),
            FOREIGN KEY (CI) REFERENCES Cliente(CI),
            FOREIGN KEY (idEmpleado) REFERENCES Empleado(idEmpleado)
        )
    """)
    conexion.commit()
    conexion.close()


def tabla_Cliente():
    conexion = conexion_auto()
    conexion.execute("""
        CREATE TABLE IF NOT EXISTS Cliente(
            CI   TEXT PRIMARY KEY,
            nombres TEXT NOT NULL,
            apellidos TEXT NOT NULL,
            telefono TEXT NOT NULL,
            direccion TEXT,
            email TEXT NOT NULL
        )
    """)
    conexion.commit()
    conexion.close()


def tabla_Empleado():
    conexion = conexion_auto()
    conexion.execute("""
        CREATE TABLE IF NOT EXISTS Cliente(
            idEmpleado   TEXT PRIMARY KEY,
            CI TEXT NOT NULL,
            password TEXT NOT NULL,
            nombre TEXT NOT NULL,
            apellidoP TEXT NOT NULL,
            apellidoM TEXT,
            direcciones TEXT,
            salario DOUBLE NOT NULL
        )
    """)
    conexion.commit()
    conexion.close()


@main.route("/")
def menu():
    return render_template("menu.html")
    