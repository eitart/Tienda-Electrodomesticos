import sqlite3

from datetime import datetime, timezone, timedelta

from flask import Flask, render_template, request, redirect, url_for, session, flash


from werkzeug.security import generate_password_hash,check_password_hash



main = Flask(__name__)

base_name = "datitos.db"

main.config["SECRET_KEY"] = "3l-8R1N-S3-1a C0m3"


def conexion_auto():
    conexion = sqlite3.connect(base_name)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def fecha_actual():
    bolivia = timezone(timedelta(hours=-4))
    return datetime.now(bolivia).strftime("%Y-%m-%d %H:%M:%S")


def tabla_proveedor():
    conexion = conexion_auto()

    conexion.execute("""
        CREATE TABLE IF NOT EXISTS proveedor (
            idProveedor INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            apellido TEXT NOT NULL,
            direc TEXT NOT NULL,
            telef TEXT NOT NULL
        )
    """)

    conexion.commit()
    conexion.close()


def tabla_producto():
    conexion = conexion_auto()

    conexion.execute("""
        CREATE TABLE IF NOT EXISTS Electrodomestico (
            codProducto INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            marca TEXT NOT NULL,
            categoria TEXT,
            modelo TEXT NOT NULL,
            precio REAL NOT NULL CHECK (precio > 0),
            stock INTEGER NOT NULL CHECK (stock >= 0),
            foto TEXT NOT NULL DEFAULT ''
        )
    """)

    conexion.commit()
    conexion.close()


def tabla_cliente():
    conexion = conexion_auto()

    conexion.execute("""
        CREATE TABLE IF NOT EXISTS Cliente (
            CI TEXT PRIMARY KEY,
            nombres TEXT NOT NULL,
            apellidos TEXT NOT NULL,
            telefono TEXT NOT NULL,
            direccion TEXT,
            email TEXT NOT NULL
        )
    """)

    conexion.commit()
    conexion.close()


def tabla_empleado():
    conexion = conexion_auto()

    conexion.execute("""
        CREATE TABLE IF NOT EXISTS Empleado (
            idEmpleado INTEGER PRIMARY KEY AUTOINCREMENT,
            CI TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            nombre TEXT NOT NULL,
            apellidoP TEXT NOT NULL,
            apellidoM TEXT,
            direcciones TEXT,
            salario REAL NOT NULL DEFAULT 0,
            idPermiso INTEGER NOT NULL DEFAULT 1
        )
    """)

    conexion.commit()
    conexion.close()


def tabla_venta():
    conexion = conexion_auto()

    conexion.execute("""
        CREATE TABLE IF NOT EXISTS Venta (
            idVenta INTEGER PRIMARY KEY AUTOINCREMENT,
            CI TEXT NOT NULL,
            idEmpleado INTEGER NOT NULL,
            total REAL NOT NULL CHECK (total >= 0),
            MetodoPago TEXT NOT NULL,
            fecha TEXT NOT NULL,
            FOREIGN KEY (CI) REFERENCES Cliente(CI),
            FOREIGN KEY (idEmpleado) REFERENCES Empleado(idEmpleado)
        )
    """)

    conexion.commit()
    conexion.close()


def tabla_detalle():
    conexion = conexion_auto()

    conexion.execute("""
        CREATE TABLE IF NOT EXISTS detalleVenta (
            idVenta INTEGER NOT NULL,
            codProducto INTEGER NOT NULL,
            cantidad INTEGER NOT NULL CHECK (cantidad > 0),
            precioSubtotal REAL NOT NULL,
            precioUnitario REAL NOT NULL,
            PRIMARY KEY (idVenta, codProducto),
            FOREIGN KEY (idVenta) REFERENCES Venta(idVenta),
            FOREIGN KEY (codProducto) REFERENCES Electrodomestico(codProducto)
        )
    """)

    conexion.commit()
    conexion.close()


