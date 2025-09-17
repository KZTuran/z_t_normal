import streamlit as st
import pandas as pd
import numpy as np
import io
import time

st.title("📊 Нормализация результатов теста")
st.write("Загрузи Excel/CSV с сырыми баллами, выбери колонку(и) и укажи с какой строки начинать обработку.")

# Загрузка файла
uploaded_file = st.file_uploader("Загрузи файл", type=["csv", "xlsx"])

if uploaded_file:
    # Определяем формат файла
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    # Переименуем 'Unnamed' колонки для удобства
    df.columns = [
        col if not col.startswith("Unnamed") else f"Column_{i}"
        for i, col in enumerate(df.columns, start=1)
    ]

    st.write("### Исходные данные:")
    st.dataframe(df)

    # С какой строки считать
    start_row = st.number_input(
        "С какой строки начинать обработку? (нумерация с 1)",
        min_value=1,
        max_value=len(df),
        value=1
    )

    # Выбор колонок
    columns = st.multiselect(
        "Выбери колонку(и) с сырыми баллами",
        df.columns
    )

    if st.button("Посчитать Z и T"):
        if not columns:
            st.warning("❗ Пожалуйста, выбери хотя бы одну колонку.")
        else:
            start_time = time.time()

            df_selected = df.iloc[start_row-1:].copy()
            result_df = df.copy()

            z_cols, t_cols = [], []

            for column in columns:
                # Преобразуем в числа
                scores = pd.to_numeric(df_selected[column], errors="coerce")
                scores_clean = scores.dropna()

                mean = scores_clean.mean()
                sd = scores_clean.std(ddof=1)

                z_col = f"{column}_Z"
                t_col = f"{column}_T"
                z_cols.append(z_col)
                t_cols.append(t_col)

                if pd.isna(sd) or sd == 0:
                    # Если разброс нулевой/недостаточно данных — заполняем NaN и предупреждаем
                    result_df.loc[start_row-1:, z_col] = np.nan
                    result_df.loc[start_row-1:, t_col] = np.nan
                    st.warning(f"Колонка «{column}»: стандартное отклонение = 0 или недостаточно данных. Z/T не рассчитаны.")
                    continue

                # 1) Считаем Z из исходных баллов
                z_raw = (scores - mean) / sd

                # 2) Округляем Z до 2 знаков — это будет показываться в таблице
                z_rounded = z_raw.round(2)

                # 3) Считаем T ИЗ УЖЕ ОКРУГЛЁННОГО Z, чтобы проверка сходилась
                t_from_z = (50 + 10 * z_rounded).round(2)

                # Записываем в результат
                result_df.loc[start_row-1:, z_col] = z_rounded
                result_df.loc[start_row-1:, t_col] = t_from_z

            # Порядок колонок: RAW → Z → T
            raw_cols = [c for c in df.columns if c not in z_cols and c not in t_cols]
            ordered_cols = raw_cols + z_cols + t_cols
            result_df = result_df[ordered_cols]

            # Переименуем с разделителями для удобства
            renamed = {}
            for c in raw_cols: renamed[c] = f"RAW | {c}"
            for c in z_cols:  renamed[c] = f"Z | {c[:-2]}"   # обрезаем суффикс '_Z'
            for c in t_cols:  renamed[c] = f"T | {c[:-2]}"   # обрезаем суффикс '_T'
            result_df = result_df.rename(columns=renamed)

            end_time = time.time()  # конец замера времени
            elapsed = end_time - start_time

            st.write("### Результаты:")
            st.dataframe(result_df)
            st.write(f"⏱️ Время обработки: {elapsed:.3f} сек.")

            # Сохранение в Excel (.xlsx)
            output = io.BytesIO()
            result_df.to_excel(output, index=False, engine="openpyxl")
            excel_data = output.getvalue()

            st.download_button(
                label="Скачать результат в Excel (.xlsx)",
                data=excel_data,
                file_name="normalized_scores.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )





# streamlit run C:\Users\Asus\Desktop\Универ\python\app_1\.venv\Test_1.py
