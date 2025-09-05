# COPIA Y REEMPLAZA TU FUNCIÓN ENTERA CON ESTA
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

        # --- DEBUG PRINT 1 ---
        print("--- Nombres de entrenadores cargados de 'Lista entrenador':")
        print(df_trainers['Nombre'].unique())
        print("-" * 20)

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

            # --- DEBUG PRINT 2 ---
            print("--- Nombres de entrenadores extraídos de las hojas de Pokémon:")
            print(df_pokemon_combined['Nombre'].unique())
            print("-" * 20)

            df_merged = pd.merge(df_trainers, df_pokemon_combined, on=['Nombre'], how='inner')

            # --- DEBUG PRINT 3: EL MÁS IMPORTANTE ---
            print(f"--- ¡IMPORTANTE! Tamaño de df_merged después de la unión: {df_merged.shape}")
            if df_merged.shape[0] == 0:
                print(">>> ALERTA: El DataFrame está VACÍO. No se encontraron nombres en común. Revisa los prints anteriores.")
            print("-" * 20)

            df_merged['Modalidad'] = df_merged['Modalidad'].str.strip()
            df_merged['Modo'] = df_merged['Modo'].astype(str).str.strip().str.replace(' ', '', regex=False)
            df_merged = df_merged[df_merged.apply(lambda row: row['Modalidad'].replace('.', '') in row['Modo'].replace('.', ''), axis=1)]

            df_final = df_merged.drop(columns=['Modo']).copy()
            df_final.rename(columns={'Tipo Entrenador_x': 'Tipo Entrenador'}, inplace=True)

            # --- DEBUG PRINT 4 ---
            print("--- Columnas finales del DataFrame que se va a usar:")
            print(df_final.columns.tolist())
            print("-" * 20)

            return df_final

        print(">>> ALERTA: No se procesaron datos de Pokémon. Retornando DataFrame vacío.")
        return pd.DataFrame()

    except Exception as e:
        print(f"Error fatal en cargar_datos: {e}")
        return pd.DataFrame()