def tabla_suministra():
    conexion = conexion_auto()

    conexion.execute("""
        CREATE TABLE IF NOT EXISTS Suministra (
            idSuministra INTEGER PRIMARY KEY AUTOINCREMENT,
            idProveedor INTEGER NOT NULL,
            codProducto INTEGER NOT NULL,
            estadoPedido TEXT NOT NULL DEFAULT 'espera'
                CHECK (
                    estadoPedido IN ('hecho', 'espera', 'cancelado')
                ),
            FOREIGN KEY (idProveedor)
                REFERENCES proveedor(idProveedor),
            FOREIGN KEY (codProducto)
                REFERENCES Electrodomestico(codProducto)
        )
    """)

    conexion.commit()
    conexion.close()


def crear_admin():
    conexion = conexion_auto()

    empleado = conexion.execute("""
        SELECT idEmpleado
        FROM Empleado
        LIMIT 1
    """).fetchone()

    if empleado is None:
        conexion.execute("""
            INSERT INTO Empleado (
                CI, password, nombre, apellidoP,
                apellidoM, direcciones, salario, idPermiso
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "eitan07",
            generate_password_hash("ElBryanSeLaCome"),
            "Eitan Arturo",
            "Vargas",
            "Gironda",
            "por ahisito",
            4000000,
            1
        ))

        conexion.commit()

    conexion.close()


tabla_proveedor()
tabla_producto()
tabla_cliente()
tabla_empleado()
tabla_venta()
tabla_detalle()
tabla_suministra()
crear_admin()



@main.context_processor
def datos_layout():
    return {
        "nombre_usuario": session.get("nombre", "Usuario")
    }



@main.route("/", methods=["GET", "POST"])
@main.route("/login", methods=["GET", "POST"])
def login():
    if "idEmpleado" in session:
        return redirect(url_for("perfil"))

    if request.method == "POST":
        ci = request.form["ci"].strip()
        password = request.form["password"]

        conexion = conexion_auto()

        empleado = conexion.execute("""
            SELECT *
            FROM Empleado
            WHERE CI = ?
        """, (ci,)).fetchone()

        conexion.close()

        if empleado and check_password_hash(
            empleado["password"], password
        ):
            session.clear()
            session["idEmpleado"] = empleado["idEmpleado"]
            session["nombre"] = empleado["nombre"]

            return redirect(url_for("perfil"))

        flash("Usuario o contraseña incorrectos.", "error")

    return render_template("login.html")


@main.route("/salir", methods=["POST"])
def salir():
    session.clear()
    return redirect(url_for("login"))



@main.route("/perfil")
def perfil():
    if "idEmpleado" not in session:
        return redirect(url_for("login"))

    conexion = conexion_auto()

    empleado = conexion.execute("""
        SELECT *
        FROM Empleado
        WHERE idEmpleado = ?
    """, (session["idEmpleado"],)).fetchone()

    resumen = conexion.execute("""
        SELECT
            COUNT(*) AS cantidad,
            COALESCE(SUM(total), 0) AS total
        FROM Venta
        WHERE idEmpleado = ?
    """, (session["idEmpleado"],)).fetchone()

    conexion.close()

    return render_template("perfil.html",empleado=empleado,resumen=resumen)



@main.route("/productos", methods=["GET", "POST"])
def productos():
    if "idEmpleado" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        nuevoProducto = {
            "nombre": request.form["nombre"].strip(),
            "marca": request.form["marca"].strip(),
            "categoria": request.form["categoria"].strip(),
            "modelo": request.form["modelo"].strip(),
            "precio": request.form.get("precio", type=float),
            "stock": request.form.get("stock", type=int),
            "foto": request.form.get("foto", "").strip()
        }

        if (nuevoProducto["nombre"] == "" or nuevoProducto["marca"] == ""or nuevoProducto["modelo"] == ""):
            flash("Completa nombre, marca y modelo.", "error")
            return redirect(url_for("productos"))

        if nuevoProducto["precio"] is None:
            flash("Escribe un precio válido.", "error")
            return redirect(url_for("productos"))

        if not 0.01 <= nuevoProducto["precio"] <= 1000000000:
            flash("El precio debe estar entre 0.01 y 1000000000.", "error")
            return redirect(url_for("productos"))

        if nuevoProducto["stock"] is None:
            flash("Escribe un stock entero.", "error")
            return redirect(url_for("productos"))

        if not 0 <= nuevoProducto["stock"] <= 1000000000:
            flash("El stock debe estar entre 0 y 1000000000.", "error")
            return redirect(url_for("productos"))

        conexion = conexion_auto()

        conexion.execute("""
            INSERT INTO Electrodomestico (
                nombre, marca, categoria,
                modelo, precio, stock, foto
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            nuevoProducto["nombre"],
            nuevoProducto["marca"],
            nuevoProducto["categoria"],
            nuevoProducto["modelo"],
            round(nuevoProducto["precio"], 2),
            nuevoProducto["stock"],
            nuevoProducto["foto"]
        ))

        conexion.commit()
        conexion.close()

        flash("Producto registrado.", "exito")
        return redirect(url_for("productos"))

    conexion = conexion_auto()

    lista = conexion.execute("""
        SELECT *
        FROM Electrodomestico
        ORDER BY nombre COLLATE NOCASE ASC
    """).fetchall()

    conexion.close()

    return render_template("productos.html",productos=lista)



