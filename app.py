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
                
                table_starts = df.index[df.iloc[:, 0].astype(str).str.strip() == '#'].tolist()
                
                for i in range(len(table_starts)):
                    header_row_index = table_starts[i]
                    
                    trainer_info_row = df.iloc[header_row_index - 2, 0]
                    match = re.search(r'(.+)\s+\((Lv\.\d+)\s+Mode\)', str(trainer_info_row))
                    if not match:
                        continue
                    
                    trainer_name = match.group(1).strip()
                    mode = match.group(2).strip()

                    end_row_table = table_starts[i + 1] - 3 if i + 1 < len(table_starts) else len(df)
                    
                    df_pokemon = df.iloc[header_row_index + 2:end_row_table].copy()
                    
                    df_pokemon.columns = ['#', 'Nombre Pokémon', 'empty', 'Item', 'Moves 1', 'Moves 2', 'Moves 3', 'Moves 4',
                                          'Nature', 'EVs_HP', 'EVs_Attack', 'EVs_Defense', 'EVs_Sp_Atk', 'EVs_Sp_Def', 'EVs_Speed']

                    df_pokemon['Nombre Pokémon'] = df_pokemon['Nombre Pokémon'].astype(str).str.replace(' (Pokémon)', '', regex=False).str.strip()
                    df_pokemon['Item'] = df_pokemon['Item'].astype(str).str.split(pat='[ \xa0]', n=1, expand=True)[0].str.strip()
                    
                    df_pokemon.drop(columns=['#', 'empty'], inplace=True)
                    
                    df_pokemon['Nombre'] = trainer_name
                    df_pokemon['Modalidad'] = mode
                    df_pokemon['Tipo Entrenador'] = pokemon_sheet
                    
                    all_pokemon_data.append(df_pokemon)

            except Exception as e:
                print(f"Error al procesar la hoja '{pokemon_sheet}': {e}")
                continue
        
        if all_pokemon_data:
            df_pokemon_combined = pd.concat(all_pokemon_data, ignore_index=True)
            df_pokemon_combined.drop_duplicates(subset=['Nombre', 'Modalidad', 'Nombre Pokémon'], keep='first', inplace=True)
            
            df_merged = pd.merge(df_trainers, df_pokemon_combined, on=['Nombre'], how='inner')
            
            # Limpieza y filtrado final
            df_merged['Modalidad'] = df_merged['Modalidad'].str.strip()
            df_merged['Modo'] = df_merged['Modo'].astype(str).str.strip().str.replace(' ', '', regex=False)
            df_merged = df_merged[df_merged.apply(lambda row: row['Modalidad'].replace('.', '') in row['Modo'].replace('.', ''), axis=1)]

            df_final = df_merged.drop(columns=['Modo']).copy()
            df_final.rename(columns={'Tipo Entrenador_x': 'Tipo Entrenador'}, inplace=True)
            
            return df_final
        return pd.DataFrame()
    except FileNotFoundError:
        print(f"Error: El archivo '{file_path}' no se encontró.")
        return pd.DataFrame()
    except ValueError as e:
        print(f"Error en el archivo de Excel: {e}")
        return pd.DataFrame()

app = Flask(__name__)
file_path = 'Battle_Tower_RS_gen3.xlsx'
df_final = cargar_datos(file_path)

@app.route('/', methods=['GET', 'POST'])
def index():
    resultados = pd.DataFrame()
    
    if request.method == 'POST':
        nombre_entrenador = request.form.get('nombre_entrenador')
        tipo_entrenador = request.form.get('tipo_entrenador')
        modalidad = request.form.get('modalidad')
        nombre_pokemon = request.form.get('nombre_pokemon')

        df_filtrado = df_final.copy()
        if tipo_entrenador:
            df_filtrado = df_filtrado[df_filtrado['Tipo Entrenador'].str.contains(tipo_entrenador, case=False, na=False)]
        if nombre_entrenador:
            df_filtrado = df_filtrado[df_filtrado['Nombre'].str.contains(nombre_entrenador, case=False, na=False)]
        if modalidad:
            df_filtrado = df_filtrado[df_filtrado['Modalidad'].str.contains(modalidad, case=False, na=False)]
        if nombre_pokemon:
            df_filtrado = df_filtrado[df_filtrado['Nombre Pokémon'].str.contains(nombre_pokemon, case=False, na=False)]
            
        resultados = df_filtrado
        
    return render_template('index.html', resultados=resultados)

if __name__ == '__main__':
      port = int(os.environ.get("PORT", 5000))  # usa el puerto de Render o 5000 local
    app.run(host="0.0.0.0", port=port)