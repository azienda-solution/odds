
from function import Client, analys_per_link, append_new_line, callAi, clean_text, click_consent, convert_sheet_csv_read_excel, extract_list_from_google, forebet, get_domain, initGoogle, load_file, save_to_excel, scrap_selenium_v1, to_percentage
from upload_drive import upload_text_file_to_drive


from pydub import AudioSegment
import os
from pathlib import Path

def merge_audio_files(input_folder, output_file="merged_audio.mp3"):
    """
    Fusionne tous les fichiers audio d'un dossier en un seul fichier.
    
    Args:
        input_folder (str): Chemin du dossier contenant les fichiers audio
        output_file (str): Nom du fichier de sortie (par défaut: merged_audio.mp3)
    """
    
    # Extensions audio supportées
    audio_extensions = {'.mp3', '.wav', '.ogg', '.flac', '.m4a', '.wma', '.aac'}
    
    # Récupérer tous les fichiers audio du dossier
    audio_files = []
    for file in sorted(os.listdir(input_folder)):
        file_path = os.path.join(input_folder, file)
        if Path(file).suffix.lower() in audio_extensions and os.path.isfile(file_path):
            audio_files.append(file_path)
    
    if not audio_files:
        print("Aucun fichier audio trouvé dans le dossier.")
        return
    
    print(f"Fichiers audio trouvés: {len(audio_files)}")
    for i, file in enumerate(audio_files, 1):
        print(f"  {i}. {os.path.basename(file)}")
    
    # Charger et fusionner les fichiers audio
    print("\nFusion en cours...")
    combined = AudioSegment.empty()
    
    for i, file_path in enumerate(audio_files, 1):
        try:
            print(f"Traitement de {os.path.basename(file_path)}... ({i}/{len(audio_files)})")
            audio = AudioSegment.from_file(file_path)
            combined += audio
        except Exception as e:
            print(f"Erreur lors du traitement de {file_path}: {e}")
            continue
    
    # Exporter le fichier fusionné
    output_path = os.path.join(input_folder, output_file)
    print(f"\nExportation vers {output_path}...")
    combined.export(output_path, format=Path(output_file).suffix[1:])
    
    print(f"✓ Fusion terminée! Fichier créé: {output_path}")
    print(f"Durée totale: {len(combined) / 1000:.2f} secondes")

if __name__ == "__main__":
    # Exemple d'utilisation
    folder_path = input("Entrez le chemin du dossier contenant les fichiers audio: ").strip()
    
    if not os.path.exists(folder_path):
        print("Erreur: Le dossier n'existe pas.")
    else:
        output_name = input("Nom du fichier de sortie (par défaut: merged_audio.mp3): ").strip()
        if not output_name:
            output_name = "merged_audio.mp3"
        
        merge_audio_files(folder_path, output_name)