@main.route("/registro")
def registro():
    return redirect(url_for("ventas"))


@main.route("/ventas")
def ventas():
    if "idEmpleado" not in session:
        return redirect(url_for("login"))

    buscar = request.args.get("buscar", "").strip()
    orden = request.args.get("orden", "fecha")

    if orden == "cliente":
        ordenar = "c.nombres COLLATE NOCASE, c.apellidos COLLATE NOCASE"
    elif orden == "vendedor":
        ordenar = "e.nombre COLLATE NOCASE, e.apellidoP COLLATE NOCASE"
    else:
        orden = "fecha"
        ordenar = "v.fecha DESC"

    conexion = conexion_auto()

    lista = conexion.execute("""
        SELECT
            v.idVenta,
            v.fecha,
            v.total,
            v.MetodoPago,
            c.nombres || ' ' || c.apellidos AS cliente,
            e.nombre || ' ' || e.apellidoP AS vendedor,
            p.codProducto,
            p.nombre AS producto,
            d.cantidad,
            d.precioUnitario
        FROM Venta v
        JOIN Cliente c ON c.CI = v.CI
        JOIN Empleado e ON e.idEmpleado = v.idEmpleado
        JOIN detalleVenta d ON d.idVenta = v.idVenta
        JOIN Electrodomestico p ON p.codProducto = d.codProducto
        WHERE (
            ? = ''
            OR CAST(v.idVenta AS TEXT) = ?
            OR CAST(p.codProducto AS TEXT) = ?
            OR p.nombre LIKE ?
        )
        ORDER BY """ + ordenar + ", v.idVenta DESC", (
            buscar,
            buscar,
            buscar,
            "%" + buscar + "%"
        )
    ).fetchall()

    conexion.close()

    return render_template("registroventas.html",ventas=lista,buscar=buscar,orden=orden,hoy=fecha_actual()[:10])



