import pandas as pd
import re
import os
from flask import Flask, render_template, request

# --- Carga y preparación de los datos ---
def cargar_datos(file_path):
    """
    Procesa el archivo de Excel para extraer, limpiar y combinar los datos de Pokémon.
    """
    try:
        xl_file = pd.ExcelFile(file_path)
        sheet_names = xl_file.sheet_names
        trainer_sheet = 'Lista entrenador'
        if trainer_sheet not in sheet_names:
            raise ValueError(f"No se encontró la hoja '{trainer_sheet}' en el archivo.")
        
        df_trainers = pd.read_excel(xl_file, sheet_name=trainer_sheet, header=0)
        df_trainers.columns = df_trainers.columns.str.strip()
        df_trainers = df_trainers[['Tipo Entrenador', 'Nombre', 'Modo']].copy()
        
        all_pokemon_data = []
        pokemon_sheets = [s for s in sheet_names if s != trainer_sheet]
        
        for pokemon_sheet in pokemon_sheets:
            try:
                df = pd.read_excel(xl_file, sheet_name=pokemon_sheet, header=None)
                # Encuentra todas las filas donde la primera columna es '#'
                table_starts = df.index[df.iloc[:, 0].astype(str).str.strip() == '#'].tolist()
                
                for i in range(len(table_starts)):
                    header_row_index = table_starts[i]
                    
                    # --- ¡ESTA ERA LA LÍNEA DEL ERROR! ---
                    # Se cambió de 'header_row_index - 2' a 'header_row_index - 1'
                    trainer_info_row = df.iloc[header_row_index - 1, 0] 
                    
                    match = re.search(r'(.+)\s+\((Lv\.\d+)\s+Mode\)', str(trainer_info_row))
                    if not match:
                        continue
                    
                    trainer_name = match.group(1).strip()
                    mode = match.group(2).strip()

                    # Determina el final de la tabla actual
                    end_row_table = table_starts[i + 1] - 2 if i + 1 < len(table_starts) else len(df)
                    
                    df_pokemon = df.iloc[header_row_index + 1:end_row_table].copy()
                    
                    # Asigna los nombres de columna basados en tu imagen
                    df_pokemon.columns = ['#', 'Pokémon', 'Item', 'Moves 1', 'Moves 2', 'Moves 3', 'Moves 4',
                                          'Nature', 'EVs_HP', 'EVs_Attack', 'EVs_Defense', 'EVs_Sp_Atk', 'EVs_Sp_Def', 'EVs_Speed']

                    df_pokemon.drop(columns=['#'], inplace=True)
                    
                    df_pokemon['Nombre'] = trainer_name
                    df_pokemon['Modalidad'] = mode
                    df_pokemon['Tipo Entrenador'] = pokemon_sheet
                    
                    all_pokemon_data.append(df_pokemon)

            except Exception as e:
                print(f"Error procesando la hoja '{pokemon_sheet}': {e}")
                continue
        
        if not all_pokemon_data:
            return pd.DataFrame()

        df_pokemon_combined = pd.concat(all_pokemon_data, ignore_index=True)
        
        df_merged = pd.merge(df_trainers, df_pokemon_combined, on=['Nombre'], how='inner')
        
        if df_merged.empty:
            return pd.DataFrame()
        
        df_merged['Modalidad'] = df_merged['Modalidad'].str.strip()
        df_merged['Modo'] = df_merged['Modo'].astype(str).str.strip().str.replace(' ', '', regex=False)
        df_merged = df_merged[df_merged.apply(lambda row: row['Modalidad'].replace('.', '') in row['Modo'].replace('.', ''), axis=1)]

        if 'Tipo Entrenador_x' in df_merged.columns:
            df_final = df_merged.drop(columns=['Modo']).copy()
            df_final.rename(columns={'Tipo Entrenador_x': 'Tipo Entrenador'}, inplace=True)
            # Renombrar 'Pokémon' a 'Nombre Pokémon' para consistencia con el HTML
            if 'Pokémon' in df_final.columns:
                df_final.rename(columns={'Pokémon': 'Nombre Pokémon'}, inplace=True)
            return df_final
        else:
            return pd.DataFrame()

    except Exception as e:
        print(f"Error fatal en cargar_datos: {e}")
        return pd.DataFrame()

# --- Inicialización de la Aplicación Flask ---
app = Flask(__name__)

# --- Carga de datos al iniciar la aplicación ---
file_path = 'Battle_Tower_RS_gen3.xlsx'
df_final = cargar_datos(file_path)

if not df_final.empty:
    print("¡Éxito! Los datos se cargaron correctamente.")
else:
    print("ADVERTENCIA: La aplicación se inicia con un DataFrame vacío.")

# --- Definición de la Ruta Principal ---
# Reemplaza tu función index con esta
@app.route('/', methods=['GET', 'POST'])
def index():
    resultados = pd.DataFrame()
    
    if request.method == 'POST' and not df_final.empty:
        nombre_entrenador = request.form.get('nombre_entrenador')
        tipo_entrenador = request.form.get('tipo_entrenador')
        modalidad = request.form.get('modalidad')
        nombre_pokemon = request.form.get('nombre_pokemon')

        df_filtrado = df_final.copy()

        if tipo_entrenador and 'Tipo Entrenador' in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado['Tipo Entrenador'].str.contains(tipo_entrenador, case=False, na=False)]
        
        if nombre_entrenador and 'Nombre' in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado['Nombre'].str.contains(nombre_entrenador, case=False, na=False)]
        
        if modalidad and 'Modalidad' in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado['Modalidad'].str.contains(modalidad, case=False, na=False)]
        
        if nombre_pokemon and 'Nombre Pokémon' in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado['Nombre Pokémon'].str.contains(nombre_pokemon, case=False, na=False)]
            
        resultados = df_filtrado
        
        # --- LÍNEA DE DEPURACIÓN ---
        # Esto nos dirá cuántos resultados encontró el filtro.
        print(f"Resultados encontrados después de filtrar: {len(resultados)}")
        
    return render_template('index.html', resultados=resultados)

# --- Bloque para ejecución local ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)