from flask import Flask, request, jsonify, render_template
import pandas as pd
import re

app = Flask(__name__)

# === (aquí va todo el código de carga de df_final que ya te pasé) ===

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/buscar", methods=["GET"])
def buscar():
    filtros = {
        "nombre_entrenador": request.args.get("nombre_entrenador"),
        "tipo_entrenador": request.args.get("tipo_entrenador"),
        "modalidad": request.args.get("modalidad"),
        "nombre_pokemon": request.args.get("nombre_pokemon")
    }
    resultados = buscar_pokemon(df_final, **filtros)

    if resultados.empty:
        return jsonify([])
    return resultados.to_dict(orient="records")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