@main.route("/ventas/nueva", methods=["GET", "POST"])
@main.route("/ventas/editar/<int:idVenta>", methods=["GET", "POST"])
def formulario_venta(idVenta=None):
    if "idEmpleado" not in session:
        return redirect(url_for("login"))

    conexion = conexion_auto()
    venta = None

    if request.method == "POST":
        conexion.execute("BEGIN IMMEDIATE")

    if idVenta is not None:
        venta = conexion.execute("""
            SELECT
                v.*,
                d.codProducto,
                d.cantidad,
                d.precioUnitario
            FROM Venta v
            JOIN detalleVenta d ON d.idVenta = v.idVenta
            WHERE v.idVenta = ?
        """, (idVenta,)).fetchone()

        if venta is None:
            conexion.close()
            flash("La venta no existe.", "error")
            return redirect(url_for("ventas"))

        if venta["fecha"][:10] != fecha_actual()[:10]:
            conexion.close()
            flash("Solo puedes editar ventas realizadas hoy.", "error")
            return redirect(url_for("ventas"))

    if request.method == "POST":
        datos = {
            "CI": request.form["CI"].strip(),
            "codProducto": request.form.get("codProducto", type=int),
            "cantidad": request.form.get("cantidad", type=int),
            "MetodoPago": request.form["MetodoPago"]
        }

        mensaje = ""

        cliente = conexion.execute("""
            SELECT CI
            FROM Cliente
            WHERE CI = ?
        """, (datos["CI"],)).fetchone()

        producto = conexion.execute("""
            SELECT *
            FROM Electrodomestico
            WHERE codProducto = ?
        """, (datos["codProducto"],)).fetchone()

        if cliente is None:
            mensaje = "Selecciona un cliente válido."

        elif producto is None:
            mensaje = "Selecciona un producto válido."

        elif datos["cantidad"] is None:
            mensaje = "Escribe una cantidad entera."

        elif datos["cantidad"] <= 0:
            mensaje = "La cantidad debe ser mayor que cero."

        elif datos["MetodoPago"] not in [
            "Efectivo", "QR", "Tarjeta", "Transferencia"
        ]:
            mensaje = "Selecciona un método de pago válido."

        else:
            disponible = producto["stock"]
            if venta is not None:
                if venta["codProducto"] == datos["codProducto"]:
                    disponible = disponible + venta["cantidad"]

            if datos["cantidad"] > disponible:
                mensaje = "Stock insuficiente. Disponible: " + str(disponible)

        if mensaje != "":
            conexion.close()
            flash(mensaje, "error")

            if idVenta is not None:
                return redirect(url_for(
                    "formulario_venta",
                    idVenta=idVenta
                ))

            return redirect(url_for("formulario_venta"))

        precio = producto["precio"]

        if venta is not None:
            if venta["codProducto"] == datos["codProducto"]:
                precio = venta["precioUnitario"]

        total = round(precio * datos["cantidad"], 2)

        if venta is None:
            cursor = conexion.execute("""
                INSERT INTO Venta (
                    CI, idEmpleado, total, MetodoPago, fecha
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                datos["CI"],
                session["idEmpleado"],
                total,
                datos["MetodoPago"],
                fecha_actual()
            ))

            idVenta = cursor.lastrowid

        else:
            conexion.execute("""
                UPDATE Electrodomestico
                SET stock = stock + ?
                WHERE codProducto = ?
            """, (
                venta["cantidad"],
                venta["codProducto"]
            ))

            conexion.execute("""
                UPDATE Venta
                SET CI = ?, total = ?, MetodoPago = ?
                WHERE idVenta = ?
            """, (
                datos["CI"],
                total,
                datos["MetodoPago"],
                idVenta
            ))

            conexion.execute("""
                DELETE FROM detalleVenta
                WHERE idVenta = ?
            """, (idVenta,))

        conexion.execute("""
            INSERT INTO detalleVenta (
                idVenta, codProducto, cantidad,
                precioSubtotal, precioUnitario
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            idVenta,
            datos["codProducto"],
            datos["cantidad"],
            total,
            precio
        ))

        conexion.execute("""
            UPDATE Electrodomestico
            SET stock = stock - ?
            WHERE codProducto = ?
        """, (
            datos["cantidad"],
            datos["codProducto"]
        ))

        conexion.commit()
        conexion.close()

        flash("Venta guardada y stock actualizado.", "exito")
        return redirect(url_for("ventas"))

    clientes = conexion.execute("""
        SELECT *
        FROM Cliente
        ORDER BY nombres COLLATE NOCASE
    """).fetchall()

    productos = conexion.execute("""
        SELECT *
        FROM Electrodomestico
        ORDER BY nombre COLLATE NOCASE
    """).fetchall()

    conexion.close()

    return render_template("formulario_venta.html",venta=venta,clientes=clientes,productos=productos)



