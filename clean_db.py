import sqlite3
from config import DB_NAME


def clean_crazy_items():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Deleta itens onde a RAM parece um telefone (número > 1000)
    print("Verificando itens corrompidos...")

    # Verifica visualmente antes
    cursor.execute("SELECT id, title, ram FROM OLX_ITENS_RAW WHERE CAST(ram AS INTEGER) > 200")
    bad_items = cursor.fetchall()

    if bad_items:
        print(f"Encontrados {len(bad_items)} itens alucinados (Telefone no lugar da RAM):")
        for item in bad_items:
            print(f"ID: {item[0]} | RAM Detectada: {item[2]} | Título: {item[1]}")

        # Deleta
        cursor.execute("DELETE FROM OLX_ITENS_RAW WHERE CAST(ram AS INTEGER) > 200")
        conn.commit()
        print("✅ Itens removidos com sucesso.")
    else:
        print("Nenhum item corrompido encontrado via SQL.")

    conn.close()


if __name__ == "__main__":
    clean_crazy_items()