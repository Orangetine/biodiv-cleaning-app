import os
from site import abs_paths
import yaml
import numpy as np

# Defining settings path 

dir_path = os.path.abspath(os.path.dirname(__file__))
root_dir = os.path.abspath(os.path.join(dir_path, "../.."))
settings_dir_path = os.path.join(dir_path,"settings")
eng_fr_colnames_path = os.path.join(settings_dir_path,"eng_fr_colnames.yaml")
mapping_code_atlas_faune_GN_path = os.path.join(settings_dir_path,\
                                    "mapping_codes_atlas_faune_GN.yaml")

code_atlas_faune_GN_path = os.path.join(settings_dir_path,\
                                    "codes_atlas_faune_GN.yaml")
id_espece_cd_nom_dict_path = os.path.join(settings_dir_path,\
                                    "id_espece_cdnom_dict.yaml")

# Getting dictionnaries from yaml settings files 

with open(code_atlas_faune_GN_path, "r", encoding="utf-8") as code_atlas_faune_GN_yaml:
    code_atlas_faune_GN = yaml.safe_load(code_atlas_faune_GN_yaml)

with open(mapping_code_atlas_faune_GN_path, "r", encoding="utf-8") as mapping_atlas_faune_GN_yaml:
    mapping_code_atlas_faune_GN = yaml.safe_load(mapping_atlas_faune_GN_yaml)

# Used for creating column cd_nom, we map id_espece (bd faune) according 
# to their equivalent cd_nom (bd geonat)
with open(id_espece_cd_nom_dict_path, "r", encoding="utf-8") as id_espece_cd_nom_dict_yaml:
    id_espece_cd_nom_dict = yaml.safe_load(id_espece_cd_nom_dict_yaml)


#  Retrieving Atlas Codes Constants

code_atlas = code_atlas_faune_GN["code_atlas"]
code_atlas_faune = code_atlas["code_atlas_faune"]
code_atlas_GN = code_atlas["code_atlas_GN"]
code_atlas_transcription = code_atlas_faune_GN["transcription_code"]

# Useful for mapping integer with its corresponding code atlas transcription

TRANS_FAUNE = code_atlas_transcription["transcription_faune"]
TRANS_GN = code_atlas_transcription["transcription_GN"]

# Mapping localisation

mapping_localisation = {
    "Point" : 10,
    "Jardin" : 100,
    "Transect": 50,
    "Polygone" : 500,
    "Lieu-dit" : 750,
    "Localisation précise" : 10,
    "Localisation imprécise" : 500,
    "Localisation précise (polygone)" : 200
}

# Mapping Full Form

mapping_full_form = {
    0: "Liste complète = Non",
    1: "Liste complète = Oui",
}


# Mapping ESTIMATION_CODE

mapping_estimation_code = {
    "~" : "estimé",
    ">" : "estimé",
    "×" : "Ne sait pas",
    np.nan : "compté" 
}

# Mapping Code Atlas Faune to Geonat
mapping_code_atlas_faune = {
    "2" : 1,
    "3" : 2,
    "4" : 3,
    "5" : 4,
    "6" : 5,
    "7" : 6,
    "8" : 7,
    "9" : 8,
    "10" : 9,
    "11" : 10,
    "12" : 11,
    "13" : 12,
    "14" : 13,
    "15" : 14,
    "16" : 14,
    "17" : 11,
    "18" : 15,
    "19" : 15,
    "30" : 1,
    "40" : 3,
    "50" : 10,
    "99" : np.nan
}

mapping_code_atlas_faune_new = {
    "30" : 1,
    "40" : 3,
    "50" : 10,
    "99" : np.nan
}

used_columns = ['ID_SIGHTING', 'ID_SPECIES', 
                'NAME_SPECIES', 'LATIN_SPECIES',
                'TAXONOMY_NAME', 'FAMILY_NAME', 
                'ID_FORM', 'ESTIMATION_CODE', 
                'TOTAL_COUNT', 'DETAIL', 
                'BEHAVIOUR', 'COMMENT', 
                'PRIVATE_COMMENT','MEDIA_HAS_MEDIA', 
                'HAS_DEATH_INFO', 'ATLAS_CODE', "NATURALITE",
                'NAME', 'SURNAME']