@main.route("/proveedores", methods=["GET", "POST"])
def proveedores():
    if "idEmpleado" not in session:
        return redirect(url_for("login"))

    conexion = conexion_auto()

    if request.method == "POST":
        accion = request.form["accion"]

        if accion == "proveedor":
            nuevoProveedor = {
                "nombre": request.form["nombre"].strip(),
                "apellido": request.form["apellido"].strip(),
                "direc": request.form["direc"].strip(),
                "telef": request.form["telef"].strip()
            }

            if (nuevoProveedor["nombre"] == "" or nuevoProveedor["apellido"] == ""or nuevoProveedor["direc"] == ""or nuevoProveedor["telef"] == ""):
                conexion.close()
                flash("Completa los datos del proveedor.", "error")
                return redirect(url_for("proveedores"))

            conexion.execute("""
                INSERT INTO proveedor (
                    nombre, apellido, direc, telef
                )
                VALUES (?, ?, ?, ?)
            """, (
                nuevoProveedor["nombre"],
                nuevoProveedor["apellido"],
                nuevoProveedor["direc"],
                nuevoProveedor["telef"]
            ))

            flash("Proveedor registrado.", "exito")

        elif accion == "pedido" or accion == "estado":
            estado = request.form["estadoPedido"]

            if estado not in ["hecho", "espera", "cancelado"]:
                conexion.close()
                flash("Estado inválido.", "error")
                return redirect(url_for("proveedores"))

            if accion == "pedido":
                idProveedor = request.form.get("idProveedor", type=int)
                codProducto = request.form.get("codProducto", type=int)

                proveedor = conexion.execute("""
                    SELECT idProveedor
                    FROM proveedor
                    WHERE idProveedor = ?
                """, (idProveedor,)).fetchone()

                producto = conexion.execute("""
                    SELECT codProducto
                    FROM Electrodomestico
                    WHERE codProducto = ?
                """, (codProducto,)).fetchone()

                if proveedor is None or producto is None:
                    conexion.close()
                    flash("Selecciona proveedor y producto válidos.", "error")
                    return redirect(url_for("proveedores"))

                conexion.execute("""
                    INSERT INTO Suministra (
                        idProveedor, codProducto, estadoPedido
                    )
                    VALUES (?, ?, ?)
                """, (
                    idProveedor,
                    codProducto,
                    estado
                ))

                flash("Pedido registrado.", "exito")

            else:
                idPedido = request.form.get("idSuministra", type=int)

                pedido = conexion.execute("""
                    SELECT idSuministra
                    FROM Suministra
                    WHERE idSuministra = ?
                """, (idPedido,)).fetchone()

                if pedido is None:
                    conexion.close()
                    flash("El pedido no existe.", "error")
                    return redirect(url_for("proveedores"))

                conexion.execute("""
                    UPDATE Suministra
                    SET estadoPedido = ?
                    WHERE idSuministra = ?
                """, (
                    estado,
                    idPedido
                ))

                flash("Estado actualizado.", "exito")

        else:
            conexion.close()
            flash("Acción inválida.", "error")
            return redirect(url_for("proveedores"))

        conexion.commit()
        conexion.close()

        return redirect(url_for("proveedores"))

    buscar = request.args.get("buscar", "").strip()

    pedidos = conexion.execute("""
        SELECT
            s.idSuministra,
            s.estadoPedido,
            pr.idProveedor,
            pr.nombre || ' ' || pr.apellido AS proveedor,
            p.codProducto,
            p.nombre AS producto,
            p.marca
        FROM Suministra s
        JOIN proveedor pr ON pr.idProveedor = s.idProveedor
        JOIN Electrodomestico p ON p.codProducto = s.codProducto
        WHERE (
            ? = ''
            OR CAST(pr.idProveedor AS TEXT) = ?
            OR CAST(p.codProducto AS TEXT) = ?
            OR (pr.nombre || ' ' || pr.apellido) LIKE ?
            OR p.nombre LIKE ?
        )
        ORDER BY s.idSuministra DESC
    """, (
        buscar,
        buscar,
        buscar,
        "%" + buscar + "%",
        "%" + buscar + "%"
    )).fetchall()

    listaProveedores = conexion.execute("""
        SELECT *
        FROM proveedor
        ORDER BY nombre COLLATE NOCASE
    """).fetchall()

    listaProductos = conexion.execute("""
        SELECT *
        FROM Electrodomestico
        ORDER BY nombre COLLATE NOCASE
    """).fetchall()

    conexion.close()

    return render_template("proveedores.html",pedidos=pedidos,proveedores=listaProveedores,productos=listaProductos,buscar=buscar)



