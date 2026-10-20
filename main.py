from functools import wraps
import sqlite3, os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash



main = Flask(__name__)
leerUsuario = os.getenv("LEER_USUARIO","")

base_name = "datitos.db"

main.config["SECRET_KEY"] = "El-bryan-prefiere-a-las-del-don-bosco-que-a-la-rayzeel"

def conexion_auto():
    conexion = sqlite3.connect(base_name)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON;")
    return conexion
