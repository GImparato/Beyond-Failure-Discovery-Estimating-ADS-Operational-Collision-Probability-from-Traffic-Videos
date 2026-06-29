import csv
import os


def append_row(csv_path, row_dict):
    """
    Appende una riga al CSV.
    Se il file non esiste → lo crea.
    Se compaiono nuove colonne → riscrive l’header.
    """
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    file_exists = os.path.exists(csv_path)

    # Se il file non esiste, usa le chiavi della riga come header
    if not file_exists:
        fieldnames = list(row_dict.keys())
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(row_dict)
        return

    # Se il file esiste, leggi l’header corrente
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        existing_header = next(reader)

    # Verifica se ci sono nuove colonne
    new_fields = [k for k in row_dict.keys() if k not in existing_header]

    if new_fields:
        # Aggiorna header
        updated_header = existing_header + new_fields

        # Leggi tutte le righe esistenti
        with open(csv_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Riscrivi tutto con header aggiornato
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=updated_header)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)
            writer.writerow(row_dict)
    else:
        # Nessuna nuova colonna → append normale
        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=existing_header)
            writer.writerow(row_dict)