@main.route("/usuarios", methods=["GET", "POST"])
def usuarios():
    if "idEmpleado" not in session:
        return redirect(url_for("login"))

    conexion = conexion_auto()

    if request.method == "POST":
        nuevoCliente = {
            "CI": request.form["CI"].strip(),
            "nombres": request.form["nombres"].strip(),
            "apellidos": request.form["apellidos"].strip(),
            "telefono": request.form["telefono"].strip(),
            "direccion": request.form["direccion"].strip(),
            "email": request.form["email"].strip()
        }

        if (
            nuevoCliente["CI"] == ""
            or nuevoCliente["nombres"] == ""
            or nuevoCliente["apellidos"] == ""
            or nuevoCliente["telefono"] == ""
            or nuevoCliente["email"] == ""
        ):
            conexion.close()
            flash("Completa los campos obligatorios.", "error")
            return redirect(url_for("usuarios"))

        # Comprueba el CI antes de insertar.
        conexion.execute("BEGIN IMMEDIATE")

        existe = conexion.execute("""
            SELECT CI
            FROM Cliente
            WHERE CI = ?
        """, (nuevoCliente["CI"],)).fetchone()

        if existe is not None:
            conexion.close()
            flash("Ya existe un cliente con ese CI.", "error")
            return redirect(url_for("usuarios"))

        conexion.execute("""
            INSERT INTO Cliente (
                CI, nombres, apellidos,
                telefono, direccion, email
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            nuevoCliente["CI"],
            nuevoCliente["nombres"],
            nuevoCliente["apellidos"],
            nuevoCliente["telefono"],
            nuevoCliente["direccion"],
            nuevoCliente["email"]
        ))

        conexion.commit()
        conexion.close()

        flash("Cliente registrado.", "exito")
        return redirect(url_for("usuarios"))

    buscar = request.args.get("buscar", "").strip()

    clientes = conexion.execute("""
        SELECT *
        FROM Cliente
        WHERE (
            ? = ''
            OR CI = ?
            OR (nombres || ' ' || apellidos) LIKE ?
        )
        ORDER BY nombres COLLATE NOCASE
    """, (
        buscar,
        buscar,
        "%" + buscar + "%"
    )).fetchall()

    historial = conexion.execute("""
        SELECT
            v.CI,
            v.idVenta,
            v.fecha,
            v.total,
            v.MetodoPago,
            p.nombre AS producto,
            d.cantidad
        FROM Venta v
        JOIN Cliente c ON c.CI = v.CI
        JOIN detalleVenta d ON d.idVenta = v.idVenta
        JOIN Electrodomestico p ON p.codProducto = d.codProducto
        WHERE (
            ? = ''
            OR c.CI = ?
            OR (c.nombres || ' ' || c.apellidos) LIKE ?
        )
        ORDER BY v.fecha DESC, v.idVenta DESC
    """, (
        buscar,
        buscar,
        "%" + buscar + "%"
    )).fetchall()

    conexion.close()

    return render_template("clientes.html",clientes=clientes,historial=historial,buscar=buscar)



@main.route("/admin")
def admin():
    return redirect(url_for("perfil"))
